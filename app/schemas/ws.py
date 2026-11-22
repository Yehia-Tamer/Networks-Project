"""
WebSocket protocol (protocol 1) — every frame is one JSON object with a "type".

Phone -> server : send, sync, read, ping
Server -> phone : ack, message, sync_batch, presence, error, pong

SSE (protocol 2) sends the same server -> phone frames as events; see sse_event().

How to use in routers/ws.py:

    raw = await websocket.receive_text()
    try:
        frame = parse_client_frame(raw)
    except ValidationError as e:
        await websocket.send_text(ErrorFrame(code="invalid_frame", detail=str(e)).model_dump_json())
        continue

    match frame:
        case SendFrame():  ...
        case SyncFrame():  ...
        case ReadFrame():  ...
        case PingFrame():  await websocket.send_text(PongFrame().model_dump_json())

Owner: Yehia
"""
from datetime import datetime
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from .message import ClientMsgId, Id, MessageContent, MessageOut


# ---------------------------------------------------------------------------
# Phone -> server
# ---------------------------------------------------------------------------

class ClientFrame(BaseModel):
    # Reject unknown fields, so a typo like "groupId" fails loudly instead of being ignored.
    model_config = ConfigDict(extra="forbid")


class SendFrame(ClientFrame):
    """A new message. The server answers with `ack` once it is saved."""
    type: Literal["send"]
    client_msg_id: ClientMsgId
    group_id: Id
    content: MessageContent
    sent_at: datetime | None = None  # phone's clock when "send" was pressed (latency metric)


class SyncFrame(ClientFrame):
    """Send me every message newer than after_id (0 = everything, e.g. on a new device)."""
    type: Literal["sync"]
    after_id: Annotated[int, Field(ge=0)] = 0


class ReadFrame(ClientFrame):
    """I have read up to message_id in this group."""
    type: Literal["read"]
    group_id: Id
    message_id: Id


class PingFrame(ClientFrame):
    """Keep-alive. The server answers with `pong`."""
    type: Literal["ping"]


# Pydantic picks the right class by looking at "type" first.
AnyClientFrame = Annotated[
    Union[SendFrame, SyncFrame, ReadFrame, PingFrame],
    Field(discriminator="type"),
]
_client_frame_adapter = TypeAdapter(AnyClientFrame)


def parse_client_frame(raw: str | bytes) -> SendFrame | SyncFrame | ReadFrame | PingFrame:
    """Turn the raw JSON text from the socket into a frame object.

    Raises pydantic.ValidationError if the JSON is broken, "type" is unknown,
    or a field is missing / wrong.
    """
    return _client_frame_adapter.validate_json(raw)


# ---------------------------------------------------------------------------
# Server -> phone
# (each has its "type" filled in already, so you only pass the other fields)
# ---------------------------------------------------------------------------

class AckFrame(BaseModel):
    """Your message is saved. The phone matches it by client_msg_id and marks it "sent"."""
    type: Literal["ack"] = "ack"
    client_msg_id: str
    message_id: int
    time_sent: datetime


class MessageFrame(BaseModel):
    """A new message in one of your chats."""
    type: Literal["message"] = "message"
    message: MessageOut


class SyncBatchFrame(BaseModel):
    """Catch-up after (re)connecting. If has_more, send `sync` again with the last id."""
    type: Literal["sync_batch"] = "sync_batch"
    messages: list[MessageOut]
    has_more: bool


class PresenceFrame(BaseModel):
    """Someone came online or went offline."""
    type: Literal["presence"] = "presence"
    user_id: int
    online: bool


ErrorCode = Literal[
    "invalid_frame",   # broken JSON, unknown type, missing or wrong field
    "not_member",      # tried to send to / read a group you are not in
    "server_error",    # something failed on our side (e.g. database down)
]


class ErrorFrame(BaseModel):
    """Something was rejected. client_msg_id is set when it was a `send`."""
    type: Literal["error"] = "error"
    code: ErrorCode
    detail: str
    client_msg_id: str | None = None


class PongFrame(BaseModel):
    type: Literal["pong"] = "pong"


ServerFrame = AckFrame | MessageFrame | SyncBatchFrame | PresenceFrame | ErrorFrame | PongFrame


# ---------------------------------------------------------------------------
# Protocol 2 (SSE) helper
# ---------------------------------------------------------------------------

def sse_event(frame: ServerFrame) -> str:
    """Format a server frame as one Server-Sent Event, ready to yield from a StreamingResponse.

        event: message
        data: {"type": "message", "message": {...}}
        <blank line>
    """
    return f"event: {frame.type}\ndata: {frame.model_dump_json()}\n\n"