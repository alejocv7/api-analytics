from fastapi import APIRouter, status

from app import schemas
from app.dependencies import CurrentUserDep, SessionDep
from app.services import project

router = APIRouter()


@router.get("/", response_model=list[schemas.ProjectResponse])
async def get_projects(user: CurrentUserDep, session: SessionDep):
    return project.get_user_projects(user.id, session)


@router.post("/", response_model=schemas.ProjectResponse)
async def create_project(
    project_in: schemas.ProjectCreate, user: CurrentUserDep, session: SessionDep
):
    return project.create_user_project(user.id, project_in, session)


@router.get("/{project_key}", response_model=schemas.ProjectResponse)
async def get_project(project_key: str, user: CurrentUserDep, session: SessionDep):
    return project.get_user_project_by_key(project_key, user.id, session)


@router.put("/{project_key}", response_model=schemas.ProjectResponse)
async def update_project(
    project_key: str,
    update_data: schemas.ProjectUpdate,
    user: CurrentUserDep,
    session: SessionDep,
):
    return project.update_user_project(user.id, project_key, update_data, session)


@router.delete("/{project_key}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_key: str, user: CurrentUserDep, session: SessionDep):
    project.delete_user_project(user.id, project_key, session)
