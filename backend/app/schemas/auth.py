import uuid

from pydantic import BaseModel, ConfigDict

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    """JWT access token plus opaque refresh token."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "session-id.secret",
                    "token_type": "bearer",
                    "expires_in": 900,
                }
            ]
        }
    )


class TokenLoginResponse(TokenRefreshResponse):
    user: UserResponse


class TokenData(BaseModel):
    """Application identity extracted from a validated JWT token."""

    user_id: uuid.UUID
    session_id: uuid.UUID

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "00000000-0000-0000-0000-000000000001",
                    "session_id": "00000000-0000-0000-0000-000000000002",
                }
            ]
        }
    )


class RefreshTokenData(BaseModel):
    """Parsed opaque refresh token data."""

    session_id: uuid.UUID
    secret: str
