import logging
from collections.abc import Sequence

from sqlalchemy import func, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.core.config import settings
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.utils import apply_update

logger = logging.getLogger(__name__)


async def create_api_key(
    key_in: schemas.APIKeyCreate, project: models.Project, session: AsyncSession
) -> tuple[models.APIKey, str]:
    # Check if within limit
    stmt = select(func.count(models.APIKey.id)).where(
        models.APIKey.project_id == project.id, models.APIKey.is_active.is_(True)
    )

    active_keys_count = (await session.scalars(stmt)).one_or_none()
    if active_keys_count and active_keys_count >= settings.API_KEY_PROJECT_LIMIT:
        logger.warning(
            "API key creation failed: Limit reached for project_id: %s", project.id
        )
        raise ConflictError("Project has reached the maximum number of API keys")

    api_key, plain_key = models.APIKey.new_key(
        key_in.name, project.id, key_in.expires_at
    )

    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)

    logger.info("API key created: %s (project_id: %s)", api_key.id, project.id)
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
            models.APIKey.is_active.is_(True) if active_only else true(),
        )
        .order_by(models.APIKey.created_at.desc())
    )
    return (await session.scalars(stmt)).all()


async def get_api_key(
    api_key_id: int, project_id: int, session: AsyncSession
) -> models.APIKey:
    stmt = select(models.APIKey).where(
        models.APIKey.id == api_key_id,
        models.APIKey.project_id == project_id,
    )
    api_key = (await session.scalars(stmt)).one_or_none()
    if api_key is None:
        raise NotFoundError("API key not found")
    return api_key


async def update_api_key(
    api_key_id: int,
    update_data: schemas.APIKeyUpdate,
    project_id: int,
    session: AsyncSession,
) -> models.APIKey:
    api_key = await get_api_key(api_key_id, project_id, session)

    apply_update(api_key, update_data)

    await session.commit()
    await session.refresh(api_key)
    logger.info("API key updated: %s (project_id: %s)", api_key_id, project_id)
    return api_key


async def rotate_api_key(
    api_key_id: int, project_id: int, session: AsyncSession
) -> tuple[models.APIKey, str]:
    old_key = await get_api_key(api_key_id, project_id, session)
    if not old_key.is_active or old_key.is_expired:
        logger.warning(
            "API key rotation failed: Key is inactive or expired: %s (project_id: %s)",
            api_key_id,
            project_id,
        )
        raise BadRequestError("Cannot rotate an inactive or expired API key.")

    new_api_key, new_plain_key = models.APIKey.new_key(
        old_key.name, old_key.project_id, old_key.expires_at
    )

    session.add(new_api_key)
    old_key.is_active = False
    if "(rotated)" not in old_key.name:
        old_key.name += " (rotated)"

    await session.commit()
    await session.refresh(new_api_key)

    logger.info(
        "API key rotated: %s -> %s (project_id: %s)",
        api_key_id,
        new_api_key.id,
        project_id,
    )
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
    active_keys_count = await session.scalar(stmt)
    if active_keys_count == 0 and api_key.is_active:
        logger.warning(
            "API key deletion failed: Last active key for project_id: %s", project_id
        )
        raise BadRequestError("Cannot delete the last active API key.")

    await session.delete(api_key)
    await session.commit()
    logger.info("API key deleted: %s (project_id: %s)", api_key_id, project_id)
