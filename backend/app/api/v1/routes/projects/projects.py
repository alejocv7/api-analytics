from fastapi import APIRouter, Query, Request, status

from app import models, schemas
from app.core.rate_limiter import limiter
from app.dependencies import CurrentUserDep, ProjectDep, SessionDep
from app.services import project_service

router = APIRouter()


@router.get(
    "/",
    response_model=schemas.ProjectListResponse,
    summary="List all projects",
    description="""
    Returns a list of all projects belonging to the authenticated user.
    """,
)
async def get_projects(
    user: CurrentUserDep,
    session: SessionDep,
    active_only: bool = False,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> schemas.ProjectListResponse:
    items = await project_service.get_user_projects(
        user.id,
        session,
        active_only=active_only,
        offset=(page - 1) * page_size,
        limit=page_size,
    )
    total = await project_service.count_user_projects(
        user.id, session, active_only=active_only
    )
    return schemas.ProjectListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


@router.post(
    "/",
    response_model=schemas.ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="""
    Creates a new project for the authenticated user.

    Each project is used to group metrics and can have multiple associated API keys.
    """,
)
@limiter.limit("20/minute")
async def create_project(
    request: Request,  # noqa: ARG001
    project_in: schemas.ProjectCreate,
    user: CurrentUserDep,
    session: SessionDep,
) -> models.Project:
    return await project_service.create_user_project(user.id, project_in, session)


@router.get(
    "/{project_key}",
    response_model=schemas.ProjectResponse,
    summary="Get project details",
    description="""
    Retrieves the details of a specific project identified by its project key.
    """,
)
async def get_project(project: ProjectDep) -> models.Project:
    return project


@router.patch(
    "/{project_key}",
    response_model=schemas.ProjectResponse,
    summary="Update a project",
    description="""
    Updates the information of an existing project.
    """,
)
async def update_project(
    project: ProjectDep,
    update_data: schemas.ProjectUpdate,
    session: SessionDep,
) -> models.Project:
    return await project_service.update_user_project(project, update_data, session)


@router.delete(
    "/{project_key}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    description="""
    Deletes a project and all its associated API keys and metrics.

    This action is irreversible!
    """,
)
@limiter.limit("10/minute")
async def delete_project(
    request: Request,  # noqa: ARG001
    project: ProjectDep,
    session: SessionDep,
) -> None:
    await project_service.delete_user_project(project, session)
