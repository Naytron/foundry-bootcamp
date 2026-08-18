"""Chat orchestration tests."""

from collections.abc import AsyncIterator

from support_assistant.agent.mock import MockChatProvider
from support_assistant.agent.service import ChatService
from support_assistant.agent.sessions import SessionStore


async def _collect(stream: AsyncIterator[str]) -> str:
    parts = [part async for part in stream]
    return "".join(parts)


async def test_chat_service_streams_and_continues_session() -> None:
    service = ChatService(
        MockChatProvider(),
        SessionStore(max_sessions=10, ttl_seconds=60),
    )

    session_id, first_stream = await service.stream(message="password", session_id=None)
    first = await _collect(first_stream)
    _, second_stream = await service.stream(message="warranty", session_id=session_id)
    second = await _collect(second_stream)

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
        )
    ]

    assert "mock mode" in "".join(parts)
    assert await provider.is_ready()
