"""Application service that coordinates sessions and a chat provider."""

from collections.abc import AsyncIterator
from uuid import UUID

from support_assistant.agent.models import ConversationTurn
from support_assistant.agent.provider import ChatProvider
from support_assistant.agent.sessions import SessionStore


class ChatService:
    """Coordinate a provider response with bounded session history."""

    def __init__(self, provider: ChatProvider, sessions: SessionStore) -> None:
        self._provider = provider
        self._sessions = sessions

    async def stream(
        self, *, message: str, session_id: UUID | None
    ) -> tuple[UUID, AsyncIterator[str]]:
        """Create the response stream and return its effective session identifier."""
        conversation = await self._sessions.get_or_create(session_id)
        history = tuple(conversation.turns)
        await self._sessions.append(
            conversation.id,
            ConversationTurn(role="user", content=message),
        )

        async def generate() -> AsyncIterator[str]:
            response_parts: list[str] = []
            async for text in self._provider.stream(
                message=message,
                session_id=conversation.id,
                history=history,
            ):
                response_parts.append(text)
                yield text

            await self._sessions.append(
                conversation.id,
                ConversationTurn(role="assistant", content="".join(response_parts).strip()),
            )

        return conversation.id, generate()

    async def is_ready(self) -> bool:
        """Delegate readiness to the configured provider."""
        return await self._provider.is_ready()
