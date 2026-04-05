from fastapi import APIRouter, Request, status

from app import schemas
from app.core import rate_limits
from app.core.rate_limiter import get_user_key, limiter
from app.dependencies import (
    CurrentUserDep,
    OwnerProjectDep,
    ProjectDep,
    SessionDep,
)
from app.schemas import PaginationQuery
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get(
    "",
    response_model=schemas.ProjectListResponse,
    summary="List all projects",
    description="""
    Returns a list of all projects belonging to the authenticated user.
    """,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        429: {"model": schemas.ErrorResponse, "description": "Rate limit exceeded"},
    },
)
async def get_projects(
    user: CurrentUserDep,
    session: SessionDep,
    pagination: PaginationQuery,
    active_only: bool = False,
) -> schemas.ProjectListResponse:
    result = await project_service.get_user_projects(
        user.id,
        session,
        pagination,
        active_only=active_only,
    )
    return schemas.ProjectListResponse.from_result(result)


@router.post(
    "",
    response_model=schemas.ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="""
    Creates a new project for the authenticated user.

    Each project is used to group metrics and can have multiple associated API keys.
    """,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        409: {
            "model": schemas.ErrorResponse,
            "description": "Project name already exists",
        },
        422: {"model": schemas.ErrorResponse, "description": "Validation error"},
        429: {"model": schemas.ErrorResponse, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(rate_limits.DATA_WRITE, key_func=get_user_key)
async def create_project(
    request: Request,  # noqa: ARG001
    project_in: schemas.ProjectCreate,
    user: CurrentUserDep,
    session: SessionDep,
) -> schemas.ProjectResponse:
    return await project_service.create_user_project(user.id, project_in, session)


@router.get(
    "/{project_key}",
    response_model=schemas.ProjectResponse,
    summary="Get project details",
    description="""
    Retrieves the details of a specific project identified by its project key.
    """,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        403: {"model": schemas.ErrorResponse, "description": "Not enough permissions"},
        404: {"model": schemas.ErrorResponse, "description": "Project not found"},
    },
)
async def get_project(
    project: ProjectDep, session: SessionDep
) -> schemas.ProjectResponse:
    return await project_service.get_project_with_counts(project, session)


@router.patch(
    "/{project_key}",
    response_model=schemas.ProjectResponse,
    summary="Update a project",
    description="""
    Updates the information of an existing project.
    """,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        403: {
            "model": schemas.ErrorResponse,
            "description": "Not owner of the project",
        },
        404: {"model": schemas.ErrorResponse, "description": "Project not found"},
        409: {
            "model": schemas.ErrorResponse,
            "description": "Project name already exists",
        },
        422: {"model": schemas.ErrorResponse, "description": "Validation error"},
    },
)
async def update_project(
    project: OwnerProjectDep,
    update_data: schemas.ProjectUpdate,
    session: SessionDep,
) -> schemas.ProjectResponse:
    return await project_service.update_user_project(project, update_data, session)


@router.delete(
    "/{project_key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    description="""
    Deletes a project and all its associated API keys and metrics.

    This action is irreversible!
    """,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        403: {
            "model": schemas.ErrorResponse,
            "description": "Not owner of the project",
        },
        404: {"model": schemas.ErrorResponse, "description": "Project not found"},
        429: {"model": schemas.ErrorResponse, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(rate_limits.DATA_DELETE, key_func=get_user_key)
async def delete_project(
    request: Request,  # noqa: ARG001
    project: OwnerProjectDep,
    session: SessionDep,
) -> None:
    await project_service.delete_user_project(project, session)
