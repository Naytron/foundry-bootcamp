"""Application service that coordinates sessions and a chat provider."""

import asyncio
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from uuid import UUID

from support_assistant.agent.models import ConversationTurn
from support_assistant.agent.provider import ChatProvider
from support_assistant.agent.sessions import SessionStore
from support_assistant.retrieval.models import KnowledgeDocument
from support_assistant.retrieval.provider import KnowledgeRetriever


@dataclass(slots=True)
class ChatResponse:
    """Own the stream and release its lease only after nested cleanup."""

    session_id: UUID
    sources: list[KnowledgeDocument]
    stream: AsyncGenerator[str]
    _sessions: SessionStore
    _lease_id: UUID
    _close_lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)
    _closed: bool = field(default=False, init=False)

    async def close(self) -> None:
        """Close nested streams and release this response's lease exactly once."""
        async with self._close_lock:
            if self._closed:
                return
            self._closed = True
            try:
                await self.stream.aclose()
            finally:
                await self._sessions.release(self.session_id, self._lease_id)


class ChatService:
    """Coordinate a provider response with bounded session history."""

    def __init__(
        self,
        provider: ChatProvider,
        sessions: SessionStore,
        retriever: KnowledgeRetriever,
    ) -> None:
        self._provider = provider
        self._sessions = sessions
        self._retriever = retriever

    async def stream(self, *, message: str, session_id: UUID | None) -> ChatResponse:
        """Create the response stream and return its effective session identifier."""
        conversation, lease_id = await self._sessions.get_or_create(session_id)
        setup_complete = False
        try:
            history = tuple(conversation.turns)
            context = await self._retriever.search(message)
            setup_complete = True
        finally:
            if not setup_complete:
                await self._sessions.release(conversation.id, lease_id)

        async def generate() -> AsyncGenerator[str]:
            response_parts: list[str] = []
            provider_stream = self._provider.stream(
                message=message,
                session_id=conversation.id,
                history=history,
                context=context,
            )
            try:
                async for text in provider_stream:
                    response_parts.append(text)
                    yield text
            finally:
                await provider_stream.aclose()

            await self._sessions.append_many(
                conversation.id,
                (
                    ConversationTurn(role="user", content=message),
                    ConversationTurn(
                        role="assistant",
                        content="".join(response_parts).strip(),
                    ),
                ),
            )

        return ChatResponse(
            session_id=conversation.id,
            sources=context,
            stream=generate(),
            _sessions=self._sessions,
            _lease_id=lease_id,
        )

    async def is_ready(self) -> bool:
        """Delegate readiness to the configured provider."""
        return await self._provider.is_ready()

    async def start(self) -> None:
        """Initialize provider resources."""
        await self._provider.start()

    async def close(self) -> None:
        """Release provider and retrieval resources."""
        await self._provider.close()
        await self._retriever.close()
