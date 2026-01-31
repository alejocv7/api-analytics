from fastapi import APIRouter, status

from app import schemas
from app.dependencies import CurrentUserDep, SessionDep
from app.services import api_key_service, project_service

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.APIKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    key_in: schemas.APIKeyCreate,
    project_key: str,
    user: CurrentUserDep,
    session: SessionDep,
):
    project = project_service.get_user_project_by_key(user.id, project_key, session)
    api_key, plain_key = api_key_service.create_api_key(key_in, project, session)

    res = schemas.APIKeyCreateResponse.model_validate(api_key)
    res.key = plain_key
    return res


@router.get("/", response_model=list[schemas.APIKeyResponse])
async def list_api_keys(
    project_key: str,
    session: SessionDep,
    user: CurrentUserDep,
    active_only: bool = False,
):
    project = project_service.get_user_project_by_key(user.id, project_key, session)
    return api_key_service.list_api_keys(project.id, session, active_only)


@router.get("/{api_key_id}", response_model=schemas.APIKeyResponse)
async def get_api_key(
    api_key_id: int, project_key: str, user: CurrentUserDep, session: SessionDep
):
    project = project_service.get_user_project_by_key(user.id, project_key, session)
    return api_key_service.get_api_key(api_key_id, project.id, session)


@router.patch("/{api_key_id}", response_model=schemas.APIKeyResponse)
async def update_api_key(
    api_key_id: int,
    project_key: str,
    user: CurrentUserDep,
    update_data: schemas.APIKeyUpdate,
    session: SessionDep,
):
    project = project_service.get_user_project_by_key(user.id, project_key, session)
    return api_key_service.update_api_key(api_key_id, project.id, update_data, session)


@router.post("/{api_key_id}/rotate", response_model=schemas.APIKeyCreateResponse)
async def rotate_api_key(
    api_key_id: int, project_key: str, user: CurrentUserDep, session: SessionDep
):
    project = project_service.get_user_project_by_key(user.id, project_key, session)
    api_key, plain_key = api_key_service.rotate_api_key(api_key_id, project.id, session)

    res = schemas.APIKeyCreateResponse.model_validate(api_key)
    res.key = plain_key
    return res


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: int, project_key: str, user: CurrentUserDep, session: SessionDep
):
    project = project_service.get_user_project_by_key(user.id, project_key, session)
    api_key_service.delete_api_key(api_key_id, project.id, session)
