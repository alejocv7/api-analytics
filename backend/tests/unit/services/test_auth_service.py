from unittest.mock import AsyncMock, patch

import pytest

from app import models, schemas
from app.core.exceptions import BadRequestError, BearerAuthenticationError
from app.services import auth_service

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
