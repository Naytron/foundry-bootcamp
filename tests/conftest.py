"""Shared test fixtures."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from support_assistant.config import Settings
from support_assistant.main import create_app


@pytest.fixture
def settings() -> Settings:
    """Return isolated mock-mode settings."""
    return Settings(
        _env_file=None,
        app_env="test",
        use_mock_services=True,
        bootcamp_access_token="test-token",
        rate_limit_requests=10,
    )


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    """Run the FastAPI lifespan around each API test."""
    with TestClient(create_app(settings)) as test_client:
        yield test_client
