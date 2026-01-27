from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models
from app.core import config, db, security
from app.core.security import hash_api_key

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{config.settings.API_PREFIX}/login")
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def get_db() -> Generator[Session, None, None]:
    with db.Session() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]


def get_project_id(
    session: SessionDep,
    api_key: str = Security(api_key_header),
) -> int:
    """Validates API key and returns the Project id."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="API key required"
        )

    api_key_obj = session.execute(
        select(models.ApiKey).where(
            models.ApiKey.key_hash == hash_api_key(api_key),
            models.ApiKey.is_active.is_(True),
        )
    ).scalar_one_or_none()

    if not api_key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key"
        )

    return api_key_obj.project_id


ProjectIdDep = Annotated[int, Depends(get_project_id)]


def get_current_user(session: SessionDep, token: TokenDep) -> models.User:
    token_data = security.decode_token(token)
    user = session.get(models.User, token_data.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUserDep = Annotated[models.User, Depends(get_current_user)]
