"""
GET /metrics: live numbers read from the ConnectionManager (app/realtime/manager.py).

Owner: Eyad.
manager.stats() gives running totals since the server started. To turn totals into
"per second", we keep the last few snapshots and compare the newest one with one
about WINDOW seconds older.
"""
import time
from collections import deque

from fastapi import APIRouter, Depends

from app.oauth2 import get_current_user
from app.realtime.manager import manager

router = APIRouter(tags=["metrics"])

WINDOW = 5.0                          # seconds used for the rates
_samples: deque = deque(maxlen=60)    # (time, messages in+out, bytes in+out)


@router.get("/metrics")
def metrics(current_user=Depends(get_current_user)):
    now = time.time()
    stats = manager.stats()
    msgs = stats["messages_in"] + stats["messages_out"]
    nbytes = stats["bytes_in"] + stats["bytes_out"]
    _samples.append((now, msgs, nbytes))

    # The oldest sample that is still inside the window is the base for the rates.
    base = next((s for s in _samples if now - s[0] <= WINDOW), _samples[-1])
    dt = now - base[0]
    msgs_per_s = (msgs - base[1]) / dt if dt > 0.5 else 0.0
    bytes_per_s = (nbytes - base[2]) / dt if dt > 0.5 else 0.0

    return {
        **stats,  # uptime, online users, active connections (ws / sse), message/frame/byte totals
        "uptime_seconds": int(stats["uptime_seconds"]),
        "messages_per_second": round(msgs_per_s, 2),
        "bytes_per_second": round(bytes_per_s, 1),
    }
