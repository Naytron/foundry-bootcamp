"""Conversation session-store tests."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from support_assistant.agent.models import ConversationTurn
from support_assistant.agent.sessions import SessionStore


async def test_session_store_reuses_known_session() -> None:
    store = SessionStore(max_sessions=2, ttl_seconds=60)
    first = await store.get_or_create(None)

    second = await store.get_or_create(first.id)

    assert second is first


async def test_session_store_evicts_oldest_when_bounded() -> None:
    store = SessionStore(max_sessions=1, ttl_seconds=60)
    first = await store.get_or_create(None)
    second = await store.get_or_create(None)

    replacement = await store.get_or_create(first.id)

    assert second.id != first.id
    assert replacement.id != first.id


async def test_session_store_prunes_expired_session() -> None:
    store = SessionStore(max_sessions=2, ttl_seconds=60)
    expired = await store.get_or_create(None)
    expired.updated_at = datetime.now(UTC) - timedelta(minutes=2)

    replacement = await store.get_or_create(expired.id)

    assert replacement.id != expired.id


async def test_session_store_appends_turn() -> None:
    store = SessionStore(max_sessions=2, ttl_seconds=60)
    conversation = await store.get_or_create(None)
    turn = ConversationTurn(role="user", content="hello")

    await store.append(conversation.id, turn)

    assert conversation.turns == [turn]


async def test_unknown_id_creates_new_session() -> None:
    store = SessionStore(max_sessions=2, ttl_seconds=60)

    conversation = await store.get_or_create(uuid4())

    assert conversation.turns == []
