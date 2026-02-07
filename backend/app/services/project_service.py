import secrets
from typing import Sequence

from fastapi import status
from sqlalchemy import select, true
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.core.config import settings
from app.core.exceptions import APIError


async def create_user_project(
    user_id: int,
    project_in: schemas.ProjectCreate,
    session: AsyncSession,
):
    project_key = _generate_project_key(project_in.name)
    project = models.Project(
        name=project_in.name,
        description=project_in.description,
        project_key=project_key,
        user_id=user_id,
    )

    try:
        session.add(project)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise APIError(
            status_code=status.HTTP_409_CONFLICT,
            message="Project already exists",
        )
    await session.refresh(project)

    return project


async def get_user_project_by_key(
    user_id: int, project_key: str, session: AsyncSession
):
    statement = select(models.Project).where(
        models.Project.user_id == user_id,
        models.Project.project_key == project_key,
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def get_user_projects(
    user_id: int,
    session: AsyncSession,
    active_only: bool = False,
    offset: int = 0,
    limit: int = 20,
) -> Sequence[models.Project]:
    """Get a list of projects for a user."""

    statement = (
        select(models.Project)
        .where(models.Project.user_id == user_id)
        .where(models.Project.is_active if active_only else true())
        .offset(offset)
        .limit(limit)
    )

    result = await session.execute(statement)
    return result.scalars().all()


async def update_user_project(
    project: models.Project,
    update_data: schemas.ProjectUpdate,
    session: AsyncSession,
) -> models.Project:
    # Check if the new name is already in use
    if update_data.name != project.name:
        stmt = select(models.Project).where(
            models.Project.user_id == project.user_id,
            models.Project.name == update_data.name,
            models.Project.id != project.id,
        )
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise APIError(
                status_code=status.HTTP_409_CONFLICT,
                message="Project name already in use",
            )

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(project, key, value)

    await session.commit()
    await session.refresh(project)

    return project


async def delete_user_project(
    project: models.Project,
    session: AsyncSession,
):
    await session.delete(project)
    await session.commit()


def _generate_project_key(name: str) -> str:
    """Generate a project key for a project."""
    return (
        name.lower().replace(" ", "-")
        + "-"
        + secrets.token_hex(settings.PROJECT_SUFFIX_LENGTH)
    )
