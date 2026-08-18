"""Privacy-conscious OpenTelemetry configuration for Azure Monitor."""

import os

from azure.monitor.opentelemetry import configure_azure_monitor

from support_assistant.config import Settings

_configured = False


def configure_observability(settings: Settings) -> bool:
    """Configure Azure Monitor only when an Application Insights target is present."""
    global _configured
    if _configured or not settings.applicationinsights_connection_string:
        return _configured

    os.environ["AZURE_EXPERIMENTAL_ENABLE_GENAI_TRACING"] = "true"
    os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = (
        "true" if settings.capture_message_content else "false"
    )
    configure_azure_monitor(
        connection_string=settings.applicationinsights_connection_string.get_secret_value(),
        enable_live_metrics=False,
    )
    _instrument_foundry_project_client()
    _configured = True
    return True


def _instrument_foundry_project_client() -> None:
    from azure.ai.projects.telemetry import AIProjectInstrumentor

    AIProjectInstrumentor().instrument()
