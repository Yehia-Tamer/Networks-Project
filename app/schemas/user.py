import re
from datetime import datetime

from pydantic import BaseModel, field_validator, ConfigDict, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    display_name: str | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if len(value) < 8:
            raise ValueError("Must be at least 8 characters")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Must contain an uppercase letter")
        if not re.search(r"[a-z]", value):
            raise ValueError("Must contain a lowercase letter")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            raise ValueError("Must contain a special character")
        return value


class UserResponse(BaseModel):
    """Public shape of a user (used by /auth/register and every /users route).
    The password hash is deliberately NOT listed, so FastAPI never sends it."""
    user_id: int
    username: str
    email: EmailStr
    display_name: str | None = None
    created_at: datetime
    last_seen_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    display_name: str | None = None
    email: EmailStr | None = None
