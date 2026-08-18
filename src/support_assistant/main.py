"""FastAPI application entry point."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from support_assistant import __version__
from support_assistant.agent.foundry import FoundryChatProvider
from support_assistant.agent.mock import MockChatProvider
from support_assistant.agent.service import ChatService
from support_assistant.agent.sessions import SessionStore
from support_assistant.api.middleware import (
    AccessTokenMiddleware,
    RateLimitMiddleware,
    RequestContextMiddleware,
)
from support_assistant.api.routes import router
from support_assistant.config import Settings, get_settings
from support_assistant.identity import create_credential

WEB_ROOT = Path(__file__).parent / "web"


def _configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def _create_chat_service(settings: Settings) -> ChatService:
    provider = (
        MockChatProvider()
        if settings.use_mock_services
        else FoundryChatProvider(settings, create_credential(settings))
    )
    sessions = SessionStore(
        max_sessions=settings.max_sessions,
        ttl_seconds=settings.session_ttl_seconds,
    )
    return ChatService(provider, sessions)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create an application instance with explicit, testable dependencies."""
    resolved_settings = settings or get_settings()
    _configure_logging(resolved_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.settings = resolved_settings
        app.state.chat_service = _create_chat_service(resolved_settings)
        yield

    app = FastAPI(
        title="Foundry AI Bootcamp Support Assistant",
        version=__version__,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    app.add_middleware(AccessTokenMiddleware, settings=resolved_settings)
    app.add_middleware(RateLimitMiddleware, settings=resolved_settings)
    app.add_middleware(RequestContextMiddleware)
    app.include_router(router)
    app.mount("/", StaticFiles(directory=WEB_ROOT, html=True), name="web")
    return app


app = create_app()
