from pydantic import BaseModel, ConfigDict


class TokenResponse(BaseModel):
    """JWT access + refresh token pair."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                }
            ]
        }
    )


class RefreshTokenRequest(BaseModel):
    """Request body for the token refresh endpoint."""

    refresh_token: str


class TokenData(BaseModel):
    """Application identity extracted from a validated JWT token."""

    user_id: int

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": 1,
                }
            ]
        }
    )


class RefreshTokenData(BaseModel):
    """Claims extracted from a validated refresh token."""

    user_id: int
    token_version: int
