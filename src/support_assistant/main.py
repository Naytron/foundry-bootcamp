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
from support_assistant.agent.provider import ChatProvider
from support_assistant.agent.service import ChatService
from support_assistant.agent.sessions import SessionStore
from support_assistant.api.middleware import (
    AccessTokenMiddleware,
    RateLimitMiddleware,
    RequestContextMiddleware,
)
from support_assistant.api.routes import router
from support_assistant.config import Settings, get_settings
from support_assistant.identity import AzureCredential, create_credential
from support_assistant.observability import configure_observability
from support_assistant.retrieval.azure_search import AzureSearchRetriever
from support_assistant.retrieval.embeddings import FoundryEmbeddingProvider
from support_assistant.retrieval.local import LocalKnowledgeRetriever
from support_assistant.retrieval.provider import KnowledgeRetriever

WEB_ROOT = Path(__file__).parent / "web"


def _configure_logging(settings: Settings) -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def _create_chat_service(settings: Settings) -> tuple[ChatService, AzureCredential | None]:
    credential: AzureCredential | None = None
    provider: ChatProvider
    retriever: KnowledgeRetriever
    if settings.use_mock_services:
        provider = MockChatProvider()
        retriever = LocalKnowledgeRetriever(
            settings.knowledge_base_path,
            top_k=settings.retrieval_top_k,
        )
    else:
        credential = create_credential(settings)
        provider = FoundryChatProvider(settings, credential)
        embeddings = (
            FoundryEmbeddingProvider(
                endpoint=str(settings.foundry_project_endpoint).rstrip("/"),
                model=settings.embedding_model,
                credential=credential,
            )
            if settings.embedding_model
            else None
        )
        retriever = AzureSearchRetriever(
            endpoint=str(settings.azure_ai_search_endpoint).rstrip("/"),
            index_name=settings.azure_ai_search_index,
            semantic_configuration=settings.azure_ai_search_semantic_configuration,
            vector_field=settings.azure_ai_search_vector_field,
            credential=credential,
            top_k=settings.retrieval_top_k,
            embeddings=embeddings,
        )

    sessions = SessionStore(
        max_sessions=settings.max_sessions,
        ttl_seconds=settings.session_ttl_seconds,
        max_turns=settings.max_session_turns * 2,
        on_evict=provider.discard_session,
    )
    return ChatService(provider, sessions, retriever), credential


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create an application instance with explicit, testable dependencies."""
    resolved_settings = settings or get_settings()
    _configure_logging(resolved_settings)
    configure_observability(resolved_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        chat_service, credential = _create_chat_service(resolved_settings)
        app.state.settings = resolved_settings
        app.state.chat_service = chat_service
        await chat_service.start()
        try:
            yield
        finally:
            await chat_service.close()
            if credential:
                credential.close()

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
