"""
Message endpoints: history, sending over HTTP (protocol 2), mark read and reconnect sync.
All need the Authorization: Bearer header. Anything about one group returns 403 if the user is
not a member.

    GET  /groups/{id}/messages?after_id= | ?before_id= &limit=50  -> list of MessageOut
    POST /messages                -> MessageOut: 201 if new, 200 if it already existed
    POST /groups/{id}/read        -> 204
    GET  /sync?after_id=          -> SyncResponse

Owner: Maryam
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app import database, models
from app.oauth2 import get_current_user
from app.realtime import protocol
from app.repository import group as group_repo
from app.repository import message as message_repo
from app.schemas.message import MarkRead, MessageCreate, MessageOut, SyncResponse

router = APIRouter(tags=["messages"])

SYNC_LIMIT = 500


def _require_member(db: Session, group_id: int, user_id: int) -> None:
    # TODO: switch to Gelan's require_member dependency once routers/groups.py has it.
    if not group_repo.is_member(db, group_id, user_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not a member of this chat")


@router.get("/groups/{group_id}/messages", response_model=list[MessageOut])
def get_history(
    group_id: int,
    after_id: int | None = Query(None, ge=0, description="Messages newer than this id"),
    before_id: int | None = Query(None, gt=0, description="Messages older than this id (scroll up)"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(database.get_db),
    user: models.User = Depends(get_current_user),
):
    """Chat history, oldest first. No ids = the first `limit` messages of the chat.
    Use before_id with the oldest id on screen to load older messages."""
    _require_member(db, group_id, user.user_id)
    if after_id is not None and before_id is not None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Use after_id or before_id, not both")
    if before_id is not None:
        return message_repo.get_before(db, group_id, before_id, limit)
    return message_repo.get_after(db, group_id, after_id or 0, limit)


@router.post("/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    request: MessageCreate,
    response: Response,
    db: Session = Depends(database.get_db),
    user: models.User = Depends(get_current_user),
):
    """Send a message over HTTP (protocol 2). The response is the ack: it only comes back after
    the message is committed. Sending the same client_msg_id again returns the original message
    with 200 instead of storing a copy, so the phone can safely retry."""
    try:
        message, created = protocol.save_message(
            db, user.user_id, request.group_id, request.client_msg_id, request.content)
    except protocol.NotMemberError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You are not a member of this chat")

    if created:
        # Same fan-out as a WebSocket send: online members get it on /ws or /stream right away.
        await protocol.deliver_message(db, message)
    else:
        response.status_code = status.HTTP_200_OK
    return message


@router.post("/groups/{group_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def mark_read(
    group_id: int,
    request: MarkRead,
    db: Session = Depends(database.get_db),
    user: models.User = Depends(get_current_user),
):
    """"I have read up to this message" (used for unread counts)."""
    _require_member(db, group_id, user.user_id)
    message_repo.mark_read(db, group_id, user.user_id, request.message_id)


@router.get("/sync", response_model=SyncResponse)
def sync(
    after_id: int = Query(0, ge=0),
    db: Session = Depends(database.get_db),
    user: models.User = Depends(get_current_user),
):
    """Every message in all my chats newer than after_id (0 on a new device).
    If has_more is true, call again with after_id = the last message_id received."""
    rows = message_repo.get_after_for_user(db, user.user_id, after_id, SYNC_LIMIT)
    return SyncResponse(
        messages=[MessageOut.model_validate(m) for m in rows],
        has_more=len(rows) == SYNC_LIMIT,
    )
