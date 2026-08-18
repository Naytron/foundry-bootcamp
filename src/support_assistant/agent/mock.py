"""Deterministic chat provider for local learning and automated tests."""

import asyncio
from collections.abc import AsyncIterator, Sequence
from typing import ClassVar
from uuid import UUID

from support_assistant.agent.models import ConversationTurn


class MockChatProvider:
    """Return stable support responses without calling Azure."""

    _RESPONSES: ClassVar[dict[str, str]] = {
        "password": (
            "To reset your Contoso Support Portal password, select **Forgot password** "
            "on the sign-in page and follow the verification steps. Mock mode does not "
            "send email or change an account."
        ),
        "warranty": (
            "Warranty coverage depends on the product and purchase date. In Day 2, the "
            "agent will look up the synthetic warranty policy and cite its source."
        ),
        "ticket": (
            "I can draft a support case, but I will ask for confirmation before a "
            "side-effect-shaped action. Mock mode never sends a real ticket."
        ),
    }

    async def stream(
        self,
        *,
        message: str,
        session_id: UUID,
        history: Sequence[ConversationTurn],
    ) -> AsyncIterator[str]:
        """Yield a deterministic response in small chunks to exercise streaming."""
        del session_id
        normalized = message.casefold()
        response = next(
            (text for keyword, text in self._RESPONSES.items() if keyword in normalized),
            (
                "I am running in local mock mode. Ask about a password reset, warranty, "
                "or support ticket. Day 2 replaces this response with grounded retrieval."
            ),
        )
        if history:
            response = f"Continuing our conversation: {response}"

        words = response.split()
        for index in range(0, len(words), 4):
            await asyncio.sleep(0)
            yield " ".join(words[index : index + 4]) + " "

    async def is_ready(self) -> bool:
        """Mock mode is always ready."""
        return True
