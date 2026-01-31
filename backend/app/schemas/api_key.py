from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


class APIKeyBase(BaseModel):
    """Base API key schema."""

    name: str = Field(max_length=255)


class APIKeyCreate(APIKeyBase):
    """Schema for creating an API key."""

    expires_at: datetime | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"name": "Production Key", "expires_at": None},
                {"name": "Temporary Testing Key", "expires_at": "2026-12-31T23:59:59Z"},
            ]
        }
    )


class APIKeyUpdate(BaseModel):
    """Schema for updating an API key."""

    name: str | None = Field(None, max_length=255)
    is_active: bool | None = None


class APIKeyResponse(APIKeyBase):
    """Schema for API key in responses (without the actual key)."""

    id: int
    project_id: int
    is_active: bool
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime | None
    total_requests: int

    model_config = ConfigDict(from_attributes=True)


class APIKeyCreateResponse(APIKeyResponse):
    """
    Response when creating a new API key.
    IMPORTANT: This is the ONLY time the full key is shown!
    """

    key: str  # Full API key - shown only once!
    warning: str = "Save this key securely! You won't be able to see it again."

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "key": "sk_live_abc123",
                    "name": "Production Key",
                    "project_id": 1,
                    "is_active": True,
                    "created_at": "2026-01-27T10:00:00Z",
                    "last_used_at": None,
                    "expires_at": None,
                    "total_requests": 0,
                    "warning": "Save this key securely! You won't be able to see it again.",
                }
            ]
        }
    )


class APIKeyListResponse(BaseModel):
    """Response for list of API keys."""

    items: list[APIKeyResponse]
    total: int

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"items": [], "total": 0}]}
    )
