"""Deterministic chat provider for local learning and automated tests."""

import asyncio
import json
import re
from collections.abc import AsyncGenerator, Sequence
from typing import ClassVar
from uuid import UUID

from support_assistant.agent.models import ConversationTurn
from support_assistant.retrieval.local import STOP_WORDS
from support_assistant.retrieval.models import KnowledgeDocument
from support_assistant.tools.support import create_case_draft, get_warranty_record

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
SERIAL_PATTERN = re.compile(r"\bCTS-\d{5}\b", re.IGNORECASE)


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
        context: Sequence[KnowledgeDocument],
    ) -> AsyncGenerator[str]:
        """Yield a deterministic response in small chunks to exercise streaming."""
        del session_id
        normalized = message.casefold()
        serial = SERIAL_PATTERN.search(message)
        if serial:
            response = json.dumps(get_warranty_record(serial.group()), separators=(",", ":"))
        elif "draft" in normalized and ("case" in normalized or "ticket" in normalized):
            response = json.dumps(
                create_case_draft(
                    product="Contoso Trail Sensor",
                    summary=message,
                    urgency="normal",
                ),
                separators=(",", ":"),
            )
        elif {"battery", "hot", "smoke", "smoking"} & set(TOKEN_PATTERN.findall(normalized)):
            response = (
                "Escalate immediately when a customer reports a safety hazard, smoke, "
                "heat, or a damaged battery. [support-escalation]"
            )
        elif context:
            source = context[0]
            paragraph = self._best_paragraph(source.content, message)
            response = f"Based on {source.title}: {paragraph} [{source.id}]"
        else:
            response = next(
                (text for keyword, text in self._RESPONSES.items() if keyword in normalized),
                (
                    "I am running in local mock mode. Ask about a password reset, warranty, "
                    "or support ticket."
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

    async def start(self) -> None:
        """No resources are required."""

    async def close(self) -> None:
        """No resources are held."""

    def discard_session(self, session_id: UUID) -> None:
        """Mock mode has no provider session state."""
        del session_id

    @staticmethod
    def _best_paragraph(content: str, query: str) -> str:
        terms = set(TOKEN_PATTERN.findall(query.casefold())) - STOP_WORDS
        paragraphs = [
            paragraph.strip()
            for paragraph in content.split("\n\n")
            if paragraph.strip() and not paragraph.lstrip().startswith("#")
        ]
        return max(
            paragraphs,
            key=lambda paragraph: sum(
                term in terms for term in TOKEN_PATTERN.findall(paragraph.casefold())
            ),
        )
