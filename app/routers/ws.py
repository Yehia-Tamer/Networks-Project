"""
Protocol 1: the WebSocket endpoint   ws://<laptop-ip>:8000/ws?token=<jwt>

One TCP connection stays open, and both sides can send a frame at any time. Every frame is one
JSON object with a "type" (defined in app/schemas/ws.py):
    phone -> server : send, sync, read, ping
    server -> phone : ack, message, sync_batch, presence, error, pong

Lifetime of one connection:
    1. check the token (before accepting the socket)
    2. register the socket in the ConnectionManager, tell the others "user X is online"
    3. loop: read a frame, validate it, handle it (app/realtime/protocol.py)
    4. when the phone disconnects: remove ONLY this socket, save last_seen, tell the others

The phone sends `sync` right after connecting, so it catches up on everything it missed.

Owner: Yehia
"""
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from pydantic import ValidationError

from app.realtime import protocol
from app.realtime.manager import WebSocketConnection, manager
from app.schemas.ws import ErrorFrame, parse_client_frame

router = APIRouter(tags=["realtime"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query("")):
    # 1. Login check. Closing before accept() rejects the handshake, so a phone without a valid
    #    token never gets a connection. 1008 = "policy violation".
    user_id = protocol.user_id_from_token(token)
    if user_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    conn = WebSocketConnection(websocket, user_id)

    # 2. Register. Only announce "online" for the user's first connection.
    if manager.connect(conn):
        await manager.broadcast_presence(user_id, online=True)

    try:
        # 3. Read frames until the phone disconnects.
        while True:
            raw = await websocket.receive_text()
            manager.count_frame_in(raw)
            try:
                frame = parse_client_frame(raw)
            except ValidationError as e:
                # Bad frame: tell this phone what was wrong, keep the connection open.
                await manager.send_to_connection(conn, ErrorFrame(
                    code="invalid_frame", detail=str(e.errors(include_url=False)[:3])))
                continue
            await protocol.handle_frame(conn, frame)
    except WebSocketDisconnect:
        pass  # normal: phone closed the app, lost Wi-Fi, locked the screen...
    finally:
        # 4. Remove only this socket; every other phone keeps its connection.
        if manager.disconnect(conn):
            protocol.save_last_seen(user_id)
            await manager.broadcast_presence(user_id, online=False)
