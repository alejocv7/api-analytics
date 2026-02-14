from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Schema for health check response."""

    status: str = Field(..., description="Overall service status")
    components: dict[str, str] = Field(
        ..., description="Status of individual components"
    )
    environment: str = Field(..., description="Current environment")
    version: str = Field(..., description="API version")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(timespec="seconds"),
        description="Current server time",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "status": "online",
                    "components": {"database": "healthy"},
                    "environment": "local",
                    "version": "0.1.0",
                    "timestamp": "2026-02-11T10:00:00Z",
                }
            ]
        }
    )
