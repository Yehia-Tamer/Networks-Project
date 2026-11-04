from fastapi import FastAPI, Depends

from app.database import Base, engine, get_db
import app.models
from app.routers import auth

api=FastAPI(title="Real Time Chat API")

Base.metadata.create_all(bind=engine)

@api.get('/',status_code=200)
def root():
    return {"message": "Hello World"}

api.include_router(auth.router)