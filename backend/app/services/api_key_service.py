from typing import Sequence

from fastapi import status
from sqlalchemy import func, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.core.config import settings
from app.core.exceptions import APIError


async def create_api_key(
    key_in: schemas.APIKeyCreate, project: models.Project, session: AsyncSession
) -> tuple[models.APIKey, str]:
    # Check if within limit
    stmt = select(func.count(models.APIKey.id)).where(
        models.APIKey.project_id == project.id, models.APIKey.is_active.is_(True)
    )
    result = await session.execute(stmt)
    active_keys_count = result.scalar_one()
    if active_keys_count >= settings.API_KEY_PROJECT_LIMIT:
        raise ValueError("Project has reached the maximum number of API keys")

    api_key, plain_key = models.APIKey.new_key(
        key_in.name, project.id, key_in.expires_at
    )

    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)

    return api_key, plain_key


async def list_api_keys(
    project_id: int,
    session: AsyncSession,
    active_only: bool = False,
) -> Sequence[models.APIKey]:
    stmt = (
        select(models.APIKey)
        .where(
            models.APIKey.project_id == project_id,
            models.APIKey.is_active == active_only if active_only else true(),
        )
        .order_by(models.APIKey.created_at.desc())
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_api_key(
    api_key_id: int, project_id: int, session: AsyncSession
) -> models.APIKey:
    stmt = select(models.APIKey).where(
        models.APIKey.id == api_key_id,
        models.APIKey.project_id == project_id,
    )
    result = await session.execute(stmt)
    return result.scalars().one()


async def update_api_key(
    api_key_id: int,
    project_id: int,
    update_data: schemas.APIKeyUpdate,
    session: AsyncSession,
) -> models.APIKey:
    api_key = await get_api_key(api_key_id, project_id, session)

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(api_key, key, value)

    await session.commit()
    await session.refresh(api_key)
    return api_key


async def rotate_api_key(
    api_key_id: int, project_id: int, session: AsyncSession
) -> tuple[models.APIKey, str]:
    old_key = await get_api_key(api_key_id, project_id, session)
    if not old_key.is_active or old_key.is_expired:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Cannot rotate an inactive or expired API key.",
        )

    new_api_key, new_plain_key = models.APIKey.new_key(
        old_key.name, old_key.project_id, old_key.expires_at
    )

    session.add(new_api_key)
    old_key.is_active = False
    if "(rotated)" not in old_key.name:
        old_key.name += " (rotated)"

    await session.commit()
    await session.refresh(new_api_key)

    return new_api_key, new_plain_key


async def delete_api_key(
    api_key_id: int, project_id: int, session: AsyncSession
) -> None:
    api_key = await get_api_key(api_key_id, project_id, session)

    # Check this is not the last active key
    stmt = select(func.count(models.APIKey.id)).where(
        models.APIKey.project_id == project_id,
        models.APIKey.is_active.is_(True),
        models.APIKey.id != api_key_id,
    )
    result = await session.execute(stmt)
    active_keys_count = result.scalar_one()
    if active_keys_count == 0 and api_key.is_active:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Cannot delete the last active API key.",
        )

    await session.delete(api_key)
    await session.commit()
