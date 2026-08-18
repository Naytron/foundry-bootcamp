"""FastAPI contract and middleware tests."""

import json
from collections.abc import AsyncIterator
from types import SimpleNamespace
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from starlette.requests import Request

from support_assistant.agent.mock import MockChatProvider
from support_assistant.agent.service import ChatService
from support_assistant.agent.sessions import SessionStore
from support_assistant.api.models import ChatRequest
from support_assistant.api.routes import chat
from support_assistant.config import Settings
from support_assistant.main import create_app
from support_assistant.retrieval.provider import NullKnowledgeRetriever


def test_health_and_readiness_are_public(client: TestClient) -> None:
    health = client.get("/health")
    ready = client.get("/ready")

    assert health.status_code == 200
    assert health.json() == {"status": "healthy", "mode": "mock"}
    assert ready.status_code == 200
    assert ready.json() == {"status": "ready", "mode": "mock"}
    assert health.headers["x-content-type-options"] == "nosniff"


def test_browser_configuration_contains_no_secret(client: TestClient) -> None:
    response = client.get("/api/config")

    assert response.status_code == 200
    assert response.json()["mode"] == "mock"
    assert "token" not in json.dumps(response.json()).casefold()


def test_chat_requires_bearer_token(client: TestClient) -> None:
    response = client.post("/api/chat", json={"message": "hello"})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_chat_streams_metadata_text_and_completion(client: TestClient) -> None:
    with client.stream(
        "POST",
        "/api/chat",
        headers={"Authorization": "Bearer test-token", "x-request-id": "request-123"},
        json={"message": "How do I reset my password?"},
    ) as response:
        body = "".join(response.iter_text())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["x-request-id"] == "request-123"
    assert "event: metadata" in body
    assert "event: delta" in body
    assert "event: citations" in body
    assert "event: done" in body
    assert "reset" in body.casefold()


def test_chat_rejects_blank_and_oversized_messages(client: TestClient) -> None:
    headers = {"Authorization": "Bearer test-token"}

    blank = client.post("/api/chat", headers=headers, json={"message": "  "})
    oversized = client.post("/api/chat", headers=headers, json={"message": "x" * 4_001})

    assert blank.status_code == 422
    assert oversized.status_code == 422


def test_rate_limit_returns_retry_after() -> None:
    settings = Settings(
        _env_file=None,
        app_env="test",
        use_mock_services=True,
        bootcamp_access_token="test-token",
        rate_limit_requests=1,
        rate_limit_window_seconds=10,
    )
    with TestClient(create_app(settings)) as client:
        headers = {"Authorization": "Bearer test-token"}
        first = client.post("/api/chat", headers=headers, json={"message": "hello"})
        second = client.post("/api/chat", headers=headers, json={"message": "hello"})

    assert first.status_code == 200
    assert second.status_code == 429
    assert second.headers["retry-after"] == "10"


def test_static_chat_page_loads(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Contoso Support Assistant" in response.text
    assert response.headers["content-security-policy"].startswith("default-src")


def test_not_ready_provider_returns_service_unavailable(client: TestClient) -> None:
    class NotReadyService:
        async def is_ready(self) -> bool:
            return False

    client.app.state.chat_service = NotReadyService()

    response = client.get("/ready")

    assert response.status_code == 503


def test_provider_error_is_returned_as_safe_stream_event(client: TestClient) -> None:
    from support_assistant.agent.provider import ChatProviderError

    class FailingService:
        async def stream(self, *, message: str, session_id: UUID | None) -> object:
            del message, session_id

            async def fail() -> AsyncIterator[str]:
                if False:
                    yield ""
                raise ChatProviderError("sensitive detail")

            class FailingResponse:
                def __init__(self) -> None:
                    self.session_id = uuid4()
                    self.sources: list[object] = []
                    self.stream = fail()

                async def close(self) -> None:
                    await self.stream.aclose()

            return FailingResponse()

    client.app.state.chat_service = FailingService()

    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer test-token"},
        json={"message": "hello"},
    )

    assert response.status_code == 200
    assert "event: error" in response.text
    assert "sensitive detail" not in response.text


def test_retrieval_error_returns_safe_service_unavailable(client: TestClient) -> None:
    from support_assistant.retrieval.provider import RetrievalError

    class FailingRetrievalService:
        async def stream(self, *, message: str, session_id: UUID | None) -> None:
            del message, session_id
            raise RetrievalError("sensitive search detail")

    client.app.state.chat_service = FailingRetrievalService()

    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer test-token"},
        json={"message": "hello"},
    )

    assert response.status_code == 503
    assert "temporarily unavailable" in response.json()["detail"]
    assert "sensitive search detail" not in response.text


def test_overlapping_session_returns_conflict(client: TestClient) -> None:
    from support_assistant.agent.sessions import SessionBusyError

    class BusyService:
        async def stream(self, *, message: str, session_id: UUID | None) -> None:
            del message, session_id
            raise SessionBusyError("internal state")

    client.app.state.chat_service = BusyService()

    response = client.post(
        "/api/chat",
        headers={"Authorization": "Bearer test-token"},
        json={"message": "hello"},
    )

    assert response.status_code == 409
    assert "Wait for the current response" in response.json()["detail"]


async def test_closing_stream_after_metadata_releases_session_lease() -> None:
    service = ChatService(
        MockChatProvider(),
        SessionStore(max_sessions=1, ttl_seconds=60),
        NullKnowledgeRetriever(),
    )
    app = SimpleNamespace(
        state=SimpleNamespace(
            settings=Settings(
                _env_file=None,
                app_env="test",
                use_mock_services=True,
                bootcamp_access_token="test-token",
            ),
            chat_service=service,
        )
    )
    request = Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/api/chat",
            "headers": [],
            "query_string": b"",
            "server": ("testserver", 80),
            "client": ("testclient", 123),
            "scheme": "http",
            "app": app,
            "state": {"request_id": "early-disconnect"},
        }
    )

    response = await chat(ChatRequest(message="hello"), request)
    iterator = response.body_iterator
    metadata = await anext(iterator)
    await iterator.aclose()

    metadata_text = metadata.decode() if isinstance(metadata, bytes) else metadata
    metadata_json = json.loads(metadata_text.split("data: ", maxsplit=1)[1])
    session_id = UUID(metadata_json["session_id"])
    next_response = await service.stream(
        message="hello again",
        session_id=session_id,
    )
    await next_response.close()
