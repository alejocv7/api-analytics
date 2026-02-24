import uuid

from fastapi import APIRouter, Request, status

from app import models, schemas
from app.core import rate_limits
from app.core.rate_limiter import get_user_key, limiter
from app.dependencies import OwnerProjectDep, ProjectDep, SessionDep
from app.schemas import PaginationQuery
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
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        403: {
            "model": schemas.ErrorResponse,
            "description": "Not owner of the project",
        },
        409: {"model": schemas.ErrorResponse, "description": "API key limit reached"},
        429: {"model": schemas.ErrorResponse, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(rate_limits.DATA_WRITE, key_func=get_user_key)
async def create_api_key(
    request: Request,  # noqa: ARG001
    key_in: schemas.APIKeyCreate,
    project: OwnerProjectDep,
    session: SessionDep,
) -> schemas.APIKeyCreateResponse:
    api_key, plain_key = await api_key_service.create_api_key(key_in, project, session)
    return _build_api_key_create_response(api_key, plain_key)


@router.get(
    "/",
    response_model=schemas.APIKeyListResponse,
    summary="List API keys",
    description="""
    Returns a list of all API keys associated with the project.
    """,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        403: {"model": schemas.ErrorResponse, "description": "Not enough permissions"},
        404: {"model": schemas.ErrorResponse, "description": "Project not found"},
    },
)
async def list_api_keys(
    project: ProjectDep,
    session: SessionDep,
    pagination: PaginationQuery,
    active_only: bool = False,
) -> schemas.APIKeyListResponse:
    result = await api_key_service.list_api_keys(
        project.id,
        session,
        pagination,
        active_only,
    )
    return schemas.APIKeyListResponse.from_result(result)


@router.get(
    "/{api_key_id}",
    response_model=schemas.APIKeyResponse,
    summary="Get API key details",
    description="""
    Retrieves the metadata of a specific API key.
    """,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        403: {"model": schemas.ErrorResponse, "description": "Not enough permissions"},
        404: {
            "model": schemas.ErrorResponse,
            "description": "API key or project not found",
        },
    },
)
async def get_api_key(
    api_key_id: uuid.UUID, project: ProjectDep, session: SessionDep
) -> models.APIKey:
    return await api_key_service.get_api_key(api_key_id, project.id, session)


@router.patch(
    "/{api_key_id}",
    response_model=schemas.APIKeyResponse,
    summary="Update an API key",
    description="""
    Updates the metadata of an API key, such as its name or expiration date.
    """,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        403: {
            "model": schemas.ErrorResponse,
            "description": "Not owner of the project",
        },
        404: {
            "model": schemas.ErrorResponse,
            "description": "API key or project not found",
        },
        422: {"model": schemas.ErrorResponse, "description": "Validation error"},
    },
)
async def update_api_key(
    api_key_id: uuid.UUID,
    update_data: schemas.APIKeyUpdate,
    project: OwnerProjectDep,
    session: SessionDep,
) -> models.APIKey:
    return await api_key_service.update_api_key(
        api_key_id, update_data, project.id, session
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
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        403: {
            "model": schemas.ErrorResponse,
            "description": "Not owner of the project",
        },
        404: {
            "model": schemas.ErrorResponse,
            "description": "API key or project not found",
        },
        429: {"model": schemas.ErrorResponse, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(rate_limits.KEY_ROTATE, key_func=get_user_key)
async def rotate_api_key(
    request: Request,  # noqa: ARG001
    api_key_id: uuid.UUID,
    project: OwnerProjectDep,
    session: SessionDep,
) -> schemas.APIKeyCreateResponse:
    api_key, plain_key = await api_key_service.rotate_api_key(
        api_key_id, project.id, session
    )
    return _build_api_key_create_response(api_key, plain_key)


@router.delete(
    "/{api_key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an API key",
    description="""
    Permanently deletes an API key.
    """,
    responses={
        401: {"model": schemas.ErrorResponse, "description": "Not authenticated"},
        403: {
            "model": schemas.ErrorResponse,
            "description": "Not owner of the project",
        },
        404: {
            "model": schemas.ErrorResponse,
            "description": "API key or project not found",
        },
        429: {"model": schemas.ErrorResponse, "description": "Rate limit exceeded"},
    },
)
@limiter.limit(rate_limits.DATA_DELETE, key_func=get_user_key)
async def delete_api_key(
    request: Request,  # noqa: ARG001
    api_key_id: uuid.UUID,
    project: OwnerProjectDep,
    session: SessionDep,
) -> None:
    await api_key_service.delete_api_key(api_key_id, project.id, session)


def _build_api_key_create_response(
    api_key: models.APIKey, plain_key: str
) -> schemas.APIKeyCreateResponse:
    """Helper to build the response for API key creation and rotation."""
    res_data = schemas.APIKeyResponse.model_validate(api_key).model_dump()
    return schemas.APIKeyCreateResponse(**res_data, key=plain_key)
