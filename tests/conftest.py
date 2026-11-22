"""
Shared test setup. Tests never touch your real PostgreSQL: each test gets a fresh, empty
SQLite database in memory.
"""
import os

# Must be set BEFORE importing app.*, because app/database.py creates its engine on import.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ.setdefault("JWT_SECRET", "test-secret-" + "x" * 52)
os.environ.setdefault("ACCESS_TOKEN_EXPIRES_MINUTES", "60")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base


@pytest.fixture
def db():
    """A database session on a brand-new in-memory database with the 4 tables."""
    engine = create_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def chat(db):
    """Two users (alice, bob) in one group chat, plus a third user (carol) who is NOT in it."""
    alice = models.User(username="alice", email="alice@example.com", hashed_password="x")
    bob = models.User(username="bob", email="bob@example.com", hashed_password="x")
    carol = models.User(username="carol", email="carol@example.com", hashed_password="x")
    db.add_all([alice, bob, carol])
    db.flush()
    group = models.Group(name="Team", created_by=alice.user_id)
    db.add(group)
    db.flush()
    db.add_all([
        models.GroupMember(group_id=group.group_id, user_id=alice.user_id),
        models.GroupMember(group_id=group.group_id, user_id=bob.user_id),
    ])
    db.commit()
    return {"alice": alice, "bob": bob, "carol": carol, "group": group}
