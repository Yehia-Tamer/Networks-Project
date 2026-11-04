from app import JWTtoken, models, schemas, hashing
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import timedelta
from starlette import status
import os

def register_user(request: schemas.UserCreate, db: Session):
    existing_user = db.query(models.User).filter(
        (models.User.username == request.username) | (models.User.email == request.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or email already exists")

    new_user = models.User(
        username=request.username,
        email=request.email,
        hashed_password=hashing.Hash.bcrypt(request.password),
        display_name=request.display_name,
        last_seen_at=None
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Username or email already exists")
    db.refresh(new_user)
    return new_user

def login_user(request, db):
    user = (
        db.query(models.User).filter(models.User.username == request.username).first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    if not hashing.Hash.verify(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    access_token_expires = timedelta(
        minutes=int(os.getenv("ACCESS_TOKEN_EXPIRES_MINUTES"))
    )
    access_token = JWTtoken.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
