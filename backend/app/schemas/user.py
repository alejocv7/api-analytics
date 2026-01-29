from datetime import datetime

from fastapi.openapi.models import EmailStr
from pydantic import BaseModel, ConfigDict

from app.schemas import SecurePassword


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: SecurePassword
    full_name: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "[EMAIL_ADDRESS]",
                    "password": "[PASSWORD]",
                    "full_name": "John Doe",
                }
            ]
        }
    )


class UserResponse(BaseModel):
    """Schema for user data in responses."""

    email: str
    full_name: str | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
