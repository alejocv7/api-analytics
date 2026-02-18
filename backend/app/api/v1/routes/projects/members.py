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
)
async def add_member(
    member_in: schemas.MemberAdd,
    project: OwnerProjectDep,
    session: SessionDep,
) -> models.UserProject:
    return await member_service.add_member(
        project, member_in.user_id, member_in.role, session
    )


@router.get(
    "/",
    response_model=schemas.MemberListResponse,
    summary="List project members",
    description="""
    Returns all members of the project, including the owner.
    """,
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
        items=list(items),
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
)
async def update_member_role(
    user_id: int,
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
)
async def remove_member(
    user_id: int,
    project: OwnerProjectDep,
    session: SessionDep,
) -> None:
    await member_service.remove_member(project, user_id, session)
