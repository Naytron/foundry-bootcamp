"""Chat provider protocol and provider-level errors."""

from collections.abc import AsyncIterator, Sequence
from typing import Protocol
from uuid import UUID

from support_assistant.agent.models import ConversationTurn


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
    ) -> AsyncIterator[str]:
        """Stream response text for one conversation turn."""
        ...

    async def is_ready(self) -> bool:
        """Return whether the provider is configured to accept requests."""
        ...
