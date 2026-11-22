"""
Protocol 2: Server-Sent Events   GET /stream?token=<jwt>&after_id=<last id the phone has>

The phone opens ONE long HTTP response and the server keeps writing events into it. It is
one-way (server -> phone), so the phone SENDS with a normal request: POST /messages
(routers/messages.py), and the HTTP response to that POST is the "ack".

Each event carries exactly the same JSON as a WebSocket frame (app/schemas/ws.py, sse_event):
    event: message
    data: {"type": "message", "message": {...}}

Compared with protocol 1: same JSON, different transport. The WebSocket reuses one open
connection in both directions; here every send is a new HTTP request. That difference is what
we measure in the report.

On the phone:  const es = new EventSource(`${API}/stream?token=...&after_id=...`)
Listen with es.addEventListener("message" | "sync_batch" | "presence" | ..., handler).

Owner: Yehia
"""
import asyncio

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from app.realtime import protocol
from app.realtime.manager import SSEConnection, manager

router = APIRouter(tags=["realtime"])

# Send a comment line this often when nothing happens, so Wi-Fi routers and the browser do not
# close the "idle" connection, and so we notice quickly when the phone is gone.
KEEPALIVE_SECONDS = 15


@router.get("/stream")
async def stream(request: Request, token: str = Query(""), after_id: int = Query(0, ge=0)):
    user_id = protocol.user_id_from_token(token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    conn = SSEConnection(user_id)

    async def events():
        if manager.connect(conn):
            await manager.broadcast_presence(user_id, online=True)
        try:
            # Catch up first. The phone cannot send a `sync` frame on a one-way stream, so it
            # passes ?after_id= and we keep sending batches until it has everything.
            last_id, has_more = await protocol.send_sync(conn, after_id)
            while has_more:
                last_id, has_more = await protocol.send_sync(conn, last_id)

            # Then stay live: write every event the manager puts in this connection's queue.
            while not await request.is_disconnected():
                try:
                    yield await asyncio.wait_for(conn.queue.get(), timeout=KEEPALIVE_SECONDS)
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"  # lines starting with ":" are ignored by EventSource
        finally:
            # The phone is gone. We may not await here (the response is being cancelled),
            # so do the database update now and send "offline" in the background.
            if manager.disconnect(conn):
                protocol.save_last_seen(user_id)
                manager.run_in_background(manager.broadcast_presence(user_id, online=False))

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
