"""
Tests for repository/message.py: no duplicates and correct sync.
Run from the project root:  pytest

Owner: Maryam
"""
from sqlalchemy import func, select

from app import models
from app.repository import message as message_repo
from app.schemas.message import MessageCreate

CLIENT_ID = "6f1c2a9e-0b7d-4c1e-9a55-3d2f8e7b1c04"


def count_messages(db) -> int:
    return db.scalar(select(func.count()).select_from(models.Message))


def test_same_client_msg_id_twice_is_stored_once(db, chat):
    """The phone resends a message whose ack was lost: we must not store a second copy."""
    alice, group = chat["alice"], chat["group"]

    first, created_first = message_repo.create_message(db, alice.user_id, group.group_id, CLIENT_ID, "hi")
    second, created_second = message_repo.create_message(db, alice.user_id, group.group_id, CLIENT_ID, "hi")

    assert created_first is True
    assert created_second is False
    assert second.message_id == first.message_id
    assert count_messages(db) == 1


def test_different_client_msg_ids_are_two_messages(db, chat):
    alice, group = chat["alice"], chat["group"]
    message_repo.create_message(db, alice.user_id, group.group_id, CLIENT_ID, "hi")
    message_repo.create_message(db, alice.user_id, group.group_id,
                                "0b7d6f1c-2a9e-4c1e-9a55-3d2f8e7b1c04", "hi again")
    assert count_messages(db) == 2


def test_uppercase_uuid_counts_as_the_same_message():
    """MessageCreate lowercases client_msg_id, so the duplicate check always matches."""
    body = MessageCreate(group_id=1, client_msg_id=CLIENT_ID.upper(), content="hi")
    assert body.client_msg_id == CLIENT_ID


def test_sync_returns_only_newer_messages_in_my_groups(db, chat):
    """Reconnect sync: everything after the last id the phone has, only from chats I am in."""
    alice, bob, carol, group = chat["alice"], chat["bob"], chat["carol"], chat["group"]
    ids = []
    for i in range(3):
        message, _ = message_repo.create_message(
            db, alice.user_id, group.group_id, f"00000000-0000-4000-8000-00000000000{i}", f"msg {i}")
        ids.append(message.message_id)

    # Bob had the first message, then went offline: he gets the other two, oldest first.
    missed = message_repo.get_after_for_user(db, bob.user_id, after_id=ids[0])
    assert [m.message_id for m in missed] == ids[1:]

    # Carol is not in the group, so she gets nothing.
    assert message_repo.get_after_for_user(db, carol.user_id, after_id=0) == []


def test_mark_read_never_moves_backwards(db, chat):
    bob, group = chat["bob"], chat["group"]
    message_repo.mark_read(db, group.group_id, bob.user_id, 10)
    message_repo.mark_read(db, group.group_id, bob.user_id, 5)  # a late, older "read"
    member = db.get(models.GroupMember, (group.group_id, bob.user_id))
    assert member.last_read_message_id == 10
