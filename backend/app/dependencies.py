import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends, Header, Path, Security
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app import models
from app.core import config, db, security
from app.core.cookies import ACCESS_TOKEN_COOKIE
from app.core.enums import TokenTransport
from app.core.exceptions import (
    AuthenticationError,
    BearerAuthenticationError,
    ForbiddenError,
)
from app.core.headers import TOKEN_TRANSPORT_HEADER
from app.core.redis import redis_manager
from app.services import project_service

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{config.settings.API_PREFIX}/auth/login",
    auto_error=False,  # cookie transport won't have a Bearer header; don't auto-raise
)


def get_token_transport(
    x_token_transport: Annotated[
        TokenTransport | None, Header(alias=TOKEN_TRANSPORT_HEADER)
    ] = None,
) -> TokenTransport:
    return x_token_transport or TokenTransport.COOKIE


TokenTransportDep = Annotated[TokenTransport, Depends(get_token_transport)]


async def get_db() -> AsyncGenerator[AsyncSession]:
    async with db.AsyncSessionLocal() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_db)]


async def get_redis() -> AsyncGenerator[redis.Redis]:
    if redis_manager.client is None:
        raise RuntimeError("Redis is not initialized")
    yield redis_manager.client


RedisDep = Annotated[redis.Redis, Depends(get_redis)]


async def get_project_id_by_api_key(
    request: Request,
    session: SessionDep,
    api_key: str = Security(api_key_header),
) -> uuid.UUID:
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
        api_key_obj.key_hash
        if api_key_obj
        else (config.settings.SECURITY_DUMMY_API_KEY_HASH)
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


ProjectIdDep = Annotated[uuid.UUID, Depends(get_project_id_by_api_key)]


async def get_current_user(
    request: Request,
    session: SessionDep,
    bearer_token: Annotated[str | None, Depends(reusable_oauth2)],
) -> models.User:
    token = request.cookies.get(ACCESS_TOKEN_COOKIE) or bearer_token
    if not token:
        raise BearerAuthenticationError("Not authenticated")
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
    return await project_service.get_user_project_by_key(user.id, project_key, session)


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
