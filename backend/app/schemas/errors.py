from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Schema for consistent error responses."""

    error: str = Field(..., description="A short, human-readable error message")
    details: dict[str, Any] | list[dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional error context (e.g., validation errors)",
    )
    request_id: str | None = Field(
        None, description="Correlation ID for troubleshooting"
    )
