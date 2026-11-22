"""
Pydantic schemas: the shapes of data going in and out of the API.

One file per feature, so nobody edits the same file at the same time:
    user.py     Eyad    UserCreate, UserResponse, UserLogin
    group.py    Gelan   GroupCreate, GroupOut, GroupSummary, MemberOut   (to be added)
    message.py  Maryam  MessageCreate, MarkRead, MessageOut, SyncResponse
    ws.py       Yehia   WebSocket frames (protocol 1) and the SSE helper (protocol 2)

Import a module, then use its classes:
    from app.schemas import user
    user.UserCreate(...)
"""
from . import message, user, ws  # noqa: F401  (add `group` here once group.py exists)
