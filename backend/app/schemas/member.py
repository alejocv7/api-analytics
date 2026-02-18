from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.models.user_project import ProjectRole

AssignableRole = Literal[ProjectRole.member, ProjectRole.viewer]


class MemberAdd(BaseModel):
    """Schema for adding a member to a project."""

    user_id: int
    role: AssignableRole = ProjectRole.viewer

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": 2,
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

    user_id: int
    project_id: int
    role: ProjectRole

    model_config = ConfigDict(from_attributes=True)


class MemberListResponse(BaseModel):
    """Response for listing project members."""

    items: list[MemberResponse]
    total: int
    page: int
    page_size: int
