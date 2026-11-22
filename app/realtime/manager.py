"""
ConnectionManager: keeps every open connection in memory, per user, and counts traffic.

One user can have several connections at once (two phones, or two browser tabs), so we keep
    user_id -> set of connections
A connection is either a WebSocket (protocol 1) or an SSE stream (protocol 2). Both have the same
`send(frame)` method, so the rest of the code never needs to know which protocol a phone is using.

Everything is in memory, so run uvicorn with ONE worker: a second worker would have its own
manager and would not know about phones connected to the first one.

Owner: Yehia
"""
import asyncio
import time
from collections import defaultdict

from fastapi import WebSocket

from app.schemas.ws import PresenceFrame, ServerFrame, sse_event


# ---------------------------------------------------------------------------
# The two kinds of connection
# ---------------------------------------------------------------------------

class WebSocketConnection:
    """Protocol 1: frames go out as JSON text on the open WebSocket."""
    protocol = "ws"

    def __init__(self, websocket: WebSocket, user_id: int):
        self.websocket = websocket
        self.user_id = user_id

    async def send(self, frame: ServerFrame) -> int:
        """Send one frame and return how many bytes went out."""
        text = frame.model_dump_json()
        await self.websocket.send_text(text)
        return len(text.encode())


class SSEConnection:
    """Protocol 2: frames are put in a queue; routers/stream.py takes them out and writes them
    to the open HTTP response as Server-Sent Events."""
    protocol = "sse"

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.queue: asyncio.Queue[str] = asyncio.Queue()

    async def send(self, frame: ServerFrame) -> int:
        text = sse_event(frame)
        self.queue.put_nowait(text)
        return len(text.encode())


Connection = WebSocketConnection | SSEConnection


# ---------------------------------------------------------------------------
# The manager
# ---------------------------------------------------------------------------

class ConnectionManager:
    def __init__(self):
        self.connections: dict[int, set[Connection]] = defaultdict(set)

        # Counters read by GET /metrics (Eyad). "in" = phone -> server, "out" = server -> phone.
        self.started_at = time.time()
        self.messages_in = 0      # chat messages received (WebSocket `send` or POST /messages)
        self.messages_out = 0     # chat messages delivered to a phone (one per receiving connection)
        self.frames_in = 0        # every WebSocket frame received
        self.frames_out = 0       # every frame / event sent
        self.bytes_in = 0
        self.bytes_out = 0

        # Background tasks we started (kept so Python does not garbage-collect them early).
        self._tasks: set[asyncio.Task] = set()

    # ----- connect / disconnect ------------------------------------------------

    def connect(self, conn: Connection) -> bool:
        """Register a connection. Returns True if this user just came online
        (it is their first open connection)."""
        first = len(self.connections[conn.user_id]) == 0
        self.connections[conn.user_id].add(conn)
        return first

    def disconnect(self, conn: Connection) -> bool:
        """Remove ONLY this one connection; every other phone keeps working.
        Returns True if this user just went offline (it was their last connection)."""
        conns = self.connections.get(conn.user_id)
        if not conns:
            return False
        conns.discard(conn)
        if conns:
            return False
        del self.connections[conn.user_id]
        return True

    def is_online(self, user_id: int) -> bool:
        return user_id in self.connections

    def online_user_ids(self) -> list[int]:
        return list(self.connections.keys())

    # ----- sending ---------------------------------------------------------------

    async def send_to_user(self, user_id: int, frame: ServerFrame) -> None:
        """Send a frame to every open connection of one user (all their phones / tabs)."""
        # list(...) copies the set, because a failed connection is removed while we loop.
        for conn in list(self.connections.get(user_id, ())):
            await self.send_to_connection(conn, frame)

    async def send_to_users(self, user_ids: list[int], frame: ServerFrame) -> None:
        """Send a frame to several users, e.g. every member of a group.
        Members who are offline are simply skipped: they get it later through sync."""
        for user_id in user_ids:
            await self.send_to_user(user_id, frame)

    async def send_to_connection(self, conn: Connection, frame: ServerFrame) -> None:
        """Send to one connection. If that socket is already dead, drop it instead of crashing,
        so one broken phone never stops the message from reaching the others."""
        try:
            sent = await conn.send(frame)
        except Exception:
            self.disconnect(conn)
            return
        self.frames_out += 1
        self.bytes_out += sent
        if frame.type == "message":
            self.messages_out += 1
        elif frame.type == "sync_batch":
            self.messages_out += len(frame.messages)

    async def broadcast_presence(self, user_id: int, online: bool) -> None:
        """Tell everyone who is connected that user_id came online / went offline (green dots).
        We tell all connected users: simple, and fine for a small team chat."""
        frame = PresenceFrame(user_id=user_id, online=online)
        for other_id in self.online_user_ids():
            if other_id != user_id:
                await self.send_to_user(other_id, frame)

    def run_in_background(self, coro) -> None:
        """Start a coroutine without waiting for it (used when an SSE stream closes, where we
        are no longer allowed to await)."""
        task = asyncio.get_running_loop().create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    # ----- counters --------------------------------------------------------------

    def count_frame_in(self, raw: str | bytes) -> None:
        self.frames_in += 1
        self.bytes_in += len(raw.encode() if isinstance(raw, str) else raw)

    def count_message_in(self) -> None:
        self.messages_in += 1

    def stats(self) -> dict:
        """Snapshot of the counters, for GET /metrics. Totals since the server started:
        to get "per second", compare two snapshots (or divide by uptime_seconds)."""
        all_conns = [c for conns in self.connections.values() for c in conns]
        return {
            "uptime_seconds": round(time.time() - self.started_at, 1),
            "online_users": len(self.connections),
            "active_connections": len(all_conns),
            "active_websocket": sum(c.protocol == "ws" for c in all_conns),
            "active_sse": sum(c.protocol == "sse" for c in all_conns),
            "messages_in": self.messages_in,
            "messages_out": self.messages_out,
            "frames_in": self.frames_in,
            "frames_out": self.frames_out,
            "bytes_in": self.bytes_in,
            "bytes_out": self.bytes_out,
        }


# The one shared instance. Import it everywhere:  from app.realtime.manager import manager
manager = ConnectionManager()
