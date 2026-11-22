"""
Protocol 1: the WebSocket endpoint  ws://<laptop-ip>:8000/ws?token=<jwt>

Owner: Yehia. STUB from the Day 1 setup commit: already included in main.py.
Frames are defined in app/schemas/ws.py; live sockets are kept in app/realtime/manager.py.
"""
from fastapi import APIRouter

router = APIRouter(tags=["realtime"])
