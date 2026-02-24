import logging
import uuid

from sqlalchemy import exists, func, select, true
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.core.enums import ProjectRole
from app.core.exceptions import ConflictError
from app.core.utils import apply_update

logger = logging.getLogger(__name__)


async def create_user_project(
    user_id: uuid.UUID,
    project_in: schemas.ProjectCreate,
    session: AsyncSession,
) -> models.Project:
    project = models.Project(
        name=project_in.name,
        description=project_in.description,
        user_id=user_id,
    )

    try:
        session.add(project)
        await session.flush()  # get project.id without committing
        owner_membership = models.UserProject(
            user_id=user_id, project_id=project.id, role=ProjectRole.owner
        )
        session.add(owner_membership)
        await session.commit()
        logger.info("Project created: %s (user_id: %s)", project.project_key, user_id)
    except IntegrityError as e:
        await session.rollback()
        logger.warning(
            "Project creation failed: Duplicate name for user_id: %s", user_id
        )
        raise ConflictError("Project already exists") from e
    await session.refresh(project)

    return project


async def get_project_by_key(
    project_key: str, session: AsyncSession
) -> models.Project | None:
    result = await session.scalars(
        select(models.Project).where(models.Project.project_key == project_key)
    )
    return result.one_or_none()


async def get_user_project_by_key(
    user_id: uuid.UUID, project_key: str, session: AsyncSession
) -> models.Project | None:
    result = await session.scalars(
        select(models.Project)
        .join(models.UserProject, models.UserProject.project_id == models.Project.id)
        .where(
            models.UserProject.user_id == user_id,
            models.Project.project_key == project_key,
        )
    )
    return result.one_or_none()


async def get_user_projects(
    user_id: uuid.UUID,
    session: AsyncSession,
    pagination: schemas.PaginationParams,
    active_only: bool = False,
) -> schemas.PaginatedResult[models.Project]:
    """Get a list of projects for a user with total count."""

    total = await session.scalar(
        select(func.count(models.Project.id))
        .join(models.UserProject, models.UserProject.project_id == models.Project.id)
        .where(models.UserProject.user_id == user_id)
        .where(models.Project.is_active.is_(True) if active_only else true())
    )

    items = (
        await session.scalars(
            select(models.Project)
            .join(
                models.UserProject, models.UserProject.project_id == models.Project.id
            )
            .where(models.UserProject.user_id == user_id)
            .where(models.Project.is_active.is_(True) if active_only else true())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
    ).all()

    return schemas.PaginatedResult(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


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
    await session.delete(project)
    await session.commit()
