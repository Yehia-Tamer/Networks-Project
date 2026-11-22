"""
Database queries for messages. No HTTP here.

Owner: Maryam. These are STUBS from the Day 1 setup commit: the names and signatures are the team
contract (see the team guide), so keep them exactly as they are and replace each body.
create_message and get_after_for_user are needed by /ws, so write them first.
"""
from sqlalchemy.orm import Session

from app import models


def create_message(db: Session, sender_id: int, group_id: int, client_msg_id: str,
                   content: str) -> tuple[models.Message, bool]:
    """Save a message and commit. Idempotent: no duplicates.

    Returns (message, True) if it was newly created, or (existing message, False) if this
    sender already sent this client_msg_id (the unique key uq_messages_sender_client_msg).
    """
    raise NotImplementedError


def get_after_for_user(db: Session, user_id: int, after_id: int,
                       limit: int = 500) -> list[models.Message]:
    """Messages in ANY of the user's groups with message_id > after_id, oldest first (reconnect sync)."""
    raise NotImplementedError


def get_after(db: Session, group_id: int, after_id: int, limit: int = 50) -> list[models.Message]:
    """Messages in one group newer than after_id, oldest first."""
    raise NotImplementedError


def get_before(db: Session, group_id: int, before_id: int, limit: int = 50) -> list[models.Message]:
    """Messages in one group older than before_id (load older on scroll up), returned oldest first."""
    raise NotImplementedError


def mark_read(db: Session, group_id: int, user_id: int, message_id: int) -> None:
    """Set group_members.last_read_message_id (never move it backwards)."""
    raise NotImplementedError
