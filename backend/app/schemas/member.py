import uuid
from datetime import datetime
from typing import Literal

from pydantic import AliasPath, BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import ProjectRole
from app.schemas.pagination import PaginatedResponse

AssignableRole = Literal[ProjectRole.member, ProjectRole.viewer]


class MemberAdd(BaseModel):
    """Schema for adding a member to a project."""

    email: EmailStr
    role: AssignableRole = ProjectRole.viewer

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "email": "user@example.com",
                    "role": "viewer",
                }
            ]
        }
    )


class MemberUpdate(BaseModel):
    """Schema for updating a member's role."""

    role: AssignableRole

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "role": "member",
                }
            ]
        }
    )


class MemberResponse(BaseModel):
    """Schema for a project member in responses."""

    user_id: uuid.UUID
    project_id: uuid.UUID
    role: ProjectRole
    email: str = Field(validation_alias=AliasPath("user", "email"))
    full_name: str | None = Field(validation_alias=AliasPath("user", "full_name"))
    joined_at: datetime = Field(validation_alias="created_at")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


MemberListResponse = PaginatedResponse[MemberResponse]
