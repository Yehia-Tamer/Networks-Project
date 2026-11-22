"""
Database queries for chats (groups) and their members. No HTTP here.

A direct (1-to-1) chat is a group with is_direct=True and exactly 2 members, so every message
has one group_id and the same code handles both kinds of chat.

Owner: Gelan. These are STUBS from the Day 1 setup commit: the names and signatures are the team
contract (see the team guide), so keep them exactly as they are and replace each body.
is_member and member_ids are needed by /ws, so write them first.
"""
from sqlalchemy.orm import Session

from app import models


def is_member(db: Session, group_id: int, user_id: int) -> bool:
    raise NotImplementedError


def member_ids(db: Session, group_id: int) -> list[int]:
    """user_ids of everyone in the group (used to fan a new message out to their sockets)."""
    raise NotImplementedError


def create_group(db: Session, creator_id: int, name: str, description: str | None,
                 member_ids: list[int]) -> models.Group:
    """Create a group chat. The creator is always added as a member."""
    raise NotImplementedError


def get_or_create_direct(db: Session, user_a: int, user_b: int) -> models.Group:
    """Return the existing direct chat between the two users, or create it."""
    raise NotImplementedError


def add_member(db: Session, group_id: int, user_id: int) -> None:
    raise NotImplementedError


def remove_member(db: Session, group_id: int, user_id: int) -> None:
    raise NotImplementedError


def list_user_groups(db: Session, user_id: int) -> list[models.Group]:
    raise NotImplementedError
