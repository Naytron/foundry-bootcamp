"""Bounded, expiring in-memory conversation storage."""

import asyncio
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from support_assistant.agent.models import Conversation, ConversationTurn


class SessionCapacityError(RuntimeError):
    """Raised when every bounded session slot is actively streaming."""


class SessionBusyError(RuntimeError):
    """Raised when a second request overlaps an active conversation turn."""


class SessionStore:
    """Store a small number of short-lived conversations for the workshop."""

    def __init__(
        self,
        *,
        max_sessions: int,
        ttl_seconds: int,
        max_turns: int = 20,
        on_evict: Callable[[UUID], None] | None = None,
    ) -> None:
        self._max_sessions = max_sessions
        self._max_turns = max_turns
        self._ttl = timedelta(seconds=ttl_seconds)
        self._on_evict = on_evict
        self._conversations: dict[UUID, Conversation] = {}
        self._active: dict[UUID, UUID] = {}
        self._lock = asyncio.Lock()

    async def get_or_create(self, session_id: UUID | None) -> tuple[Conversation, UUID]:
        """Acquire a uniquely owned lease on a live or newly created session."""
        async with self._lock:
            self._prune()
            lease_id = uuid4()
            if session_id and session_id in self._conversations:
                conversation = self._conversations[session_id]
                if conversation.id in self._active:
                    raise SessionBusyError("A conversation turn is already in progress")
                self._active[conversation.id] = lease_id
                conversation.updated_at = datetime.now(UTC)
                return conversation, lease_id

            if len(self._conversations) >= self._max_sessions:
                inactive = [key for key in self._conversations if key not in self._active]
                if not inactive:
                    raise SessionCapacityError("All conversation slots are active")
                oldest_id = min(inactive, key=lambda key: self._conversations[key].updated_at)
                self._evict(oldest_id)

            conversation = Conversation()
            self._conversations[conversation.id] = conversation
            self._active[conversation.id] = lease_id
            return conversation, lease_id

    async def append(self, session_id: UUID, turn: ConversationTurn) -> None:
        """Append a turn to an existing conversation."""
        await self.append_many(session_id, (turn,))

    async def append_many(
        self,
        session_id: UUID,
        turns: tuple[ConversationTurn, ...],
    ) -> None:
        """Append related turns atomically so history keeps complete exchanges."""
        async with self._lock:
            conversation = self._conversations[session_id]
            conversation.turns.extend(turns)
            if len(conversation.turns) > self._max_turns:
                del conversation.turns[: -self._max_turns]
            conversation.updated_at = datetime.now(UTC)

    async def release(self, session_id: UUID, lease_id: UUID) -> None:
        """Release only the lease owned by the caller."""
        async with self._lock:
            if self._active.get(session_id) == lease_id:
                self._active.pop(session_id, None)

    def _prune(self) -> None:
        cutoff = datetime.now(UTC) - self._ttl
        expired = [
            session_id
            for session_id, conversation in self._conversations.items()
            if conversation.updated_at < cutoff and session_id not in self._active
        ]
        for session_id in expired:
            self._evict(session_id)

    def _evict(self, session_id: UUID) -> None:
        del self._conversations[session_id]
        self._active.pop(session_id, None)
        if self._on_evict:
            self._on_evict(session_id)
