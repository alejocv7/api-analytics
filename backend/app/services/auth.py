from app import models, schemas
from app.core import security
from app.dependencies import SessionDep
from app.services.users import get_user_by_email
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


def register(user: schemas.UserCreate, session: Session) -> models.User:
    if get_user_by_email(user.email, session):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    hashed_password = security.hash_password(user.password)
    new_user = models.User(
        email=user.email, hashed_password=hashed_password, full_name=user.full_name
    )

    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return new_user


def create_user_token(
    user_login: schemas.LoginRequest, session: Session
) -> schemas.TokenResponse:
    user = authenticate_user(
        user_login.email, user_login.password.get_secret_value(), session
    )
    token_data = schemas.TokenData(user_id=user.id, email=user.email)
    return schemas.TokenResponse(access_token=security.create_access_token(token_data))


# Dummy hash to use for timing attack prevention when user is not found
# This is an Argon2 hash of a random password, used to ensure constant-time comparison
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


def authenticate_user(email: str, password: str, session: SessionDep) -> models.User:
    user = get_user_by_email(email, session)
    if not user or not user.is_active:
        # Prevent timing attacks by running password verification even when user doesn't exist
        # This ensures the response time is similar whether or not the email exists
        security.verify_password(password, DUMMY_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    success, updated_hash = security.verify_password(password, user.hashed_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if updated_hash:
        user.hashed_password = updated_hash
        session.add(user)
        session.commit()
        session.refresh(user)
    return user
