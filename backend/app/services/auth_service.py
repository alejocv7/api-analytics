import logging
import uuid

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models, schemas
from app.core import security, utils
from app.core.config import settings
from app.core.enums import AuthSessionClientType
from app.core.exceptions import (
    AuthenticationError,
    BadRequestError,
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


async def create_web_session(
    user: models.User,
    session: AsyncSession,
    *,
    user_agent: str | None = None,
    client_ip: str | None = None,
) -> tuple[models.AuthSession, str]:
    secret = security.generate_session_secret()
    auth_session = models.AuthSession.create_web(
        user_id=user.id,
        session_secret_hash=security.hash_auth_secret(secret),
        user_agent=user_agent,
        ip_hash=security.hash_ip(client_ip),
    )
    session.add(auth_session)
    await session.commit()
    await session.refresh(auth_session)
    return auth_session, secret


async def create_token_session(
    user: models.User,
    session: AsyncSession,
    *,
    user_agent: str | None = None,
    client_ip: str | None = None,
) -> schemas.TokenLoginResponse:
    refresh_secret = security.generate_refresh_secret()
    auth_session = models.AuthSession.create_token(
        user_id=user.id,
        refresh_token_hash=security.hash_auth_secret(refresh_secret),
        user_agent=user_agent,
        ip_hash=security.hash_ip(client_ip),
    )

    session.add(auth_session)
    await session.commit()
    await session.refresh(auth_session)

    token_response = _build_token_response(user, auth_session.id, refresh_secret)
    return schemas.TokenLoginResponse(
        user=schemas.UserResponse.model_validate(user), **token_response.model_dump()
    )


async def get_active_web_session(
    session_secret: str, session: AsyncSession
) -> models.AuthSession:
    auth_session = await session.scalar(
        select(models.AuthSession).where(
            models.AuthSession.session_secret_hash
            == security.hash_auth_secret(session_secret),
            models.AuthSession.client_type == AuthSessionClientType.web,
        )
    )
    if auth_session is None or not auth_session.is_active():
        raise AuthenticationError("Invalid authentication credentials")
    return auth_session


async def refresh_user_token(
    refresh_token: str, session: AsyncSession
) -> schemas.TokenRefreshResponse:
    token_data = security.decode_refresh_token(refresh_token)
    auth_session = await session.scalar(
        select(models.AuthSession)
        .where(models.AuthSession.id == token_data.session_id)
        .with_for_update()
    )

    if (
        auth_session is None
        or auth_session.client_type != AuthSessionClientType.token
        or not auth_session.is_active()
    ):
        raise AuthenticationError("Invalid authentication credentials")

    if not security.compare_auth_secret(
        token_data.secret, auth_session.refresh_token_hash
    ):
        auth_session.revoke()
        session.add(auth_session)
        await session.commit()
        raise AuthenticationError("Invalid authentication credentials")

    user = await session.get(models.User, auth_session.user_id)
    if user is None or not user.is_active:
        auth_session.revoke()
        session.add(auth_session)
        await session.commit()
        raise AuthenticationError("Invalid authentication credentials")

    refresh_secret = security.generate_refresh_secret()
    auth_session.refresh_token_hash = security.hash_auth_secret(refresh_secret)
    auth_session.record_usage()
    session.add(auth_session)
    await session.commit()
    await session.refresh(auth_session)

    return _build_token_response(user, auth_session.id, refresh_secret)


async def revoke_session(session_id: uuid.UUID, session: AsyncSession) -> None:
    auth_session = await session.scalar(
        select(models.AuthSession)
        .where(models.AuthSession.id == session_id)
        .with_for_update()
    )
    if auth_session is None or not auth_session.is_active():
        return

    auth_session.revoke()
    session.add(auth_session)
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
        raise AuthenticationError("Incorrect email or password")

    success, updated_hash = security.verify_password(password, user.hashed_password)
    if not success:
        logger.warning(
            "Authentication failed: Incorrect password for email: %s",
            utils.mask_email(email),
        )
        raise AuthenticationError("Incorrect email or password")

    if updated_hash:
        user.hashed_password = updated_hash
        session.add(user)
        await session.commit()
        await session.refresh(user)

    logger.info("Authentication successful (user_id: %s)", user.id)
    return user


# --------------- Account lockout ----------------


async def authenticate_with_lockout(
    email: str,
    password: str,
    client_ip: str,
    redis_client: redis.Redis,
    session: AsyncSession,
) -> models.User:
    await check_login_locked(client_ip, email, redis_client)
    try:
        user = await authenticate_user(email, password, session)
    except AuthenticationError:
        await record_failed_login(client_ip, email, redis_client)
        raise

    await reset_login_attempts(email, client_ip, redis_client)
    return user


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


# --------------- Helpers ----------------


def _build_token_response(
    user: models.User,
    session_id: uuid.UUID,
    refresh_secret: str,
) -> schemas.TokenRefreshResponse:
    token_data = schemas.TokenData(user_id=user.id, session_id=session_id)
    return schemas.TokenRefreshResponse(
        access_token=security.create_access_token(token_data),
        refresh_token=security.create_refresh_token(session_id, refresh_secret),
        expires_in=settings.SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
