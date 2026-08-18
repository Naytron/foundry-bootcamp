"""OpenTelemetry configuration tests."""

import os
from unittest.mock import patch

from support_assistant.config import Settings
from support_assistant.observability import configure_observability


def _reset() -> None:
    import support_assistant.observability as observability

    observability._configured = False


def test_observability_is_disabled_without_connection_string() -> None:
    _reset()

    assert not configure_observability(Settings(_env_file=None, app_env="test"))


def test_observability_configures_once_without_content_capture() -> None:
    _reset()
    settings = Settings(
        _env_file=None,
        app_env="test",
        applicationinsights_connection_string="InstrumentationKey=test",
        capture_message_content=False,
    )
    with (
        patch("support_assistant.observability.configure_azure_monitor") as configure,
        patch("support_assistant.observability._instrument_foundry_project_client") as instrument,
    ):
        assert configure_observability(settings)
        assert configure_observability(settings)

    configure.assert_called_once_with(
        connection_string="InstrumentationKey=test",
        enable_live_metrics=False,
    )
    instrument.assert_called_once()
    assert os.environ["AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING"] == "true"
    assert os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] == "false"
    _reset()


def test_development_can_explicitly_enable_content_capture() -> None:
    _reset()
    settings = Settings(
        _env_file=None,
        app_env="development",
        applicationinsights_connection_string="InstrumentationKey=test",
        capture_message_content=True,
    )
    with (
        patch("support_assistant.observability.configure_azure_monitor"),
        patch("support_assistant.observability._instrument_foundry_project_client"),
    ):
        configure_observability(settings)

    assert os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] == "true"
    _reset()
