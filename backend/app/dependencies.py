from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Path, Security
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app import models
from app.core import config, db, security
from app.core.exceptions import (
    AuthenticationError,
    BearerAuthenticationError,
    ForbiddenError,
    NotFoundError,
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{config.settings.API_PREFIX}/auth/login"
)
TokenDep = Annotated[str, Depends(reusable_oauth2)]


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with db.AsyncSessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]


async def get_project_id_by_api_key(
    request: Request,
    session: SessionDep,
    api_key: str = Security(api_key_header),
) -> int:
    """Validates API key and returns the Project id."""
    if not api_key:
        raise AuthenticationError("API key required")

    key_prefix = api_key[: config.settings.API_KEY_LOOKUP_PREFIX_LENGTH]
    api_key_obj = (
        await session.scalars(
            select(models.APIKey)
            .join(models.Project)
            .where(
                models.APIKey.key_prefix == key_prefix,
                models.APIKey.is_active.is_(True),
                models.Project.is_active.is_(True),
            )
        )
    ).one_or_none()

    # Prevent timing attacks by verifying the API key even when it doesn't exist.
    # This ensures the response time is similar whether or not the API key exists.
    key_hash = (
        api_key_obj.key_hash if api_key_obj else config.settings.SECURITY_DUMMY_HASH
    )

    if (
        not security.compare_api_key(api_key, key_hash)
        or not api_key_obj
        or not api_key_obj.is_valid
    ):
        raise AuthenticationError("Invalid API key")

    # Set project_id in request state for limiter
    request.state.project_id = api_key_obj.project_id

    # Record API key usage
    api_key_obj.record_usage()
    await session.commit()

    return api_key_obj.project_id


ProjectIdDep = Annotated[int, Depends(get_project_id_by_api_key)]


async def get_current_user(
    request: Request, session: SessionDep, token: TokenDep
) -> models.User:
    token_data = security.decode_token(token)
    user = await session.get(models.User, token_data.user_id)
    if user is None:
        raise BearerAuthenticationError("Invalid authentication credentials")
    if not user.is_active:
        raise ForbiddenError("Inactive user")

    request.state.user = user
    return user


CurrentUserDep = Annotated[models.User, Depends(get_current_user)]


async def get_user_project(
    user: CurrentUserDep,
    session: SessionDep,
    project_key: str = Path(...),
) -> models.Project:
    # Avoid circular import
    from app.services import project_service

    project = await project_service.get_user_project_by_key(
        user.id, project_key, session
    )
    if not project:
        raise NotFoundError("Project not found")
    return project


ProjectDep = Annotated[models.Project, Depends(get_user_project)]


async def get_owner_project(
    project: ProjectDep,
    user: CurrentUserDep,
) -> models.Project:
    """Dependency that restricts access to the project owner only."""
    if project.user_id != user.id:
        raise ForbiddenError("Only the project owner can perform this action")
    return project


OwnerProjectDep = Annotated[models.Project, Depends(get_owner_project)]
