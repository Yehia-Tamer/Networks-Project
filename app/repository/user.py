"""
Database queries for users. No HTTP here: return None / objects and let the router pick the status code.

Owner: Eyad.
"""
from datetime import datetime, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import models


def get_by_id(db: Session, user_id: int) -> models.User | None:
    return db.query(models.User).filter(models.User.user_id == user_id).first()


def get_by_username(db: Session, username: str) -> models.User | None:
    return db.query(models.User).filter(models.User.username == username).first()


def search_users(db: Session, text: str, limit: int = 20) -> list[models.User]:
    """Users whose username or display_name contains `text` (case-insensitive)."""
    q = db.query(models.User)
    if text:
        like = f"%{text}%"
        q = q.filter(or_(models.User.username.ilike(like), models.User.display_name.ilike(like)))
    return q.order_by(models.User.username).limit(limit).all()


def update_last_seen(db: Session, user_id: int) -> None:
    """Set users.last_seen_at to now. Called by /ws when a user's last socket closes."""
    user = get_by_id(db, user_id)
    if user is not None:
        user.last_seen_at = datetime.now(timezone.utc)
        db.commit()
