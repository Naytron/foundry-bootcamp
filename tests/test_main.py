"""Application composition and entry-point tests."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from support_assistant.__main__ import main
from support_assistant.config import Settings
from support_assistant.main import _create_chat_service


def _cloud_settings() -> Settings:
    return Settings(
        _env_file=None,
        app_env="production",
        use_mock_services=False,
        foundry_project_endpoint="https://example.services.ai.azure.com/api/projects/demo",
        foundry_model="chat",
        embedding_model="embedding",
        azure_ai_search_endpoint="https://example.search.windows.net",
        bootcamp_access_token="test-token",
    )


def test_cloud_composition_wires_foundry_search_and_embeddings() -> None:
    credential = MagicMock()
    with (
        patch("support_assistant.main.create_credential", return_value=credential),
        patch("support_assistant.main.FoundryChatProvider") as foundry,
        patch("support_assistant.main.FoundryEmbeddingProvider") as embeddings,
        patch("support_assistant.main.AzureSearchRetriever") as search,
    ):
        service, resolved_credential = _create_chat_service(_cloud_settings())

    assert service is not None
    assert resolved_credential is credential
    foundry.assert_called_once()
    embeddings.assert_called_once()
    search.assert_called_once()


def test_module_entry_point_passes_validated_settings_to_uvicorn() -> None:
    settings = SimpleNamespace(app_host="127.0.0.1", port=9000, app_env="test")
    with (
        patch("support_assistant.__main__.get_settings", return_value=settings),
        patch("support_assistant.__main__.uvicorn.run") as run,
    ):
        main()

    run.assert_called_once_with(
        "support_assistant.main:app",
        host="127.0.0.1",
        port=9000,
        reload=False,
    )
