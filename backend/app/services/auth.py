from app import models, schemas
from app.core import security
from app.core.config import settings
from app.core.exceptions import APIError
from app.services.users import get_user_by_email
from fastapi import status
from sqlalchemy.orm import Session


def register(user: schemas.UserCreate, session: Session) -> models.User:
    if get_user_by_email(user.email, session):
        raise APIError(
            status_code=status.HTTP_400_BAD_REQUEST, message="Email already registered"
        )

    hashed_password = security.hash_password(user.password.get_secret_value())
    new_user = models.User(
        email=user.email, hashed_password=hashed_password, full_name=user.full_name
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return new_user


def create_user_token(user: models.User) -> schemas.TokenResponse:
    token_data = schemas.TokenData(user_id=user.id, email=user.email)
    return schemas.TokenResponse(access_token=security.create_access_token(token_data))


def authenticate_user(email: str, password: str, session: Session) -> models.User:
    user = get_user_by_email(email, session)
    if not user or not user.is_active:
        # Prevent timing attacks by running password verification even when user doesn't exist
        # This ensures the response time is similar whether or not the email exists
        # This ensures the response time is similar whether or not the email exists
        security.verify_password(password, settings.SECURITY_DUMMY_HASH)
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Incorrect email or password",
            details={"headers": {"WWW-Authenticate": "Bearer"}},
        )

    success, updated_hash = security.verify_password(password, user.hashed_password)
    if not success:
        raise APIError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message="Incorrect email or password",
            details={"headers": {"WWW-Authenticate": "Bearer"}},
        )
    if updated_hash:
        user.hashed_password = updated_hash
        session.add(user)
        session.commit()
        session.refresh(user)
    return user
