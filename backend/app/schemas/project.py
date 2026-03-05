import uuid

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
)

from app.core.config import settings
from app.schemas.pagination import PaginatedResponse


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
    description: str | None = Field(None, max_length=1000)
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

    id: uuid.UUID
    project_key: str
    user_id: uuid.UUID
    is_active: bool
    member_count: int
    api_key_count: int
    created_at: AwareDatetime
    updated_at: AwareDatetime | None

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "name": "Production API",
                    "description": "Main production API",
                    "project_key": "production-api-a1b2",
                    "user_id": 1,
                    "is_active": True,
                    "member_count": 3,
                    "api_key_count": 2,
                    "created_at": "2026-01-01T12:00:00Z",
                    "updated_at": "2026-01-01T12:00:00Z",
                }
            ]
        },
    )


ProjectListResponse = PaginatedResponse[ProjectResponse]
