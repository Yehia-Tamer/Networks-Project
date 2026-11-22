"""
Real-time server metrics for monitoring and debugging.

Owner: Eyad. STUB from the Day 1 setup commit: already included in main.py, just add the route here.
To build:
    GET /metrics -> active connections, messages per second, bytes per second, uptime
                    (read from the ConnectionManager's counters in app/realtime/manager.py)
"""
from fastapi import APIRouter

router = APIRouter(tags=["metrics"])
