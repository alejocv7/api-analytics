from unittest.mock import AsyncMock, patch

import pytest

from app import models, schemas
from app.core.exceptions import (
    BadRequestError,
    BearerAuthenticationError,
    RateLimitError,
)
from app.services import auth_service
from tests.fakes import FakeAsyncRedis

pytestmark = pytest.mark.asyncio


async def test_register_duplicate_email():
    session = AsyncMock()
    # Need a strong password for zxcvbn
    strong_password = "CorrectHorseBatteryStaple123!"
    user_in = schemas.UserCreate(
        email="test@example.com", password=strong_password, full_name="Test"
    )

    with patch(
        "app.services.user_service.get_user_by_email", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = models.User(id=1, email="test@example.com")

        with pytest.raises(BadRequestError) as exc:
            await auth_service.register(user_in, session)
        assert "Email already registered" in str(exc.value)


async def test_authenticate_user_not_found():
    session = AsyncMock()
    with patch(
        "app.services.user_service.get_user_by_email", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = None

        with pytest.raises(BearerAuthenticationError) as exc:
            await auth_service.authenticate_user("none@example.com", "pass", session)
        assert "Incorrect email or password" in str(exc.value)


async def test_authenticate_user_wrong_password():
    session = AsyncMock()
    user = models.User(id=1, email="test@example.com", hashed_password="hashed")
    with patch(
        "app.services.user_service.get_user_by_email", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = user
        with patch("app.core.security.verify_password") as mock_verify:
            mock_verify.return_value = (False, None)

            with pytest.raises(BearerAuthenticationError):
                await auth_service.authenticate_user(
                    "test@example.com", "wrong", session
                )


async def test_authenticate_user_rehashes_password_when_needed():
    """
    When verify_password signals that the hash needs updating, the new hash
    is persisted and the user is returned.
    """
    session = AsyncMock()
    user = models.User(
        id=1, email="test@example.com", hashed_password="old_hash", is_active=True
    )
    with (
        patch(
            "app.services.user_service.get_user_by_email",
            new_callable=AsyncMock,
            return_value=user,
        ),
        patch(
            "app.core.security.verify_password",
            return_value=(True, "new_hash"),
        ),
    ):
        result = await auth_service.authenticate_user(
            "test@example.com", "correct_password", session
        )

    assert user.hashed_password == "new_hash"
    session.add.assert_called_once_with(user)
    session.commit.assert_called_once()
    assert result is user


# --------------- Refresh token rotation ----------------


async def test_refresh_user_token_rotates_refresh_version():
    """refresh_user_token increments token version and returns a new token pair."""
    session = AsyncMock()
    user = models.User(id=1, is_active=True, refresh_token_version=2)
    session.scalar.return_value = user

    with patch(
        "app.core.security.decode_refresh_token",
        return_value=schemas.RefreshTokenData(user_id=1, token_version=2),
    ):
        result = await auth_service.refresh_user_token("valid.refresh.token", session)

    assert result.access_token
    assert result.refresh_token
    assert user.refresh_token_version == 3
    session.add.assert_called_once_with(user)
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(user)


async def test_refresh_user_token_rejects_replayed_token():
    """refresh_user_token rejects old refresh tokens after rotation."""
    session = AsyncMock()
    user = models.User(id=1, is_active=True, refresh_token_version=3)
    session.scalar.return_value = user

    with (
        patch(
            "app.core.security.decode_refresh_token",
            return_value=schemas.RefreshTokenData(user_id=1, token_version=2),
        ),
        pytest.raises(BearerAuthenticationError),
    ):
        await auth_service.refresh_user_token("replayed.refresh.token", session)

    session.commit.assert_not_called()


# --------------- Account lockout ----------------


async def test_check_login_locked_passes_when_no_attempts():
    """No prior failures means the account is not locked."""
    redis = FakeAsyncRedis()
    # Should not raise
    await auth_service.check_login_locked("user@example.com", redis)  # type: ignore[arg-type]


async def test_check_login_locked_raises_after_max_attempts():
    """check_login_locked raises RateLimitError once the limit is reached."""
    from app.core.config import settings

    redis = FakeAsyncRedis()
    key = "login_attempts:user@example.com"
    redis._data[key] = settings.LOGIN_MAX_ATTEMPTS

    with pytest.raises(RateLimitError) as exc:
        await auth_service.check_login_locked("user@example.com", redis)  # type: ignore[arg-type]
    assert "locked" in str(exc.value).lower()


async def test_record_failed_login_increments():
    """record_failed_login increments the counter each call."""
    redis = FakeAsyncRedis()

    await auth_service.record_failed_login("user@example.com", redis)  # type: ignore[arg-type]
    await auth_service.record_failed_login("user@example.com", redis)  # type: ignore[arg-type]

    key = "login_attempts:user@example.com"
    assert redis._data[key] == 2


async def test_record_failed_login_sets_expiry_only_on_first():
    """expire() is called only when the counter transitions from 0 to 1."""
    redis = FakeAsyncRedis()
    expire_calls: list[tuple[str, int]] = []

    original_expire = redis.expire

    async def tracking_expire(key: str, seconds: int) -> bool:
        expire_calls.append((key, seconds))
        return await original_expire(key, seconds)

    redis.expire = tracking_expire  # type: ignore[method-assign]

    await auth_service.record_failed_login("user@example.com", redis)  # type: ignore[arg-type]
    await auth_service.record_failed_login("user@example.com", redis)  # type: ignore[arg-type]

    assert len(expire_calls) == 1


async def test_reset_login_attempts_clears_counter():
    """reset_login_attempts removes the key from the store."""
    redis = FakeAsyncRedis()
    redis._data["login_attempts:user@example.com"] = 3

    await auth_service.reset_login_attempts("user@example.com", redis)  # type: ignore[arg-type]

    assert "login_attempts:user@example.com" not in redis._data
