import secrets
from typing import Sequence

from app import models, schemas
from app.core.config import settings
from fastapi import HTTPException, status
from sqlalchemy import select, true
from sqlalchemy.orm import Session


def create_user_project(
    user_id: int,
    project_in: schemas.ProjectCreate,
    session: Session,
):
    project_key = _generate_project_key(project_in.name)
    if get_user_project_by_key(project_key, user_id, session):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Project already exists",
        )

    project = models.Project(
        name=project_in.name,
        description=project_in.description,
        project_key=project_key,
        user_id=user_id,
    )

    session.add(project)
    session.commit()
    session.refresh(project)

    return project


def get_user_project_by_key(project_key: str, user_id: int, session: Session):
    statement = select(models.Project).where(
        models.Project.user_id == user_id,
        models.Project.project_key == project_key,
    )
    return session.scalars(statement).one_or_none()


def get_user_projects(
    user_id: int,
    session: Session,
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

    return session.scalars(statement).all()


def update_user_project(
    user_id: int,
    project_key: str,
    update_data: schemas.ProjectUpdate,
    session: Session,
):
    project = get_user_project_by_key(project_key, user_id, session)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    # Check if the new name is already in use
    if update_data.name != project.name:
        stmt = select(models.Project).where(
            models.Project.user_id == user_id,
            models.Project.name == update_data.name,
            models.Project.id != project.id,
        )
        if session.scalars(stmt).one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Project name already in use",
            )

    update_dict = update_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(project, key, value)

    session.add(project)
    session.commit()
    session.refresh(project)

    return project


def delete_user_project(
    user_id: int,
    project_key: str,
    session: Session,
):
    project = get_user_project_by_key(project_key, user_id, session)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    session.delete(project)
    session.commit()


def _generate_project_key(name: str) -> str:
    """Generate a project key for a project."""
    return (
        name.lower().replace(" ", "-")
        + "-"
        + secrets.token_hex(settings.PROJECT_SUFFIX_LENGTH)
    )
