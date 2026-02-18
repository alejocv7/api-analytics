import logging
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.user_project import ProjectRole

logger = logging.getLogger(__name__)


async def add_member(
    project: models.Project,
    user_id: int,
    role: ProjectRole,
    session: AsyncSession,
) -> models.UserProject:
    """Add a user as a member of a project. The owner role may not be assigned here."""
    if role == ProjectRole.owner:
        raise ForbiddenError("The owner role cannot be assigned via member management")

    user = await session.get(models.User, user_id)
    if not user:
        raise NotFoundError("User not found")

    if project.user_id == user_id:
        raise ConflictError("User is already the owner of this project")

    existing = await session.get(models.UserProject, (user_id, project.id))
    if existing:
        raise ConflictError("User is already a member of this project")

    membership = models.UserProject(user_id=user_id, project_id=project.id, role=role)
    session.add(membership)
    await session.commit()
    await session.refresh(membership)
    logger.info(
        "Member added (user_id: %s, project_id: %s, role: %s)",
        user_id,
        project.id,
        role,
    )
    return membership


async def list_members(
    project_id: int,
    session: AsyncSession,
    offset: int = 0,
    limit: int = 20,
) -> Sequence[models.UserProject]:
    """Return members of a project (all roles including owner) with pagination."""
    result = await session.scalars(
        select(models.UserProject)
        .where(models.UserProject.project_id == project_id)
        .offset(offset)
        .limit(limit)
    )
    return result.all()


async def count_members(project_id: int, session: AsyncSession) -> int:
    """Return the total number of members in a project."""
    result = await session.scalar(
        select(func.count()).where(models.UserProject.project_id == project_id)
    )
    return result or 0


async def remove_member(
    project: models.Project,
    user_id: int,
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
    user_id: int,
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
    await session.refresh(membership)
    logger.info(
        "Member role updated (user_id: %s, project_id: %s, role: %s)",
        user_id,
        project.id,
        role,
    )
    return membership
