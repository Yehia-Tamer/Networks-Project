"""
Database queries for messages. No HTTP here: routers decide the status codes.

Ordering and sync always use message_id, never time_sent: message_id only grows, so
"everything after id 120" is exact, while phone clocks differ and two messages can share a
millisecond.

Owner: Maryam
"""
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models


def _find(db: Session, sender_id: int, client_msg_id: str) -> models.Message | None:
    """The message this sender already stored under this client_msg_id, if any."""
    return db.scalar(
        select(models.Message).where(
            models.Message.sender_id == sender_id,
            models.Message.client_msg_id == client_msg_id,
        )
    )


def create_message(db: Session, sender_id: int, group_id: int, client_msg_id: str,
                   content: str) -> tuple[models.Message, bool]:
    """Save a message and commit. Idempotent: no duplicates.

    Returns (message, True) if it was newly created, or (existing message, False) if this
    sender already sent this client_msg_id. That happens when the phone resends a message whose
    ack was lost (e.g. Wi-Fi dropped right after sending).

    Two layers of protection:
      1. look for an existing row first (the normal resend case)
      2. the unique key uq_messages_sender_client_msg on (sender_id, client_msg_id): if two copies
         arrive at the same moment, the database refuses the second insert and we return the first
    """
    existing = _find(db, sender_id, client_msg_id)
    if existing is not None:
        return existing, False

    message = models.Message(
        sender_id=sender_id,
        group_id=group_id,
        client_msg_id=client_msg_id,
        content=content,
    )
    db.add(message)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = _find(db, sender_id, client_msg_id)
        if existing is None:
            raise  # a different constraint failed (e.g. group does not exist)
        return existing, False

    db.refresh(message)  # load message_id and time_sent, which the database filled in
    return message, True


def get_after_for_user(db: Session, user_id: int, after_id: int,
                       limit: int = 500) -> list[models.Message]:
    """Messages in ANY of the user's groups with message_id > after_id, oldest first.
    Used for the reconnect sync (WebSocket `sync`, SSE catch-up and GET /sync)."""
    return list(db.scalars(
        select(models.Message)
        .join(models.GroupMember, models.GroupMember.group_id == models.Message.group_id)
        .where(models.GroupMember.user_id == user_id, models.Message.message_id > after_id)
        .order_by(models.Message.message_id)
        .limit(limit)
    ))


def get_after(db: Session, group_id: int, after_id: int, limit: int = 50) -> list[models.Message]:
    """Messages in one group newer than after_id, oldest first."""
    return list(db.scalars(
        select(models.Message)
        .where(models.Message.group_id == group_id, models.Message.message_id > after_id)
        .order_by(models.Message.message_id)
        .limit(limit)
    ))


def get_before(db: Session, group_id: int, before_id: int, limit: int = 50) -> list[models.Message]:
    """The `limit` messages just before before_id (load older on scroll up), returned oldest first."""
    newest_first = db.scalars(
        select(models.Message)
        .where(models.Message.group_id == group_id, models.Message.message_id < before_id)
        .order_by(models.Message.message_id.desc())
        .limit(limit)
    )
    return list(reversed(list(newest_first)))


def mark_read(db: Session, group_id: int, user_id: int, message_id: int) -> None:
    """Set group_members.last_read_message_id. Never moves backwards, so a late "read" from an
    older screen cannot bring unread messages back."""
    member = db.get(models.GroupMember, (group_id, user_id))
    if member is None:
        return
    if member.last_read_message_id is None or message_id > member.last_read_message_id:
        member.last_read_message_id = message_id
        db.commit()
