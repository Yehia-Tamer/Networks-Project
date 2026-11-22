"""
Message schemas (Pydantic) — the shapes of messages going in and out of the API.

Used by:
  - routers/messages.py   (REST: POST /messages, history, /sync)
  - schemas/ws.py         (the WebSocket frames reuse MessageOut and the field types below)

Owner: Maryam
"""
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

# ---------------------------------------------------------------------------
# Reusable field types
# ---------------------------------------------------------------------------

# Longest message we accept. Leaves room for encrypted (base64) text, which is
# longer than the plain text it hides.
MAX_CONTENT_LENGTH = 8000


def _check_uuid(value: str) -> str:
    """client_msg_id must be a real UUID (e.g. from the `uuid` npm package)."""
    UUID(value)  # raises ValueError -> Pydantic turns it into a 422 / error frame
    return value.lower()  # one spelling, so the duplicate check always matches


# The id the PHONE generates for each message. Same id twice = same message.
# 36 characters = the standard UUID text form, which fits messages.client_msg_id (String(36)).
ClientMsgId = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=36, max_length=36),
    AfterValidator(_check_uuid),
]

# Message text (or ciphertext if end-to-end encryption is on). Never empty.
MessageContent = Annotated[str, StringConstraints(min_length=1, max_length=MAX_CONTENT_LENGTH)]

# Database ids are always positive.
Id = Annotated[int, Field(gt=0)]


# ---------------------------------------------------------------------------
# Requests (phone -> server)
# ---------------------------------------------------------------------------

class MessageCreate(BaseModel):
    """Body of POST /messages (protocol 2). The WebSocket `send` frame carries the same fields."""
    model_config = ConfigDict(extra="forbid")

    group_id: Id
    client_msg_id: ClientMsgId
    content: MessageContent
    # When the phone pressed "send" (used to measure latency). Optional.
    sent_at: datetime | None = None


class MarkRead(BaseModel):
    """Body of POST /groups/{id}/read: "I have read up to this message"."""
    model_config = ConfigDict(extra="forbid")

    message_id: Id


# ---------------------------------------------------------------------------
# Responses (server -> phone)
# ---------------------------------------------------------------------------

class MessageOut(BaseModel):
    """One stored message, exactly as phones receive it (REST, WebSocket and SSE)."""
    model_config = ConfigDict(from_attributes=True)  # can be built from a models.Message row

    message_id: int
    group_id: int
    sender_id: int
    client_msg_id: str
    content: str
    time_sent: datetime


class SyncResponse(BaseModel):
    """GET /sync result, and the body of the WebSocket `sync_batch` frame.

    has_more=True means the limit was reached: ask again with
    after_id = the last message_id in this batch.
    """
    messages: list[MessageOut]
    has_more: bool