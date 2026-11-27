"""
User endpoints. All need the Authorization: Bearer header.

Owner: Eyad.
    GET /users/me        -> UserResponse
    GET /users?search=   -> list of UserResponse
    GET /users/{id}      -> UserResponse
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.oauth2 import get_current_user
from app.repository import user as user_repo
from app.schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def read_me(current_user=Depends(get_current_user)):
    return current_user


@router.get("", response_model=list[UserResponse])
def search(search: str = Query("", max_length=50),
           db: Session = Depends(get_db),
           current_user=Depends(get_current_user)):
    return user_repo.search_users(db, search)


# /me is declared first so it is not captured by /{user_id}
@router.get("/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db),
              current_user=Depends(get_current_user)):
    user = user_repo.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
