"""Microsoft Foundry provider adapter tests."""

from collections.abc import AsyncIterator
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from agent_framework.exceptions import ChatClientException
from azure.core.exceptions import HttpResponseError
from openai import OpenAIError

from support_assistant.agent.foundry import FoundryChatProvider
from support_assistant.agent.models import ConversationTurn
from support_assistant.agent.provider import ChatProviderError
from support_assistant.config import Settings
from support_assistant.retrieval.models import KnowledgeDocument


class FakeAgent:
    """Minimal Agent Framework stand-in."""

    def __init__(self) -> None:
        self.sessions: list[object] = []
        self.entered = False
        self.exited = False
        self.last_message: object = ""

    def create_session(self) -> object:
        session = object()
        self.sessions.append(session)
        return session

    def run(self, message: object, **_: object) -> AsyncIterator[object]:
        self.last_message = message

        async def updates() -> AsyncIterator[object]:
            yield MagicMock(text="Grounded ")
            yield MagicMock(text="answer")

        return updates()

    async def __aenter__(self) -> "FakeAgent":
        self.entered = True
        return self

    async def __aexit__(self, *_: object) -> None:
        self.exited = True


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        app_env="test",
        use_mock_services=False,
        foundry_project_endpoint="https://example.services.ai.azure.com/api/projects/demo",
        foundry_model="chat",
        azure_ai_search_endpoint="https://example.search.windows.net",
        bootcamp_access_token="test-token",
    )


def _source() -> KnowledgeDocument:
    return KnowledgeDocument(
        id="policy",
        title="Policy",
        content="Reference content",
        product="Product",
        source_url="https://support.contoso.example/policy",
        updated="2026-01-01",
    )


async def test_foundry_provider_streams_grounded_message_and_lifecycle() -> None:
    fake_agent = FakeAgent()
    with (
        patch("support_assistant.agent.foundry.FoundryChatClient") as client,
        patch("support_assistant.agent.foundry.Agent", return_value=fake_agent) as agent_type,
    ):
        provider = FoundryChatProvider(_settings(), MagicMock())
        await provider.start()
        parts = [
            text
            async for text in provider.stream(
                message="What is the policy?",
                session_id=UUID(int=1),
                history=(),
                context=[_source()],
            )
        ]
        await provider.close()

    assert parts == ["Grounded ", "answer"]
    assert "<reference_data>" in fake_agent.last_message
    assert "<user_question>" in fake_agent.last_message
    assert fake_agent.entered and fake_agent.exited
    assert await provider.is_ready()
    client.assert_called_once()
    assert agent_type.call_args.kwargs["tools"]


async def test_foundry_provider_reuses_session() -> None:
    fake_agent = FakeAgent()
    with (
        patch("support_assistant.agent.foundry.FoundryChatClient"),
        patch("support_assistant.agent.foundry.Agent", return_value=fake_agent),
    ):
        provider = FoundryChatProvider(_settings(), MagicMock())
        session_id = UUID(int=2)
        for _ in range(2):
            _ = [
                text
                async for text in provider.stream(
                    message="hello",
                    session_id=session_id,
                    history=(),
                    context=(),
                )
            ]

    assert provider._sessions[session_id] is fake_agent.sessions[0]


async def test_foundry_provider_resets_bounded_session() -> None:
    fake_agent = FakeAgent()
    settings = _settings()
    settings.max_session_turns = 1
    with (
        patch("support_assistant.agent.foundry.FoundryChatClient"),
        patch("support_assistant.agent.foundry.Agent", return_value=fake_agent),
    ):
        provider = FoundryChatProvider(settings, MagicMock())
        session_id = UUID(int=4)
        for _ in range(2):
            _ = [
                text
                async for text in provider.stream(
                    message="hello",
                    session_id=session_id,
                    history=(
                        ConversationTurn(role="user", content="previous question"),
                        ConversationTurn(role="assistant", content="previous answer"),
                    ),
                    context=(),
                )
            ]

    assert len(fake_agent.sessions) == 2
    assert provider._sessions[session_id] is fake_agent.sessions[1]
    assert isinstance(fake_agent.last_message, list)
    assert len(fake_agent.last_message) == 3


async def test_foundry_provider_discards_evicted_session() -> None:
    fake_agent = FakeAgent()
    with (
        patch("support_assistant.agent.foundry.FoundryChatClient"),
        patch("support_assistant.agent.foundry.Agent", return_value=fake_agent),
    ):
        provider = FoundryChatProvider(_settings(), MagicMock())
        session_id = UUID(int=5)
        _ = [
            text
            async for text in provider.stream(
                message="hello",
                session_id=session_id,
                history=(),
                context=(),
            )
        ]
        provider.discard_session(session_id)

    assert session_id not in provider._sessions
    assert session_id not in provider._session_turns


async def test_foundry_provider_sanitizes_azure_errors() -> None:
    fake_agent = FakeAgent()
    fake_agent.run = MagicMock(side_effect=HttpResponseError("sensitive service detail"))
    with (
        patch("support_assistant.agent.foundry.FoundryChatClient"),
        patch("support_assistant.agent.foundry.Agent", return_value=fake_agent),
    ):
        provider = FoundryChatProvider(_settings(), MagicMock())

        with pytest.raises(ChatProviderError, match="could not complete"):
            _ = [
                text
                async for text in provider.stream(
                    message="hello",
                    session_id=UUID(int=3),
                    history=(),
                    context=(),
                )
            ]


async def test_foundry_provider_sanitizes_openai_errors() -> None:
    fake_agent = FakeAgent()
    fake_agent.run = MagicMock(side_effect=OpenAIError("sensitive OpenAI detail"))
    with (
        patch("support_assistant.agent.foundry.FoundryChatClient"),
        patch("support_assistant.agent.foundry.Agent", return_value=fake_agent),
    ):
        provider = FoundryChatProvider(_settings(), MagicMock())

        with pytest.raises(ChatProviderError, match="could not complete"):
            _ = [
                text
                async for text in provider.stream(
                    message="hello",
                    session_id=UUID(int=7),
                    history=(),
                    context=(),
                )
            ]


async def test_foundry_provider_sanitizes_agent_framework_errors() -> None:
    fake_agent = FakeAgent()
    fake_agent.run = MagicMock(side_effect=ChatClientException("framework detail"))
    with (
        patch("support_assistant.agent.foundry.FoundryChatClient"),
        patch("support_assistant.agent.foundry.Agent", return_value=fake_agent),
    ):
        provider = FoundryChatProvider(_settings(), MagicMock())

        with pytest.raises(ChatProviderError, match="could not complete"):
            _ = [
                text
                async for text in provider.stream(
                    message="hello",
                    session_id=UUID(int=8),
                    history=(),
                    context=(),
                )
            ]


def test_grounded_message_is_unchanged_without_context() -> None:
    assert FoundryChatProvider._grounded_message("hello", ()) == "hello"
