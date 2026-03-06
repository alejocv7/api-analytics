import logging
import uuid

from sqlalchemy import exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.core.enums import ProjectRole
from app.core.exceptions import ConflictError, NotFoundError
from app.core.utils import active_filter, apply_update

logger = logging.getLogger(__name__)


async def create_user_project(
    user_id: uuid.UUID,
    project_in: schemas.ProjectCreate,
    session: AsyncSession,
) -> schemas.ProjectResponse:
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

    return await get_project_with_counts(project, session)


async def find_project_by_key(
    project_key: str, session: AsyncSession
) -> models.Project | None:
    """Find a project by key. Returns None if not found."""
    result = await session.scalars(
        select(models.Project).where(models.Project.project_key == project_key)
    )
    return result.one_or_none()


async def get_project_by_key(project_key: str, session: AsyncSession) -> models.Project:
    """Get a project by key. Raises NotFoundError if not found."""
    project = await find_project_by_key(project_key, session)
    if not project:
        raise NotFoundError("Project not found")
    return project


async def find_user_project_by_key(
    user_id: uuid.UUID, project_key: str, session: AsyncSession
) -> models.Project | None:
    """Find a project by key for a specific user. Returns None if not found."""
    result = await session.scalars(
        select(models.Project)
        .join(models.UserProject, models.UserProject.project_id == models.Project.id)
        .where(
            models.UserProject.user_id == user_id,
            models.Project.project_key == project_key,
        )
    )
    return result.one_or_none()


async def get_user_project_by_key(
    user_id: uuid.UUID, project_key: str, session: AsyncSession
) -> models.Project:
    """Get a project by key for a specific user. Raises NotFoundError if not found."""
    project = await find_user_project_by_key(user_id, project_key, session)
    if not project:
        raise NotFoundError("Project not found")
    return project


async def get_project_with_counts(
    project: models.Project, session: AsyncSession
) -> schemas.ProjectResponse:
    """Enrich a project with member and API key counts."""
    member_count_subq = (
        select(func.count(models.UserProject.user_id))
        .where(models.UserProject.project_id == project.id)
        .scalar_subquery()
    )
    api_key_count_subq = (
        select(func.count(models.APIKey.id))
        .where(models.APIKey.project_id == project.id)
        .scalar_subquery()
    )

    row = (await session.execute(select(member_count_subq, api_key_count_subq))).one()
    member_count, api_key_count = row

    return schemas.ProjectResponse(
        **project.__dict__,
        member_count=member_count,
        api_key_count=api_key_count,
    )


async def get_user_projects(
    user_id: uuid.UUID,
    session: AsyncSession,
    pagination: schemas.PaginationParams,
    active_only: bool = False,
) -> schemas.PaginatedResult[schemas.ProjectResponse]:
    """Get a list of projects for a user with total count and aggregate stats."""

    # Correlated subqueries fetch counts for all projects in a single query.
    member_count_subq = (
        select(func.count(models.UserProject.user_id))
        .where(models.UserProject.project_id == models.Project.id)
        .correlate(models.Project)
        .scalar_subquery()
    )
    api_key_count_subq = (
        select(func.count(models.APIKey.id))
        .where(models.APIKey.project_id == models.Project.id)
        .correlate(models.Project)
        .scalar_subquery()
    )

    rows = (
        await session.execute(
            select(
                models.Project,
                member_count_subq,
                api_key_count_subq,
                func.count(models.Project.id).over().label("total"),
            )
            .join(
                models.UserProject, models.UserProject.project_id == models.Project.id
            )
            .where(models.UserProject.user_id == user_id)
            .where(active_filter(models.Project.is_active, active_only))
            .order_by(models.Project.created_at.desc())
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
    ).all()

    items = [
        schemas.ProjectResponse(
            **project.__dict__,
            member_count=member_count,
            api_key_count=api_key_count,
        )
        for project, member_count, api_key_count, _ in rows
    ]

    total = rows[0].total if rows else 0
    return schemas.PaginatedResult(items=items, total=total, pagination=pagination)


async def update_user_project(
    project: models.Project,
    update_data: schemas.ProjectUpdate,
    session: AsyncSession,
) -> schemas.ProjectResponse:
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
    return await get_project_with_counts(project, session)


async def delete_user_project(
    project: models.Project,
    session: AsyncSession,
) -> None:
    await session.delete(project)
    await session.commit()
