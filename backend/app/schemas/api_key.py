import uuid

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
)

from app import models
from app.schemas.pagination import PaginatedResponse


class APIKeyBase(BaseModel):
    """Base API key schema."""

    name: str = Field(max_length=255)


class APIKeyCreate(APIKeyBase):
    """Schema for creating an API key."""

    expires_at: AwareDatetime | None = None

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

    id: uuid.UUID
    key_prefix: str
    project_id: uuid.UUID
    is_active: bool
    created_at: AwareDatetime
    last_used_at: AwareDatetime | None
    expires_at: AwareDatetime | None
    total_requests: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "name": "Production Key",
                    "key_prefix": "sk_live_abc123",
                    "project_id": 1,
                    "is_active": True,
                    "created_at": "2026-01-27T10:00:00Z",
                    "last_used_at": "2026-01-31T20:30:45Z",
                    "expires_at": None,
                    "total_requests": 1450,
                }
            ]
        },
    )


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
                    "warning": (
                        "Save this key securely! You won't be able to see it again."
                    ),
                }
            ]
        }
    )

    @classmethod
    def from_orm_and_key(cls, api_key: models.APIKey, key: str) -> APIKeyCreateResponse:
        """Create a response from an ORM model and a plain-text key."""
        base_data = APIKeyResponse.model_validate(api_key)
        return cls(**base_data.model_dump(), key=key)


APIKeyListResponse = PaginatedResponse[APIKeyResponse]
