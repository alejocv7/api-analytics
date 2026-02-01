from fastapi.openapi.models import EmailStr
from pydantic import AwareDatetime, BaseModel, ConfigDict

from app.core.types import SecurePassword


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
    created_at: AwareDatetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "email": "user@example.com",
                    "full_name": "John Doe",
                    "is_active": True,
                    "created_at": "2026-01-20T15:30:00Z",
                }
            ]
        },
    )
