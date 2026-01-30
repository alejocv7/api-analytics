from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.core.config import settings


class ProjectBase(BaseModel):
    """Base project schema."""

    name: str = Field(
        ..., min_length=1, max_length=100, pattern=settings.PROJECT_NAME_PATTERN
    )
    description: str | None = Field(None, max_length=1000)

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Production API",
                    "description": "Main production API for e-commerce platform",
                }
            ]
        }
    )


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: str | None = Field(
        None, min_length=1, max_length=100, pattern=settings.PROJECT_NAME_PATTERN
    )
    is_active: bool | None = None

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "name": "Updated Project Name",
                    "description": "Updated description",
                    "is_active": True,
                }
            ]
        },
    )


class ProjectResponse(ProjectBase):
    """Schema for project in responses."""

    id: int
    project_key: str
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailResponse(ProjectResponse):
    """Detailed project response with statistics."""

    total_api_keys: int = 0
    active_api_keys: int = 0
    total_metrics: int = 0
    metrics_last_24h: int = 0
    avg_response_time_ms: float = 0.0
    error_rate_percent: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    """Response for list of projects."""

    items: list[ProjectResponse]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"items": [], "total": 0, "page": 1, "page_size": 20}]
        }
    )
