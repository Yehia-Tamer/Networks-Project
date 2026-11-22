"""
User endpoints. All need the Authorization: Bearer header.

Owner: Eyad. STUB from the Day 1 setup commit: already included in main.py, just add routes here.
To build (see the team guide's contract table):
    GET /users/me        -> UserResponse
    GET /users?search=   -> list of UserResponse
    GET /users/{id}      -> UserResponse
"""
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])
