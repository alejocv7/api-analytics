from typing import Sequence

from fastapi import APIRouter, status

from app import schemas
from app.dependencies import CurrentUserDep, ProjectDep, SessionDep
from app.services import project_service

router = APIRouter()


@router.get(
    "/",
    response_model=Sequence[schemas.ProjectResponse],
    summary="List all projects",
    description="""
    Returns a list of all projects belonging to the authenticated user.
    """,
)
async def get_projects(user: CurrentUserDep, session: SessionDep):
    return await project_service.get_user_projects(user.id, session)


@router.post(
    "/",
    response_model=schemas.ProjectResponse,
    summary="Create a new project",
    description="""
    Creates a new project for the authenticated user.
    
    Each project is used to group metrics and can have multiple associated API keys.
    """,
)
async def create_project(
    project_in: schemas.ProjectCreate, user: CurrentUserDep, session: SessionDep
):
    return await project_service.create_user_project(user.id, project_in, session)


@router.get(
    "/{project_key}",
    response_model=schemas.ProjectResponse,
    summary="Get project details",
    description="""
    Retrieves the details of a specific project identified by its project key.
    """,
)
async def get_project(project: ProjectDep):
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
):
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
async def delete_project(project: ProjectDep, session: SessionDep):
    await project_service.delete_user_project(project, session)
