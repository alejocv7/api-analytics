import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends, Path, Security
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app import models
from app.core import config, db, security
from app.core.cookies import SESSION_COOKIE
from app.core.enums import AuthSessionClientType
from app.core.exceptions import (
    AuthenticationError,
    BearerAuthenticationError,
    ForbiddenError,
)
from app.core.redis import redis_manager
from app.services import auth_service, project_service

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{config.settings.API_PREFIX}/auth/token/login",
    auto_error=False,
)


@dataclass(slots=True)
class AuthContext:
    user: models.User
    session_id: uuid.UUID
    client_type: AuthSessionClientType


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
        not security.compare_auth_secret(api_key, key_hash)
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


async def get_user_by_id(user_id: uuid.UUID, session: SessionDep) -> models.User:
    user = await session.get(models.User, user_id)
    if user is None:
        raise BearerAuthenticationError("Invalid authentication credentials")
    if not user.is_active:
        raise ForbiddenError("Inactive user")
    return user


async def get_current_auth(
    request: Request,
    session: SessionDep,
    bearer_token: Annotated[str | None, Depends(reusable_oauth2)],
) -> AuthContext:
    if bearer_token:
        token_data = security.decode_token(bearer_token)
        user = await get_user_by_id(token_data.user_id, session)
        return _make_auth_context(
            request, user, token_data.session_id, AuthSessionClientType.token
        )

    session_secret = request.cookies.get(SESSION_COOKIE)
    if not session_secret:
        raise AuthenticationError("Not authenticated")

    auth_session = await auth_service.get_active_web_session(session_secret, session)
    user = await get_user_by_id(auth_session.user_id, session)
    return _make_auth_context(request, user, auth_session.id, AuthSessionClientType.web)


CurrentAuthDep = Annotated[AuthContext, Depends(get_current_auth)]


async def get_current_web_auth(auth: CurrentAuthDep) -> AuthContext:
    if auth.client_type != AuthSessionClientType.web:
        raise AuthenticationError("Not authenticated")
    return auth


CurrentWebAuthDep = Annotated[AuthContext, Depends(get_current_web_auth)]


async def get_current_token_auth(auth: CurrentAuthDep) -> AuthContext:
    if auth.client_type != AuthSessionClientType.token:
        raise AuthenticationError("Not authenticated")
    return auth


CurrentTokenAuthDep = Annotated[AuthContext, Depends(get_current_token_auth)]


async def get_current_user(auth: CurrentAuthDep) -> models.User:
    return auth.user


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

# ------------------- Helper functions -------------------


def _make_auth_context(
    request: Request,
    user: models.User,
    session_id: uuid.UUID,
    client_type: AuthSessionClientType,
) -> AuthContext:
    request.state.user = user
    return AuthContext(user=user, session_id=session_id, client_type=client_type)
