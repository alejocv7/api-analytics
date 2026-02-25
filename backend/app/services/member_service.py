import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import models, schemas
from app.core.enums import ProjectRole
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.services import user_service

logger = logging.getLogger(__name__)


async def add_member(
    project: models.Project,
    email: str,
    role: ProjectRole,
    session: AsyncSession,
) -> models.UserProject:
    """Add a user as a member of a project. The owner role may not be assigned here."""
    if role == ProjectRole.owner:
        raise ForbiddenError("The owner role cannot be assigned via member management")

    user = await user_service.get_user_by_email(email, session)

    if project.user_id == user.id:
        raise ConflictError("User is already the owner of this project")

    existing = await session.get(models.UserProject, (user.id, project.id))
    if existing:
        raise ConflictError("User is already a member of this project")

    membership = models.UserProject(
        user_id=user.id, project_id=project.id, role=role, user=user
    )
    session.add(membership)
    await session.commit()
    await session.refresh(membership)

    logger.info(
        "Member added (user_id: %s, project_id: %s, role: %s)",
        user.id,
        project.id,
        role,
    )
    return membership


async def list_members(
    project_id: uuid.UUID,
    session: AsyncSession,
    pagination: schemas.PaginationParams,
) -> schemas.PaginatedResult[models.UserProject]:
    """Return members of a project with total count."""

    total = await session.scalar(
        select(func.count(models.UserProject.user_id)).where(
            models.UserProject.project_id == project_id
        )
    )

    items = (
        await session.scalars(
            select(models.UserProject)
            .where(models.UserProject.project_id == project_id)
            .options(selectinload(models.UserProject.user))
            .offset(pagination.offset)
            .limit(pagination.page_size)
        )
    ).all()

    return schemas.PaginatedResult(items=items, total=total, pagination=pagination)


async def remove_member(
    project: models.Project,
    user_id: uuid.UUID,
    session: AsyncSession,
) -> None:
    """Remove a member from a project. The owner cannot be removed."""
    if project.user_id == user_id:
        raise ForbiddenError("The project owner cannot be removed")

    membership = await session.get(models.UserProject, (user_id, project.id))
    if not membership:
        raise NotFoundError("Member not found")

    await session.delete(membership)
    await session.commit()
    logger.info("Member removed (user_id: %s, project_id: %s)", user_id, project.id)


async def update_member_role(
    project: models.Project,
    user_id: uuid.UUID,
    role: ProjectRole,
    session: AsyncSession,
) -> models.UserProject:
    """Change a member's role. The owner's role cannot be changed."""
    if project.user_id == user_id:
        raise ForbiddenError("The project owner's role cannot be changed")
    if role == ProjectRole.owner:
        raise ForbiddenError("The owner role cannot be assigned via member management")

    membership = await session.get(models.UserProject, (user_id, project.id))
    if not membership:
        raise NotFoundError("Member not found")

    membership.role = role
    await session.commit()
    await session.refresh(membership, attribute_names=["user"])

    logger.info(
        "Member role updated (user_id: %s, project_id: %s, role: %s)",
        user_id,
        project.id,
        role,
    )
    return membership
