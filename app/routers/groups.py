"""
Chat (group) endpoints. All need the Authorization: Bearer header; anything about one group
returns 403 if the user is not a member (put that check in a require_member dependency,
Maryam's routes reuse it).

Owner: Gelan. STUB from the Day 1 setup commit: already included in main.py, just add routes here.
To build (see the team guide's contract table):
    POST   /groups                       -> GroupOut
    POST   /groups/direct/{user_id}      -> GroupOut (existing chat if there is one)
    GET    /groups                       -> list of GroupSummary (last message, unread count)
    GET    /groups/{id}                  -> GroupOut with members
    POST   /groups/{id}/members          -> GroupOut
    DELETE /groups/{id}/members/{user_id} -> 204
"""
from fastapi import APIRouter

router = APIRouter(prefix="/groups", tags=["groups"])
