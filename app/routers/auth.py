from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette import status

from app import database
from app.repository import auth
from app.schemas import user

router = APIRouter(tags=["authentication"], prefix="/auth")

@router.post('/register', status_code=status.HTTP_201_CREATED, response_model=user.UserResponse)
def register(request: user.UserCreate, db: Session = Depends(database.get_db)):
    return auth.register_user(request, db)

@router.post('/login', status_code=status.HTTP_201_CREATED)
def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    return auth.login_user(request, db)