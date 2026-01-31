from fastapi import APIRouter, status

from app import schemas
from app.dependencies import CurrentUserDep, ProjectDep, SessionDep
from app.services import project_service

router = APIRouter()


@router.get("/", response_model=list[schemas.ProjectResponse])
async def get_projects(user: CurrentUserDep, session: SessionDep):
    return project_service.get_user_projects(user.id, session)


@router.post("/", response_model=schemas.ProjectResponse)
async def create_project(
    project_in: schemas.ProjectCreate, user: CurrentUserDep, session: SessionDep
):
    return project_service.create_user_project(user.id, project_in, session)


@router.get("/{project_key}", response_model=schemas.ProjectResponse)
async def get_project(project: ProjectDep):
    return project


@router.patch("/{project_key}", response_model=schemas.ProjectResponse)
async def update_project(
    project: ProjectDep,
    update_data: schemas.ProjectUpdate,
    session: SessionDep,
):
    return project_service.update_user_project(project, update_data, session)


@router.delete("/{project_key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project: ProjectDep, session: SessionDep):
    project_service.delete_user_project(project, session)
