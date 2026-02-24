import uuid

from fastapi import APIRouter, status

from app import models, schemas
from app.dependencies import OwnerProjectDep, ProjectDep, SessionDep
from app.schemas import PaginationQuery
from app.services import member_service

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a project member",
    description="""
    Adds a user as a member of the project. Only the project owner can invite members.

    The `owner` role cannot be assigned via this endpoint.
    """,
    responses={
        409: {
            "model": schemas.ErrorResponse,
            "description": "User already a member or owner",
        },
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        403: {
            "model": schemas.ErrorResponse,
            "description": "Not owner of the project",
        },
        404: {
            "model": schemas.ErrorResponse,
            "description": "User or project not found",
        },
    },
)
async def add_member(
    member_in: schemas.MemberAdd,
    project: OwnerProjectDep,
    session: SessionDep,
) -> models.UserProject:
    return await member_service.add_member(
        project, member_in.email, member_in.role, session
    )


@router.get(
    "/",
    response_model=schemas.MemberListResponse,
    summary="List project members",
    description="""
    Returns all members of the project, including the owner.
    """,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        403: {"model": schemas.ErrorResponse, "description": "Not enough permissions"},
        404: {"model": schemas.ErrorResponse, "description": "Project not found"},
    },
)
async def list_members(
    project: ProjectDep,
    session: SessionDep,
    pagination: PaginationQuery,
) -> schemas.MemberListResponse:
    items = await member_service.list_members(
        project.id, session, offset=pagination.offset, limit=pagination.page_size
    )
    total = await member_service.count_members(project.id, session)
    return schemas.MemberListResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.patch(
    "/{user_id}",
    response_model=schemas.MemberResponse,
    summary="Update a member's role",
    description="""
    Changes the role of an existing project member. Only the project owner can change
    roles. The owner's role cannot be changed, and the `owner` role cannot be assigned.
    """,
    responses={
        400: {
            "model": schemas.ErrorResponse,
            "description": "Cannot change owner role",
        },
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        403: {
            "model": schemas.ErrorResponse,
            "description": "Not owner of the project",
        },
        404: {
            "model": schemas.ErrorResponse,
            "description": "Member or project not found",
        },
    },
)
async def update_member_role(
    user_id: uuid.UUID,
    role_update: schemas.MemberUpdate,
    project: OwnerProjectDep,
    session: SessionDep,
) -> models.UserProject:
    return await member_service.update_member_role(
        project, user_id, role_update.role, session
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a project member",
    description="""
    Removes a user from the project. Only the project owner can remove members.

    The project owner cannot be removed.
    """,
    responses={
        400: {
            "model": schemas.ErrorResponse,
            "description": "Cannot remove project owner",
        },
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        403: {
            "model": schemas.ErrorResponse,
            "description": "Not owner of the project",
        },
        404: {
            "model": schemas.ErrorResponse,
            "description": "Member or project not found",
        },
    },
)
async def remove_member(
    user_id: uuid.UUID,
    project: OwnerProjectDep,
    session: SessionDep,
) -> None:
    await member_service.remove_member(project, user_id, session)
