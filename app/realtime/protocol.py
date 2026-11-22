"""
What the server does with each frame. Shared by BOTH application-layer protocols, so they behave
exactly the same and only the transport differs:
    protocol 1  routers/ws.py        (WebSocket: phone sends frames on the open socket)
    protocol 2  routers/stream.py    (SSE: server pushes) + POST /messages in routers/messages.py

The rule for "no message loss": the message is committed to the database BEFORE anyone is told
about it (ack to the sender, `message` to the other members). So a message is either saved, or
still in the sending phone's outbox to be resent. Never neither.

Owner: Yehia
"""
import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import JWTtoken, models
from app.database import SessionLocal
from app.repository import group as group_repo
from app.repository import message as message_repo
from app.repository import user as user_repo
from app.schemas.message import MessageOut
from app.schemas.ws import (
    AckFrame, ErrorFrame, MessageFrame, PingFrame, PongFrame,
    ReadFrame, SendFrame, SyncBatchFrame, SyncFrame,
)

from .manager import Connection, manager

log = logging.getLogger("chat.realtime")

# Most messages sent in one sync_batch. If a batch is full, has_more=True and the phone asks again.
SYNC_LIMIT = 500


class NotMemberError(Exception):
    """The user tried to send to / read a group they are not in."""


# ---------------------------------------------------------------------------
# Login check for /ws and /stream
# ---------------------------------------------------------------------------

def user_id_from_token(token: str) -> int | None:
    """Return the user_id inside a valid JWT, or None if the token is missing, broken or expired.

    Browsers cannot add an Authorization header to a WebSocket or an EventSource, so /ws and
    /stream get the token from ?token= and check it here instead of using get_current_user.
    """
    if not token:
        return None
    with SessionLocal() as db:
        try:
            user = JWTtoken.verify_access_token(token, HTTPException(status_code=401), db)
        except (HTTPException, ValueError):
            return None
        return user.user_id


def save_last_seen(user_id: int) -> None:
    """Store when the user went offline. A failure here is logged, never allowed to break the
    disconnect cleanup."""
    try:
        with SessionLocal() as db:
            user_repo.update_last_seen(db, user_id)
    except Exception:
        log.exception("Could not update last_seen for user %s", user_id)


# ---------------------------------------------------------------------------
# Sending a message (used by the WebSocket `send` frame AND by POST /messages)
# ---------------------------------------------------------------------------

def save_message(db: Session, sender_id: int, group_id: int, client_msg_id: str,
                 content: str) -> tuple[models.Message, bool]:
    """Check membership, then save (and commit) the message.

    Returns (message, created). created=False means the phone RESENT a message we already have
    (same sender + client_msg_id): we return the original instead of storing a copy.
    """
    if not group_repo.is_member(db, group_id, sender_id):
        raise NotMemberError()
    manager.count_message_in()
    return message_repo.create_message(db, sender_id, group_id, client_msg_id, content)


async def deliver_message(db: Session, message: models.Message) -> None:
    """Push a newly saved message to every online connection of every member, the sender's own
    devices included (each phone matches its own message by client_msg_id).
    Offline members get it later, when their phone connects and syncs."""
    frame = MessageFrame(message=MessageOut.model_validate(message))
    await manager.send_to_users(group_repo.member_ids(db, message.group_id), frame)


# ---------------------------------------------------------------------------
# Sync: catching up after being offline
# ---------------------------------------------------------------------------

async def send_sync(conn: Connection, after_id: int) -> tuple[int, bool]:
    """Send one sync_batch with the user's messages newer than after_id (in ALL their chats).

    Returns (last message_id sent, has_more). message_id only grows, so "everything after id N"
    is exact, unlike timestamps (phone clocks differ, two messages can share a millisecond).
    """
    with SessionLocal() as db:
        rows = message_repo.get_after_for_user(db, conn.user_id, after_id, limit=SYNC_LIMIT)
        messages = [MessageOut.model_validate(m) for m in rows]
    has_more = len(messages) == SYNC_LIMIT
    await manager.send_to_connection(conn, SyncBatchFrame(messages=messages, has_more=has_more))
    last_id = messages[-1].message_id if messages else after_id
    return last_id, has_more


# ---------------------------------------------------------------------------
# One incoming WebSocket frame
# ---------------------------------------------------------------------------

async def handle_frame(conn: Connection, frame: SendFrame | SyncFrame | ReadFrame | PingFrame) -> None:
    """Do what one (already validated) frame asks. Any problem becomes an `error` frame for this
    phone only: the socket stays open and no other phone is affected."""
    client_msg_id = frame.client_msg_id if isinstance(frame, SendFrame) else None
    try:
        match frame:
            case PingFrame():
                await manager.send_to_connection(conn, PongFrame())
            case SendFrame():
                await _handle_send(conn, frame)
            case SyncFrame():
                await send_sync(conn, frame.after_id)
            case ReadFrame():
                _handle_read(conn, frame)
    except NotMemberError:
        await manager.send_to_connection(conn, ErrorFrame(
            code="not_member", detail="You are not a member of this chat",
            client_msg_id=client_msg_id))
    except Exception:
        log.exception("Failed to handle a %s frame from user %s", frame.type, conn.user_id)
        await manager.send_to_connection(conn, ErrorFrame(
            code="server_error", detail="The server could not handle this frame",
            client_msg_id=client_msg_id))


async def _handle_send(conn: Connection, frame: SendFrame) -> None:
    with SessionLocal() as db:
        message, created = save_message(db, conn.user_id, frame.group_id,
                                        frame.client_msg_id, frame.content)
        # 1. Saved -> ack the sender first (the phone turns the message from "sending" to "sent").
        await manager.send_to_connection(conn, AckFrame(
            client_msg_id=message.client_msg_id,
            message_id=message.message_id,
            time_sent=message.time_sent,
        ))
        # 2. Then fan out. A resent duplicate was already delivered the first time, so skip it.
        if created:
            await deliver_message(db, message)


def _handle_read(conn: Connection, frame: ReadFrame) -> None:
    with SessionLocal() as db:
        if not group_repo.is_member(db, frame.group_id, conn.user_id):
            raise NotMemberError()
        message_repo.mark_read(db, frame.group_id, conn.user_id, frame.message_id)
