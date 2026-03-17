import pytest
from httpx import AsyncClient
from sqlalchemy import select

pytestmark = pytest.mark.asyncio


async def test_register_user(client: AsyncClient, db_session):
    from app import models

    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data  # UserResponse includes id as UUID

    # Verify in DB
    result = await db_session.execute(
        select(models.User).where(models.User.email == "newuser@example.com")
    )
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.full_name == "New User"


async def test_register_duplicate_email(client: AsyncClient, test_user):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user.email,
            "password": "AnotherPassword123!",
            "full_name": "Duplicate",
        },
    )
    assert response.status_code == 400
    assert "Registration failed" in response.json()["error"]


async def test_login_success(client: AsyncClient, test_user):
    # Login uses OAuth2PasswordRequestForm: form data with `username` field
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "Password123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_invalid_credentials(client: AsyncClient, test_user):
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "WrongPassword"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["error"]


# --------------- Refresh token ----------------


async def test_refresh_token(client: AsyncClient, test_user):
    """A valid refresh token exchanges for a new access+refresh token pair."""
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "Password123!"},
    )
    assert login.status_code == 200
    refresh_token = login.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_refresh_token_invalid(client: AsyncClient):
    """An invalid refresh token returns 401."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "not.a.valid.token"},
    )
    assert response.status_code == 401


async def test_refresh_token_with_access_token(client: AsyncClient, test_user):
    """Using an access token as a refresh token must be rejected."""
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "Password123!"},
    )
    access_token = login.json()["access_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert response.status_code == 401


async def test_refresh_token_cannot_be_reused(client: AsyncClient, test_user):
    """A refresh token is invalid after it has been exchanged once."""
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "Password123!"},
    )
    refresh_token = login.json()["refresh_token"]

    first_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert first_refresh.status_code == 200

    replay = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert replay.status_code == 401


async def test_new_access_token_from_refresh_is_usable(client: AsyncClient, test_user):
    """An access token obtained via refresh must authenticate successfully."""
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "Password123!"},
    )
    refresh_token = login.json()["refresh_token"]

    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    new_access_token = refresh_resp.json()["access_token"]

    me_resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {new_access_token}"},
    )
    assert me_resp.status_code == 200


# --------------- Account lockout ----------------


async def test_failed_login_increments_counter(
    client: AsyncClient, test_user, async_redis_client
):
    """Each failed login attempt increments the Redis counter."""
    await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "WrongPassword"},
    )
    key = f"login_attempts:127.0.0.1:{test_user.email}"
    assert await async_redis_client.get(key) == "1"


async def test_account_locked_after_max_attempts(client: AsyncClient, test_user):
    """The account is locked after LOGIN_MAX_ATTEMPTS consecutive failures."""
    from app.core.config import settings

    for _ in range(settings.LOGIN_MAX_ATTEMPTS):
        await client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": "WrongPassword"},
        )

    # Next attempt (even with correct password) must be rejected with 429
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "Password123!"},
    )
    assert response.status_code == 429
    assert "locked" in response.json()["error"].lower()


async def test_successful_login_resets_counter(
    client: AsyncClient, test_user, async_redis_client
):
    """A successful login clears the failed-attempt counter."""
    for _ in range(2):
        await client.post(
            "/api/v1/auth/login",
            data={"username": test_user.email, "password": "WrongPassword"},
        )

    key = f"login_attempts:127.0.0.1:{test_user.email}"
    assert await async_redis_client.get(key) == "2"

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "Password123!"},
    )
    assert response.status_code == 200
    assert await async_redis_client.get(key) is None


async def test_inactive_user_cannot_login(client: AsyncClient, test_user, db_session):
    test_user.is_active = False
    db_session.add(test_user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "Password123!"},
    )
    # The requirement says get_current_user raises Forbidden for inactive,
    # but authenticate_user (login) also checks for active.
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["error"]


async def test_inactive_user_cannot_access_protected(
    client: AsyncClient, test_user, db_session
):
    from app.services import auth_service

    token = auth_service.create_user_token(test_user)

    test_user.is_active = False
    db_session.add(test_user)
    await db_session.commit()

    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token.access_token}"},
    )
    assert response.status_code == 403
    assert "Inactive user" in response.json()["error"]


async def test_logout(client: AsyncClient, test_user):
    # 1. Login to get tokens
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": test_user.email, "password": "Password123!"},
    )
    tokens = login.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # 2. Verify access works (stateless)
    me = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me.status_code == 200

    # 3. Logout
    logout_resp = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_resp.status_code == 204

    # 4. Verify refresh token is revoked
    refresh_fail = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_fail.status_code == 401
