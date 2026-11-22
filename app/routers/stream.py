"""
Protocol 2: Server-Sent Events  GET /stream?token=<jwt>
The phone receives on this stream and sends with POST /messages (routers/messages.py).

Owner: Yehia. STUB from the Day 1 setup commit: already included in main.py.
Events are formatted with sse_event() from app/schemas/ws.py.
"""
from fastapi import APIRouter

router = APIRouter(tags=["realtime"])
