from fastapi.openapi.models import EmailStr
from pydantic import BaseModel, ConfigDict


class TokenResponse(BaseModel):
    """JWT token."""

    access_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                }
            ]
        }
    )


class TokenData(BaseModel):
    """Data stored in JWT token."""

    user_id: int
    email: str
    exp: int | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": 1,
                    "email": "[EMAIL_ADDRESS]",
                    "exp": 1738198800,
                }
            ]
        }
    )


class LoginRequest(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "[EMAIL_ADDRESS]",
                    "password": "[PASSWORD]",
                }
            ]
        }
    )
