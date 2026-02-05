from __future__ import annotations

from datetime import datetime, timezone
from http import HTTPMethod, HTTPStatus
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


async def create_user(
    session: AsyncSession,
    *,
    email: str = "test@example.com",
    full_name: str = "Test User",
    password: str = "Password123!",
    is_active: bool = True,
):
    from app import models
    from app.core import security

    user = models.User(
        email=email,
        full_name=full_name,
        hashed_password=security.hash_password(password),
        is_active=is_active,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def create_project(
    session: AsyncSession,
    *,
    user: Any,
    name: str = "Test Project",
    project_key: str = "test-project-key",
    description: str | None = None,
    is_active: bool = True,
):
    from app import models

    project = models.Project(
        name=name,
        project_key=project_key,
        description=description,
        user_id=user.id,
        is_active=is_active,
    )
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project


async def create_api_key(
    session: AsyncSession,
    *,
    project: Any,
    name: str = "Test API Key",
    plain_key: str | None = None,
    is_active: bool = True,
    expires_at: datetime | None = None,
):
    from app import models
    from app.core import config, security

    if plain_key is None:
        plain_key, key_prefix, key_hash = security.generate_api_key()
    else:
        key_hash = security.hash_api_key(plain_key)
        key_prefix = plain_key[: config.settings.API_KEY_LOOKUP_PREFIX_LENGTH]

    api_key = models.APIKey(
        name=name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        project_id=project.id,
        is_active=is_active,
    )
    if expires_at is not None:
        api_key.expires_at = expires_at

    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)
    return api_key, plain_key


async def create_metric(
    session: AsyncSession,
    *,
    project: Any,
    url_path: str = "/",
    method: HTTPMethod | str = "GET",
    response_status_code: HTTPStatus | int = 200,
    response_time_ms: float = 10.0,
    timestamp: datetime | None = None,
    user_agent: str | None = None,
    ip_hash: str | None = None,
):
    from app import models

    if isinstance(method, str):
        method = HTTPMethod(method)

    if isinstance(response_status_code, HTTPStatus):
        response_status_code = int(response_status_code)

    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
    elif timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    metric = models.Metric(
        project_id=project.id,
        url_path=url_path,
        method=method,
        response_status_code=response_status_code,
        response_time_ms=response_time_ms,
        timestamp=timestamp,
        user_agent=user_agent,
        ip_hash=ip_hash,
    )
    session.add(metric)
    await session.commit()
    await session.refresh(metric)
    return metric
