import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.core import security
from app.core.config import settings
from app.core.exceptions import BadRequestError, BearerAuthenticationError
from app.services import user_service

logger = logging.getLogger(__name__)


async def register(user: schemas.UserCreate, session: AsyncSession) -> models.User:
    logger.info("Registration attempt for email: %s", user.email)
    if await user_service.get_user_by_email(user.email, session):
        logger.warning("Registration failed: Email already registered: %s", user.email)
        raise BadRequestError("Email already registered")

    hashed_password = security.hash_password(user.password.get_secret_value())
    new_user = models.User(
        email=user.email, hashed_password=hashed_password, full_name=user.full_name
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    logger.info(
        "Registration successful for email: %s (user_id: %s)", user.email, new_user.id
    )
    return new_user


def create_user_token(user: models.User) -> schemas.TokenResponse:
    token_data = schemas.TokenData(user_id=user.id, email=user.email)
    return schemas.TokenResponse(access_token=security.create_access_token(token_data))


async def authenticate_user(
    email: str, password: str, session: AsyncSession
) -> models.User:
    logger.info("Authentication attempt for email: %s", email)
    user = await user_service.get_user_by_email(email, session)
    if not user or not user.is_active:
        # Prevent timing attacks by verifying password even when user doesn't exist.
        # This ensures the response time is similar whether or not the email exists.
        security.verify_password(password, settings.SECURITY_DUMMY_HASH)
        logger.warning("Authentication failed: User not found or inactive: %s", email)
        raise BearerAuthenticationError("Incorrect email or password")

    success, updated_hash = security.verify_password(password, user.hashed_password)
    if not success:
        logger.warning("Authentication failed: Incorrect password for email: %s", email)
        raise BearerAuthenticationError("Incorrect email or password")

    if updated_hash:
        user.hashed_password = updated_hash
        session.add(user)
        await session.commit()
        await session.refresh(user)

    logger.info("Authentication successful for email: %s (user_id: %s)", email, user.id)
    return user
