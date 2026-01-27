from app import models
from app.core import security
from app.dependencies import SessionDep, TokenDep
from fastapi import HTTPException, status
from sqlalchemy import select


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


def get_user_by_email(email: str, session: SessionDep) -> models.User | None:
    stmt = select(models.User).where(models.User.email == email)
    return session.execute(stmt).scalar_one_or_none()
