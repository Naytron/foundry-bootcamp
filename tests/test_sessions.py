"""Conversation session-store tests."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from support_assistant.agent.models import ConversationTurn
from support_assistant.agent.sessions import SessionBusyError, SessionStore


async def test_session_store_reuses_known_session() -> None:
    store = SessionStore(max_sessions=2, ttl_seconds=60)
    first, first_lease = await store.get_or_create(None)
    await store.release(first.id, first_lease)

    second, _ = await store.get_or_create(first.id)

    assert second is first


async def test_session_store_evicts_oldest_when_bounded() -> None:
    store = SessionStore(max_sessions=1, ttl_seconds=60)
    first, first_lease = await store.get_or_create(None)
    await store.release(first.id, first_lease)
    second, second_lease = await store.get_or_create(None)
    await store.release(second.id, second_lease)

    replacement, _ = await store.get_or_create(first.id)

    assert second.id != first.id
    assert replacement.id != first.id


async def test_session_store_prunes_expired_session() -> None:
    store = SessionStore(max_sessions=2, ttl_seconds=60)
    expired, expired_lease = await store.get_or_create(None)
    await store.release(expired.id, expired_lease)
    expired.updated_at = datetime.now(UTC) - timedelta(minutes=2)

    replacement, _ = await store.get_or_create(expired.id)

    assert replacement.id != expired.id


async def test_session_store_appends_turn() -> None:
    store = SessionStore(max_sessions=2, ttl_seconds=60)
    conversation, _ = await store.get_or_create(None)
    turn = ConversationTurn(role="user", content="hello")

    await store.append(conversation.id, turn)

    assert conversation.turns == [turn]


async def test_session_store_bounds_retained_turns() -> None:
    store = SessionStore(max_sessions=2, ttl_seconds=60, max_turns=2)
    conversation, _ = await store.get_or_create(None)

    for content in ("one", "two", "three"):
        await store.append(conversation.id, ConversationTurn(role="user", content=content))

    assert [turn.content for turn in conversation.turns] == ["two", "three"]


async def test_session_store_trims_complete_exchange_atomically() -> None:
    store = SessionStore(max_sessions=2, ttl_seconds=60, max_turns=2)
    conversation, _ = await store.get_or_create(None)

    await store.append_many(
        conversation.id,
        (
            ConversationTurn(role="user", content="first question"),
            ConversationTurn(role="assistant", content="first answer"),
        ),
    )
    await store.append_many(
        conversation.id,
        (
            ConversationTurn(role="user", content="second question"),
            ConversationTurn(role="assistant", content="second answer"),
        ),
    )

    assert [(turn.role, turn.content) for turn in conversation.turns] == [
        ("user", "second question"),
        ("assistant", "second answer"),
    ]


async def test_session_store_rejects_new_session_when_all_slots_are_active() -> None:
    from support_assistant.agent.sessions import SessionCapacityError

    store = SessionStore(max_sessions=1, ttl_seconds=60)
    await store.get_or_create(None)

    with pytest.raises(SessionCapacityError, match="slots are active"):
        await store.get_or_create(None)


async def test_session_store_rejects_overlapping_turns() -> None:
    store = SessionStore(max_sessions=2, ttl_seconds=60)
    conversation, _ = await store.get_or_create(None)

    with pytest.raises(SessionBusyError, match="already in progress"):
        await store.get_or_create(conversation.id)


async def test_session_store_notifies_provider_when_evicted() -> None:
    evicted = []
    store = SessionStore(max_sessions=1, ttl_seconds=60, on_evict=evicted.append)
    first, first_lease = await store.get_or_create(None)
    await store.release(first.id, first_lease)

    await store.get_or_create(None)

    assert evicted == [first.id]


async def test_unknown_id_creates_new_session() -> None:
    store = SessionStore(max_sessions=2, ttl_seconds=60)

    conversation, _ = await store.get_or_create(uuid4())

    assert conversation.turns == []


async def test_stale_release_cannot_unlock_newer_lease() -> None:
    store = SessionStore(max_sessions=2, ttl_seconds=60)
    conversation, first_lease = await store.get_or_create(None)
    await store.release(conversation.id, first_lease)
    _, second_lease = await store.get_or_create(conversation.id)

    await store.release(conversation.id, first_lease)

    with pytest.raises(SessionBusyError):
        await store.get_or_create(conversation.id)
    await store.release(conversation.id, second_lease)
