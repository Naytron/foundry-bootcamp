"""Configuration and credential-selection tests."""

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from support_assistant.config import Settings
from support_assistant.identity import create_credential


def test_mock_mode_does_not_require_cloud_values() -> None:
    settings = Settings(_env_file=None, app_env="test", use_mock_services=True)

    assert settings.foundry_project_endpoint is None


def test_cloud_mode_reports_all_missing_values() -> None:
    with pytest.raises(ValidationError, match=r"AZURE_AI_SEARCH_ENDPOINT.*FOUNDRY_MODEL"):
        Settings(_env_file=None, app_env="test", use_mock_services=False)


def test_production_rejects_default_access_token() -> None:
    with pytest.raises(ValidationError, match="BOOTCAMP_ACCESS_TOKEN"):
        Settings(
            _env_file=None,
            app_env="production",
            use_mock_services=False,
            foundry_project_endpoint="https://example.services.ai.azure.com/api/projects/demo",
            foundry_model="chat",
            azure_ai_search_endpoint="https://example.search.windows.net",
        )


def test_local_identity_uses_default_credential() -> None:
    settings = Settings(_env_file=None, app_env="test", use_mock_services=True)
    with patch("support_assistant.identity.DefaultAzureCredential") as credential:
        create_credential(settings)

    credential.assert_called_once_with(exclude_interactive_browser_credential=False)


def test_production_identity_uses_configured_managed_identity() -> None:
    settings = Settings(
        _env_file=None,
        app_env="production",
        use_mock_services=False,
        foundry_project_endpoint="https://example.services.ai.azure.com/api/projects/demo",
        foundry_model="chat",
        azure_ai_search_endpoint="https://example.search.windows.net",
        azure_client_id="00000000-0000-0000-0000-000000000001",
        bootcamp_access_token="non-default",
    )
    with patch("support_assistant.identity.ManagedIdentityCredential") as credential:
        create_credential(settings)

    credential.assert_called_once_with(client_id=settings.azure_client_id)
