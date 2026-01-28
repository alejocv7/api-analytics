from datetime import datetime

from fastapi.openapi.models import EmailStr
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = None


class UserResponse(BaseModel):
    """Schema for user data in responses."""

    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
