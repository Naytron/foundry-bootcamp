"""HTTP routes for health, configuration, and streaming chat."""

import json
import logging
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from opentelemetry import trace
from opentelemetry.trace import StatusCode
from starlette.background import BackgroundTask

from support_assistant.agent.provider import ChatProviderError
from support_assistant.agent.service import ChatService
from support_assistant.agent.sessions import SessionBusyError, SessionCapacityError
from support_assistant.api.models import ChatRequest, HealthResponse, PublicConfigResponse
from support_assistant.config import Settings
from support_assistant.retrieval.provider import RetrievalError

logger = logging.getLogger("support_assistant.api")
tracer = trace.get_tracer("support_assistant.api")

router = APIRouter()


def _event(name: str, payload: dict[str, object]) -> str:
    return f"event: {name}\ndata: {json.dumps(payload, separators=(',', ':'))}\n\n"


@router.get("/health", response_model=HealthResponse, tags=["operations"])
async def health(request: Request) -> HealthResponse:
    """Report process liveness without calling downstream services."""
    settings: Settings = request.app.state.settings
    return HealthResponse(
        status="healthy",
        mode="mock" if settings.use_mock_services else "azure",
    )


@router.get("/ready", response_model=HealthResponse, tags=["operations"])
async def ready(request: Request) -> HealthResponse:
    """Report whether the configured provider is ready."""
    settings: Settings = request.app.state.settings
    service: ChatService = request.app.state.chat_service
    if not await service.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The chat provider is not ready.",
        )
    return HealthResponse(
        status="ready",
        mode="mock" if settings.use_mock_services else "azure",
    )


@router.get("/api/config", response_model=PublicConfigResponse, tags=["configuration"])
async def public_config(request: Request) -> PublicConfigResponse:
    """Return non-sensitive configuration used by the browser client."""
    settings: Settings = request.app.state.settings
    return PublicConfigResponse(
        mode="mock" if settings.use_mock_services else "azure",
        max_message_characters=settings.max_message_characters,
    )


@router.post("/api/chat", tags=["chat"])
async def chat(payload: ChatRequest, request: Request) -> StreamingResponse:
    """Stream one assistant response as server-sent events."""
    settings: Settings = request.app.state.settings
    if len(payload.message) > settings.max_message_characters:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Message exceeds {settings.max_message_characters} characters.",
        )

    service: ChatService = request.app.state.chat_service
    request_id = request.state.request_id
    try:
        chat_response = await service.stream(
            message=payload.message,
            session_id=payload.session_id,
        )
    except (RetrievalError, SessionCapacityError) as exc:
        logger.exception("Chat request setup failed", extra={"request_id": request_id})
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The support assistant is temporarily unavailable.",
        ) from exc
    except SessionBusyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Wait for the current response before sending another message.",
        ) from exc

    session_id = chat_response.session_id
    sources = chat_response.sources
    response_stream = chat_response.stream

    async def events() -> AsyncIterator[str]:
        try:
            with tracer.start_as_current_span("support_assistant.chat_stream") as span:
                span.set_attribute("app.request.id", request_id)
                span.set_attribute("app.session.id", str(session_id))
                span.set_attribute("app.retrieval.source_count", len(sources))
                yield _event(
                    "metadata",
                    {"session_id": str(session_id), "request_id": request_id},
                )
                try:
                    async for text in response_stream:
                        yield _event("delta", {"text": text})
                    if sources:
                        yield _event(
                            "citations",
                            {
                                "sources": [
                                    {
                                        "id": source.id,
                                        "title": source.title,
                                        "url": source.source_url,
                                    }
                                    for source in sources
                                ]
                            },
                        )
                    yield _event("done", {"session_id": str(session_id)})
                except ChatProviderError:
                    span.set_status(StatusCode.ERROR, "chat provider failed")
                    logger.exception("Chat provider failed", extra={"request_id": request_id})
                    yield _event(
                        "error",
                        {
                            "message": "The assistant could not complete this response.",
                            "request_id": request_id,
                        },
                    )
        finally:
            await chat_response.close()

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-store",
            "X-Accel-Buffering": "no",
        },
        background=BackgroundTask(chat_response.close),
    )
