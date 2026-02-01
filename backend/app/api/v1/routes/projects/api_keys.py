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
    summary="Create an API key",
    description="""
    Creates a new API key for the project.
    
    The response includes the plain-text API key. This is the **only time** the key
    will be shown, so make sure to save it safely.
    """,
)
async def create_api_key(
    key_in: schemas.APIKeyCreate, project: ProjectDep, session: SessionDep
):
    api_key, plain_key = await api_key_service.create_api_key(key_in, project, session)

    res = schemas.APIKeyCreateResponse.model_validate(api_key)
    res.key = plain_key
    return res


@router.get(
    "/",
    response_model=Sequence[schemas.APIKeyResponse],
    summary="List API keys",
    description="""
    Returns a list of all API keys associated with the project.
    """,
)
async def list_api_keys(
    project: ProjectDep, session: SessionDep, active_only: bool = False
):
    return await api_key_service.list_api_keys(project.id, session, active_only)


@router.get(
    "/{api_key_id}",
    response_model=schemas.APIKeyResponse,
    summary="Get API key details",
    description="""
    Retrieves the metadata of a specific API key.
    """,
)
async def get_api_key(api_key_id: int, project: ProjectDep, session: SessionDep):
    return await api_key_service.get_api_key(api_key_id, project.id, session)


@router.patch(
    "/{api_key_id}",
    response_model=schemas.APIKeyResponse,
    summary="Update an API key",
    description="""
    Updates the metadata or status of an existing API key.
    """,
)
async def update_api_key(
    api_key_id: int,
    project: ProjectDep,
    update_data: schemas.APIKeyUpdate,
    session: SessionDep,
):
    return await api_key_service.update_api_key(
        api_key_id, project.id, update_data, session
    )


@router.post(
    "/{api_key_id}/rotate",
    response_model=schemas.APIKeyCreateResponse,
    summary="Rotate an API key",
    description="""
    Deactivates the current API key and creates a new one with the same configuration.
    
    This is useful for security purposes if a key has been compromised.
    
    The response includes the new plain-text API key.
    """,
)
async def rotate_api_key(api_key_id: int, project: ProjectDep, session: SessionDep):
    api_key, plain_key = await api_key_service.rotate_api_key(
        api_key_id, project.id, session
    )

    res = schemas.APIKeyCreateResponse.model_validate(api_key)
    res.key = plain_key
    return res


@router.delete(
    "/{api_key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an API key",
    description="""
    Permanently deletes an API key.
    """,
)
async def delete_api_key(api_key_id: int, project: ProjectDep, session: SessionDep):
    await api_key_service.delete_api_key(api_key_id, project.id, session)
