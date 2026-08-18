"""Chat orchestration tests."""

from collections.abc import AsyncIterator
from uuid import UUID

import pytest

from support_assistant.agent.mock import MockChatProvider
from support_assistant.agent.models import ConversationTurn
from support_assistant.agent.provider import ChatProviderError
from support_assistant.agent.service import ChatService
from support_assistant.agent.sessions import SessionStore
from support_assistant.retrieval.provider import NullKnowledgeRetriever


async def _collect(stream: AsyncIterator[str]) -> str:
    parts = [part async for part in stream]
    return "".join(parts)


async def test_chat_service_streams_and_continues_session() -> None:
    service = ChatService(
        MockChatProvider(),
        SessionStore(max_sessions=10, ttl_seconds=60),
        NullKnowledgeRetriever(),
    )

    first_response = await service.stream(
        message="password",
        session_id=None,
    )
    first = await _collect(first_response.stream)
    await first_response.close()
    second_response = await service.stream(
        message="warranty",
        session_id=first_response.session_id,
    )
    second = await _collect(second_response.stream)
    await second_response.close()

    assert "reset" in first.casefold()
    assert second.startswith("Continuing our conversation")


async def test_mock_provider_default_and_ready() -> None:
    provider = MockChatProvider()

    parts = [
        part
        async for part in provider.stream(
            message="hello",
            session_id=__import__("uuid").uuid4(),
            history=(),
            context=(),
        )
    ]

    assert "mock mode" in "".join(parts)
    assert await provider.is_ready()


async def test_closing_response_closes_nested_provider_before_releasing_lease() -> None:
    class TrackingProvider(MockChatProvider):
        def __init__(self) -> None:
            self.closed = False

        async def stream(
            self,
            *,
            message: str,
            session_id: UUID,
            history: object,
            context: object,
        ) -> AsyncIterator[str]:
            del message, session_id, history, context
            try:
                yield "first"
                yield "second"
            finally:
                self.closed = True

    provider = TrackingProvider()
    service = ChatService(
        provider,
        SessionStore(max_sessions=1, ttl_seconds=60),
        NullKnowledgeRetriever(),
    )
    response = await service.stream(message="hello", session_id=None)

    assert await anext(response.stream) == "first"
    await response.close()

    assert provider.closed
    next_response = await service.stream(
        message="hello again",
        session_id=response.session_id,
    )
    await next_response.close()


async def test_failed_stream_does_not_commit_unmatched_user_turn() -> None:
    class FailingOnceProvider(MockChatProvider):
        def __init__(self) -> None:
            self.calls = 0
            self.histories: list[tuple[ConversationTurn, ...]] = []

        async def stream(
            self,
            *,
            message: str,
            session_id: UUID,
            history: tuple[ConversationTurn, ...],
            context: object,
        ) -> AsyncIterator[str]:
            del message, session_id, context
            self.histories.append(history)
            self.calls += 1
            if self.calls == 1:
                yield "partial"
                raise ChatProviderError("failed")
            yield "complete"

    provider = FailingOnceProvider()
    service = ChatService(
        provider,
        SessionStore(max_sessions=1, ttl_seconds=60, max_turns=2),
        NullKnowledgeRetriever(),
    )
    first = await service.stream(message="first", session_id=None)
    with pytest.raises(ChatProviderError):
        await _collect(first.stream)
    await first.close()

    second = await service.stream(message="second", session_id=first.session_id)
    assert await _collect(second.stream) == "complete"
    await second.close()

    assert provider.histories == [(), ()]
