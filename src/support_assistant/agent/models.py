"""Shared agent-domain models."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class ConversationTurn:
    """One user or assistant message retained for a bounded session."""

    role: Literal["user", "assistant"]
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass(slots=True)
class Conversation:
    """In-memory conversation metadata used by the workshop application."""

    id: UUID = field(default_factory=uuid4)
    turns: list[ConversationTurn] = field(default_factory=list)
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
