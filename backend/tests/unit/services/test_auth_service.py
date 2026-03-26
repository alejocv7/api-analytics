import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app import models, schemas
from app.core.exceptions import (
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)
from app.services import auth_service
from tests.fakes import FakeAsyncRedis

pytestmark = pytest.mark.asyncio


async def test_register_duplicate_email():
    session = AsyncMock()
    session.add = MagicMock()
    # Need a strong password for zxcvbn
    strong_password = "CorrectHorseBatteryStaple123!"
    user_in = schemas.UserCreate(
        email="test@example.com", password=strong_password, full_name="Test"
    )

    with patch(
        "app.services.user_service.find_user_by_email", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = models.User(id=1, email="test@example.com")

        with pytest.raises(BadRequestError) as exc:
            await auth_service.register(user_in, session)
        assert "Registration failed" in str(exc.value)


async def test_authenticate_user_not_found():
    session = AsyncMock()
    session.add = MagicMock()
    with patch(
        "app.services.user_service.find_user_by_email", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = None

        with pytest.raises(AuthenticationError) as exc:
            await auth_service.authenticate_user("none@example.com", "pass", session)
        assert "Incorrect email or password" in str(exc.value)


async def test_authenticate_user_wrong_password():
    session = AsyncMock()
    session.add = MagicMock()
    user = models.User(id=1, email="test@example.com", hashed_password="hashed")
    with patch(
        "app.services.user_service.find_user_by_email", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = user
        with patch("app.core.security.verify_password") as mock_verify:
            mock_verify.return_value = (False, None)

            with pytest.raises(AuthenticationError):
                await auth_service.authenticate_user(
                    "test@example.com", "wrong", session
                )


async def test_authenticate_user_rehashes_password_when_needed():
    session = AsyncMock()
    session.add = MagicMock()
    user = models.User(
        id=1, email="test@example.com", hashed_password="old_hash", is_active=True
    )
    with (
        patch(
            "app.services.user_service.find_user_by_email",
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


async def test_refresh_user_token_rotates_refresh_hash():
    """refresh_user_token rotates only the current session's refresh secret."""
    session_id = uuid.uuid4()
    uid = uuid.uuid4()
    session = AsyncMock()
    session.add = MagicMock()
    auth_session = models.AuthSession.create_token(
        user_id=uid,
        refresh_token_hash="old-hash",
    )
    auth_session.id = session_id
    auth_session.expires_at = datetime.now(UTC) + timedelta(days=1)
    user = models.User(id=uid, is_active=True)
    session.scalar.return_value = auth_session
    session.get.return_value = user

    with (
        patch(
            "app.core.security.decode_refresh_token",
            return_value=schemas.RefreshTokenData(
                session_id=session_id, secret="valid-secret"
            ),
        ),
        patch(
            "app.core.security.compare_auth_secret",
            return_value=True,
        ),
        patch(
            "app.core.security.generate_refresh_secret",
            return_value="new-secret",
        ),
        patch(
            "app.core.security.hash_auth_secret",
            return_value="new-hash",
        ),
    ):
        result = await auth_service.refresh_user_token("valid.refresh.token", session)

    assert result.access_token
    assert result.refresh_token
    assert auth_session.refresh_token_hash == "new-hash"
    session.add.assert_called_once_with(auth_session)
    assert session.commit.await_count == 1
    session.refresh.assert_called_once_with(auth_session)


async def test_refresh_user_token_rejects_replayed_token_and_revokes_session():
    """Mismatched refresh secrets revoke the active token session."""
    session_id = uuid.uuid4()
    session = AsyncMock()
    session.add = MagicMock()
    auth_session = models.AuthSession.create_token(
        user_id=uuid.uuid4(),
        refresh_token_hash="current-hash",
    )
    auth_session.id = session_id
    auth_session.expires_at = datetime.now(UTC) + timedelta(days=1)
    session.scalar.return_value = auth_session

    with (
        patch(
            "app.core.security.decode_refresh_token",
            return_value=schemas.RefreshTokenData(
                session_id=session_id, secret="old-secret"
            ),
        ),
        patch(
            "app.core.security.compare_auth_secret",
            return_value=False,
        ),
        pytest.raises(AuthenticationError),
    ):
        await auth_service.refresh_user_token("replayed.refresh.token", session)

    assert auth_session.revoked_at is not None
    assert auth_session.refresh_token_hash is None
    session.commit.assert_called_once()


# --------------- Account lockout ----------------


async def test_check_login_locked_passes_when_no_attempts():
    """No prior failures means the account is not locked."""
    redis = FakeAsyncRedis()
    # Should not raise
    await auth_service.check_login_locked("127.0.0.1", "user@example.com", redis)  # type: ignore[arg-type]


async def test_check_login_locked_raises_after_max_attempts():
    """check_login_locked raises RateLimitError once the limit is reached."""
    from app.core.config import settings

    redis = FakeAsyncRedis()
    key = "login_attempts:127.0.0.1:user@example.com"
    redis._data[key] = settings.LOGIN_MAX_ATTEMPTS

    with pytest.raises(RateLimitError) as exc:
        await auth_service.check_login_locked("127.0.0.1", "user@example.com", redis)  # type: ignore[arg-type]
    assert "locked" in str(exc.value).lower()


async def test_record_failed_login_increments():
    """record_failed_login increments the counter each call."""
    redis = FakeAsyncRedis()

    await auth_service.record_failed_login("127.0.0.1", "user@example.com", redis)  # type: ignore[arg-type]
    await auth_service.record_failed_login("127.0.0.1", "user@example.com", redis)  # type: ignore[arg-type]

    key = "login_attempts:127.0.0.1:user@example.com"
    assert redis._data[key] == 2


async def test_record_failed_login_sets_expiry_only_on_first():
    """expire() is called only when the counter transitions from 0 to 1."""
    redis = FakeAsyncRedis()
    expire_calls: list[tuple[str, int]] = []

    original_expire = redis.expire

    async def tracking_expire(key: str, seconds: int, **kwargs: object) -> bool:
        expire_calls.append((key, seconds))
        return await original_expire(key, seconds, **kwargs)  # type: ignore[arg-type]

    redis.expire = tracking_expire  # type: ignore[assignment]

    await auth_service.record_failed_login("127.0.0.1", "user@example.com", redis)  # type: ignore[arg-type]
    await auth_service.record_failed_login("127.0.0.1", "user@example.com", redis)  # type: ignore[arg-type]

    assert len(expire_calls) == 1


async def test_reset_login_attempts_clears_counter():
    """reset_login_attempts removes the key from the store."""
    redis = FakeAsyncRedis()
    redis._data["login_attempts:127.0.0.1:user@example.com"] = 3

    await auth_service.reset_login_attempts("user@example.com", "127.0.0.1", redis)  # type: ignore[arg-type]

    assert "login_attempts:127.0.0.1:user@example.com" not in redis._data


async def test_authenticate_with_lockout_records_failures_on_bad_credentials():
    redis = FakeAsyncRedis()
    session = AsyncMock()

    with (
        patch(
            "app.services.auth_service.check_login_locked",
            new_callable=AsyncMock,
        ),
        patch(
            "app.services.auth_service.authenticate_user",
            new_callable=AsyncMock,
            side_effect=AuthenticationError("Incorrect email or password"),
        ),
        pytest.raises(AuthenticationError),
    ):
        await auth_service.authenticate_with_lockout(
            "user@example.com",
            "wrong-password",
            "127.0.0.1",
            redis,  # type: ignore[arg-type]
            session,
        )

    assert redis._data["login_attempts:127.0.0.1:user@example.com"] == 1


async def test_authenticate_with_lockout_resets_failures_on_success():
    redis = FakeAsyncRedis()
    redis._data["login_attempts:127.0.0.1:user@example.com"] = 2
    session = AsyncMock()
    user = models.User(id=uuid.uuid4(), email="user@example.com", is_active=True)

    with (
        patch(
            "app.services.auth_service.check_login_locked",
            new_callable=AsyncMock,
        ),
        patch(
            "app.services.auth_service.authenticate_user",
            new_callable=AsyncMock,
            return_value=user,
        ),
    ):
        result = await auth_service.authenticate_with_lockout(
            "user@example.com",
            "correct-password",
            "127.0.0.1",
            redis,  # type: ignore[arg-type]
            session,
        )

    assert result is user
    assert "login_attempts:127.0.0.1:user@example.com" not in redis._data


async def test_auth_session_helpers_create_and_revoke():
    auth_session = models.AuthSession.create_web(
        user_id=uuid.uuid4(),
        session_secret_hash="session-hash",
        user_agent="pytest",
        ip_hash="ip-hash",
    )
    auth_session.expires_at = datetime.now(UTC) + timedelta(days=1)

    assert auth_session.is_active is True
    assert auth_session.session_secret_hash == "session-hash"
    assert auth_session.refresh_token_hash is None

    auth_session.revoke()

    assert auth_session.is_active is False
    assert auth_session.revoked_at is not None
    assert auth_session.session_secret_hash is None
    assert auth_session.refresh_token_hash is None
