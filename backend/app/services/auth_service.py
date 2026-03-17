import logging
import uuid

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.core import security, utils
from app.core.config import settings
from app.core.exceptions import (
    BadRequestError,
    BearerAuthenticationError,
    RateLimitError,
)
from app.services import user_service

logger = logging.getLogger(__name__)


async def register(user: schemas.UserCreate, session: AsyncSession) -> models.User:
    logger.info("Registration attempt")
    if await user_service.find_user_by_email(user.email, session):
        logger.warning(
            "Registration failed: Email already registered: %s",
            utils.mask_email(user.email),
        )
        raise BadRequestError("Registration failed")

    hashed_password = security.hash_password(user.password.get_secret_value())
    new_user = models.User(
        email=user.email, hashed_password=hashed_password, full_name=user.full_name
    )

    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)

    logger.info("Registration successful (user_id: %s)", new_user.id)
    return new_user


def create_user_token(user: models.User) -> schemas.TokenResponse:
    token_data = schemas.TokenData(user_id=user.id)
    return schemas.TokenResponse(
        access_token=security.create_access_token(token_data),
        refresh_token=security.create_refresh_token(
            user.id, user.refresh_token_version
        ),
    )


async def refresh_user_token(
    refresh_token: str, session: AsyncSession
) -> schemas.TokenResponse:
    """Issue a new access+refresh token pair from a valid refresh token."""
    token_data = security.decode_refresh_token(refresh_token)
    user = await session.scalar(
        select(models.User)
        .where(models.User.id == token_data.user_id)
        .with_for_update()
    )

    if (
        user is None
        or not user.is_active
        or user.refresh_token_version != token_data.token_version
    ):
        raise BearerAuthenticationError("Invalid authentication credentials")

    user.refresh_token_version += 1
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return create_user_token(user)


async def logout(user_id: uuid.UUID, session: AsyncSession) -> None:
    """Invalidate all refresh tokens for the user by incrementing version."""
    user = await session.scalar(
        select(models.User).where(models.User.id == user_id).with_for_update()
    )
    if user:
        user.refresh_token_version += 1
        session.add(user)
        await session.commit()


async def authenticate_user(
    email: str, password: str, session: AsyncSession
) -> models.User:
    logger.info("Authentication attempt")
    user = await user_service.find_user_by_email(email, session)
    if not user or not user.is_active:
        # Prevent timing attacks by verifying password even when user doesn't exist.
        # This ensures the response time is similar whether or not the email exists.
        security.verify_password(password, settings.SECURITY_DUMMY_HASH)
        logger.warning(
            "Authentication failed: User not found or inactive: %s",
            utils.mask_email(email),
        )
        raise BearerAuthenticationError("Incorrect email or password")

    success, updated_hash = security.verify_password(password, user.hashed_password)
    if not success:
        logger.warning(
            "Authentication failed: Incorrect password for email: %s",
            utils.mask_email(email),
        )
        raise BearerAuthenticationError("Incorrect email or password")

    if updated_hash:
        user.hashed_password = updated_hash
        session.add(user)
        await session.commit()
        await session.refresh(user)

    logger.info("Authentication successful (user_id: %s)", user.id)
    return user


# --------------- Account lockout ----------------


def _login_attempts_key(ip: str, email: str) -> str:
    return f"login_attempts:{ip}:{email}"


async def check_login_locked(ip: str, email: str, redis_client: redis.Redis) -> None:
    """Raise RateLimitError if the account is temporarily locked."""
    value = await redis_client.get(_login_attempts_key(ip, email))
    attempts = int(value) if value else 0
    if attempts >= settings.LOGIN_MAX_ATTEMPTS:
        raise RateLimitError(
            "Account temporarily locked due to too many failed login attempts. "
            "Try again later."
        )


async def record_failed_login(ip: str, email: str, redis_client: redis.Redis) -> None:
    """Increment the failed login counter. Sets expiry on first failure."""
    key = _login_attempts_key(ip, email)
    attempts = await redis_client.incr(key)
    if attempts == 1:
        await redis_client.expire(key, settings.LOGIN_LOCKOUT_WINDOW_SECONDS)


async def reset_login_attempts(email: str, ip: str, redis_client: redis.Redis) -> None:
    """Clear the failed login counter on successful authentication."""
    await redis_client.delete(_login_attempts_key(ip, email))
