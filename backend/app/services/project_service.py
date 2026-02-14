import logging
import secrets
from collections.abc import Sequence

from sqlalchemy import exists, func, select, true
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.core.config import settings
from app.core.exceptions import ConflictError
from app.core.utils import apply_update

logger = logging.getLogger(__name__)


async def create_user_project(
    user_id: int,
    project_in: schemas.ProjectCreate,
    session: AsyncSession,
) -> models.Project:
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
        logger.info("Project created: %s (user_id: %s)", project_key, user_id)
    except IntegrityError as e:
        await session.rollback()
        logger.warning(
            "Project creation failed: Duplicate name for user_id: %s", user_id
        )
        raise ConflictError("Project already exists") from e
    await session.refresh(project)

    return project


async def get_user_project_by_key(
    user_id: int, project_key: str, session: AsyncSession
) -> models.Project | None:
    stmt = select(models.Project).where(
        models.Project.user_id == user_id,
        models.Project.project_key == project_key,
    )
    return (await session.scalars(stmt)).one_or_none()


async def get_user_projects(
    user_id: int,
    session: AsyncSession,
    active_only: bool = False,
    offset: int = 0,
    limit: int = 20,
) -> Sequence[models.Project]:
    """Get a list of projects for a user."""

    stmt = (
        select(models.Project)
        .where(models.Project.user_id == user_id)
        .where(models.Project.is_active.is_(True) if active_only else true())
        .offset(offset)
        .limit(limit)
    )

    return (await session.scalars(stmt)).all()


async def count_user_projects(
    user_id: int,
    session: AsyncSession,
    active_only: bool = False,
) -> int:
    """Count projects for a user."""
    stmt = (
        select(func.count(models.Project.id))
        .where(models.Project.user_id == user_id)
        .where(models.Project.is_active.is_(True) if active_only else true())
    )
    return (await session.scalar(stmt)) or 0


async def update_user_project(
    project: models.Project,
    update_data: schemas.ProjectUpdate,
    session: AsyncSession,
) -> models.Project:
    # Check if the new name is already in use
    if update_data.name is not None and update_data.name != project.name:
        stmt = select(
            exists().where(
                models.Project.user_id == project.user_id,
                models.Project.name == update_data.name,
                models.Project.id != project.id,
            )
        )
        if await session.scalar(stmt):
            logger.warning(
                "Project update failed: Name '%s' already in use for user_id: %s",
                update_data.name,
                project.user_id,
            )
            raise ConflictError("Project name already in use")

    apply_update(project, update_data)

    await session.commit()
    await session.refresh(project)

    logger.info(
        "Project updated: %s (user_id: %s)", project.project_key, project.user_id
    )
    return project


async def delete_user_project(
    project: models.Project,
    session: AsyncSession,
) -> None:
    project_key = project.project_key
    user_id = project.user_id
    await session.delete(project)
    await session.commit()
    logger.info("Project deleted: %s (user_id: %s)", project_key, user_id)


def _generate_project_key(name: str) -> str:
    """Generate a project key for a project."""
    return (
        name.lower().replace(" ", "-")
        + "-"
        + secrets.token_hex(settings.PROJECT_SUFFIX_LENGTH)
    )
