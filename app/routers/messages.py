"""
Message endpoints: history, sending over HTTP (protocol 2) and reconnect sync.
All need the Authorization: Bearer header.

Owner: Maryam. STUB from the Day 1 setup commit: already included in main.py, just add routes here.
No prefix, because the paths start differently. To build (see the team guide's contract table):
    GET  /groups/{id}/messages?after_id= | ?before_id= &limit=50  -> list of MessageOut
    POST /messages                -> MessageOut: 201 if new, 200 if it already existed
    POST /groups/{id}/read        -> 204
    GET  /sync?after_id=          -> SyncResponse
"""
from fastapi import APIRouter

router = APIRouter(tags=["messages"])
