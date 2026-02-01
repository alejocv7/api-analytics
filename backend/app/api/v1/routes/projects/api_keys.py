from typing import Sequence

from fastapi import APIRouter, status

from app import schemas
from app.dependencies import ProjectDep, SessionDep
from app.services import api_key_service

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.APIKeyCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    key_in: schemas.APIKeyCreate, project: ProjectDep, session: SessionDep
):
    api_key, plain_key = await api_key_service.create_api_key(key_in, project, session)

    res = schemas.APIKeyCreateResponse.model_validate(api_key)
    res.key = plain_key
    return res


@router.get("/", response_model=Sequence[schemas.APIKeyResponse])
async def list_api_keys(
    project: ProjectDep, session: SessionDep, active_only: bool = False
):
    return await api_key_service.list_api_keys(project.id, session, active_only)


@router.get("/{api_key_id}", response_model=schemas.APIKeyResponse)
async def get_api_key(api_key_id: int, project: ProjectDep, session: SessionDep):
    return await api_key_service.get_api_key(api_key_id, project.id, session)


@router.patch("/{api_key_id}", response_model=schemas.APIKeyResponse)
async def update_api_key(
    api_key_id: int,
    project: ProjectDep,
    update_data: schemas.APIKeyUpdate,
    session: SessionDep,
):
    return await api_key_service.update_api_key(
        api_key_id, project.id, update_data, session
    )


@router.post("/{api_key_id}/rotate", response_model=schemas.APIKeyCreateResponse)
async def rotate_api_key(api_key_id: int, project: ProjectDep, session: SessionDep):
    api_key, plain_key = await api_key_service.rotate_api_key(
        api_key_id, project.id, session
    )

    res = schemas.APIKeyCreateResponse.model_validate(api_key)
    res.key = plain_key
    return res


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(api_key_id: int, project: ProjectDep, session: SessionDep):
    await api_key_service.delete_api_key(api_key_id, project.id, session)
