from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.core import config, db, security
from app.core.exceptions import APIError

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{config.settings.API_PREFIX}/login")
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_db() -> Generator[Session, None, None]:
    with db.Session() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]


def get_project_id_by_api_key(
    session: SessionDep,
    api_key: str = Security(api_key_header),
) -> int:
    """Validates API key and returns the Project id."""
    if not api_key:
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED, message="API key required"
        )

    key_prefix = api_key[: config.settings.API_KEY_LOOKUP_PREFIX_LENGTH]
    api_key_obj = session.scalars(
        select(models.APIKey)
        .join(models.Project)
        .where(
            models.APIKey.key_prefix == key_prefix,
            models.APIKey.is_active.is_(True),
            models.Project.is_active.is_(True),
        )
    ).one_or_none()

    if (
        not api_key_obj
        or not api_key_obj.is_valid
        or not security.compare_api_key(api_key, api_key_obj.key_hash)
    ):
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED, message="Invalid API key"
        )
    return api_key_obj.project_id


ProjectIdDep = Annotated[int, Depends(get_project_id_by_api_key)]


def get_current_user(session: SessionDep, token: TokenDep) -> models.User:
    token_data = security.decode_token(token)
    user = session.get(models.User, token_data.user_id)
    if user is None:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="User not found",
            details={"headers": {"WWW-Authenticate": "Bearer"}},
        )
    if not user.is_active:
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST,
            message="Inactive user",
            details={"headers": {"WWW-Authenticate": "Bearer"}},
        )
    return user


CurrentUserDep = Annotated[models.User, Depends(get_current_user)]


def get_user_project(
    project_key: str,
    user: CurrentUserDep,
    session: SessionDep,
) -> models.Project:
    # Avoid circular import
    from app.services import project_service

    project = project_service.get_user_project_by_key(user.id, project_key, session)
    if not project:
        raise APIError(
            status_code=status.HTTP_404_NOT_FOUND,
            message="Project not found",
        )
    return project


ProjectDep = Annotated[models.Project, Depends(get_user_project)]
