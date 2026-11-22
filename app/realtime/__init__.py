"""
Real-time layer, shared by both application-layer protocols:
    manager.py   who is connected right now (WebSocket and SSE) + the counters for /metrics
    protocol.py  what the server does with each frame: save, ack, fan out, sync, read

Owner: Yehia
"""
