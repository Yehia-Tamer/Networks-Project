"""
Database queries for users. No HTTP here: return None / objects and let the router pick the status code.

Owner: Eyad. These are STUBS from the Day 1 setup commit: the names and signatures are the team
contract (see the team guide), so keep them exactly as they are and replace each body.
update_last_seen is needed by /ws, so write it first.
"""
from sqlalchemy.orm import Session

from app import models


def get_by_id(db: Session, user_id: int) -> models.User | None:
    raise NotImplementedError


def get_by_username(db: Session, username: str) -> models.User | None:
    raise NotImplementedError


def search_users(db: Session, text: str, limit: int = 20) -> list[models.User]:
    """Users whose username or display_name contains `text` (case-insensitive)."""
    raise NotImplementedError


def update_last_seen(db: Session, user_id: int) -> None:
    """Set users.last_seen_at to now. Called by /ws when a user's last socket closes."""
    raise NotImplementedError
