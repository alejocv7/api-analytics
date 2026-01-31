from typing import Sequence

from app import models, schemas
from app.core.config import settings
from app.core.exceptions import APIError
from fastapi import status
from sqlalchemy import select, true
from sqlalchemy.orm import Session


def create_api_key(
    key_in: schemas.APIKeyCreate, project: models.Project, session: Session
) -> tuple[models.APIKey, str]:
    # Check if within limit
    active_keys_count = sum(1 for key in project.api_keys if key.is_active)
    if active_keys_count >= settings.API_KEY_PROJECT_LIMIT:
        raise ValueError("Project has reached the maximum number of API keys")

    api_key, plain_key = models.APIKey.new_key(
        key_in.name, project.id, key_in.expires_at
    )

    session.add(api_key)
    session.commit()
    session.refresh(api_key)

    return api_key, plain_key


def list_api_keys(
    project_id: int,
    session: Session,
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
    return session.scalars(stmt).all()


def get_api_key(api_key_id: int, project_id: int, session: Session) -> models.APIKey:
    stmt = select(models.APIKey).where(
        models.APIKey.id == api_key_id,
        models.APIKey.project_id == project_id,
    )
    return session.scalars(stmt).one()


def update_api_key(
    api_key_id: int,
    project_id: int,
    update_data: schemas.APIKeyUpdate,
    session: Session,
) -> models.APIKey:
    api_key = get_api_key(api_key_id, project_id, session)

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(api_key, key, value)

    session.commit()
    session.refresh(api_key)
    return api_key


def rotate_api_key(
    api_key_id: int, project_id: int, session: Session
) -> tuple[models.APIKey, str]:
    old_key = get_api_key(api_key_id, project_id, session)
    if not old_key.is_active or old_key.is_expired:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Cannot rotate an inactive or expired API key.",
        )

    new_api_key, new_plain_key = models.APIKey.new_key(
        old_key.name, old_key.project_id, old_key.expires_at
    )

    with session.begin():
        session.add(new_api_key)
        old_key.is_active = False
        if "(rotated)" not in old_key.name:
            old_key.name += " (rotated)"
    session.refresh(new_api_key)

    return new_api_key, new_plain_key


def delete_api_key(api_key_id: int, project_id: int, session: Session) -> None:
    api_key = get_api_key(api_key_id, project_id, session)

    # Check this is not the last active key
    active_keys_count = sum(
        1 for key in api_key.project.api_keys if key.is_active and key.id != api_key_id
    )
    if active_keys_count == 0 and api_key.is_active:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Cannot delete the last active API key.",
        )

    session.delete(api_key)
    session.commit()
