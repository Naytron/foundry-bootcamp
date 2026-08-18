"""Chat provider protocol and provider-level errors."""

from collections.abc import AsyncGenerator, Sequence
from typing import Protocol
from uuid import UUID

from support_assistant.agent.models import ConversationTurn
from support_assistant.retrieval.models import KnowledgeDocument


class ChatProviderError(RuntimeError):
    """Raised when an AI provider cannot complete a response."""


class ChatProvider(Protocol):
    """Provider-neutral interface used by the application service."""

    def stream(
        self,
        *,
        message: str,
        session_id: UUID,
        history: Sequence[ConversationTurn],
        context: Sequence[KnowledgeDocument],
    ) -> AsyncGenerator[str]:
        """Stream response text for one conversation turn."""
        ...

    async def is_ready(self) -> bool:
        """Return whether the provider is configured to accept requests."""
        ...

    async def start(self) -> None:
        """Initialize provider resources."""
        ...

    async def close(self) -> None:
        """Release provider resources."""
        ...

    def discard_session(self, session_id: UUID) -> None:
        """Discard provider state after the application evicts a session."""
        ...
