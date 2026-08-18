"""Bounded, expiring in-memory conversation storage."""

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

from support_assistant.agent.models import Conversation, ConversationTurn


class SessionStore:
    """Store a small number of short-lived conversations for the workshop."""

    def __init__(self, *, max_sessions: int, ttl_seconds: int) -> None:
        self._max_sessions = max_sessions
        self._ttl = timedelta(seconds=ttl_seconds)
        self._conversations: dict[UUID, Conversation] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(self, session_id: UUID | None) -> Conversation:
        """Return a live session or create a new one after pruning expired entries."""
        async with self._lock:
            self._prune()
            if session_id and session_id in self._conversations:
                conversation = self._conversations[session_id]
                conversation.updated_at = datetime.now(UTC)
                return conversation

            if len(self._conversations) >= self._max_sessions:
                oldest_id = min(
                    self._conversations,
                    key=lambda key: self._conversations[key].updated_at,
                )
                del self._conversations[oldest_id]

            conversation = Conversation()
            self._conversations[conversation.id] = conversation
            return conversation

    async def append(self, session_id: UUID, turn: ConversationTurn) -> None:
        """Append a turn to an existing conversation."""
        async with self._lock:
            conversation = self._conversations[session_id]
            conversation.turns.append(turn)
            conversation.updated_at = datetime.now(UTC)

    def _prune(self) -> None:
        cutoff = datetime.now(UTC) - self._ttl
        expired = [
            session_id
            for session_id, conversation in self._conversations.items()
            if conversation.updated_at < cutoff
        ]
        for session_id in expired:
            del self._conversations[session_id]
