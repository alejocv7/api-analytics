import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app import models
from tests.factories import create_web_auth_cookies

pytestmark = pytest.mark.asyncio


async def test_register_user(client: AsyncClient, db_session):
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
    assert "id" in data

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


async def test_browser_login_success(client: AsyncClient, test_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert "id" in data
    assert "session" in response.cookies


async def test_login_invalid_credentials(client: AsyncClient, test_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "WrongPassword"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["error"]


async def test_browser_session_cookie_authenticates_protected_routes(
    client: AsyncClient, test_user
):
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    assert login.status_code == 200

    me = await client.get("/api/v1/users/me")
    assert me.status_code == 200
    assert me.json()["email"] == test_user.email


async def test_browser_logout_revokes_only_current_session(
    client: AsyncClient, test_user, db_session
):
    current_session = await create_web_auth_cookies(db_session, user=test_user)
    other_session = await create_web_auth_cookies(db_session, user=test_user)

    logout_resp = await client.post("/api/v1/auth/logout", cookies=current_session)
    assert logout_resp.status_code == 204

    failed = await client.get("/api/v1/users/me", cookies=current_session)
    assert failed.status_code == 401

    still_active = await client.get("/api/v1/users/me", cookies=other_session)
    assert still_active.status_code == 200


async def test_inactive_user_cannot_login(client: AsyncClient, test_user, db_session):
    test_user.is_active = False
    db_session.add(test_user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["error"]


async def test_inactive_user_cannot_access_protected(
    client: AsyncClient, test_user, db_session
):
    cookies = await create_web_auth_cookies(db_session, user=test_user)

    test_user.is_active = False
    db_session.add(test_user)
    await db_session.commit()

    response = await client.get("/api/v1/users/me", cookies=cookies)
    assert response.status_code == 403
    assert "Inactive user" in response.json()["error"]


# --------------- Token clients ----------------


async def test_token_login_returns_user_and_tokens(client: AsyncClient, test_user):
    response = await client.post(
        "/api/v1/auth/token/login",
        data={"username": test_user.email, "password": "Password123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == test_user.email
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] > 0
    assert "session" not in response.cookies


async def test_token_access_token_authenticates_protected_endpoint(
    client: AsyncClient, test_user
):
    login = await client.post(
        "/api/v1/auth/token/login",
        data={"username": test_user.email, "password": "Password123!"},
    )
    access_token = login.json()["access_token"]

    me = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == test_user.email


async def test_token_refresh_rotates_only_that_session(client: AsyncClient, test_user):
    session_a = await client.post(
        "/api/v1/auth/token/login",
        data={"username": test_user.email, "password": "Password123!"},
    )
    session_b = await client.post(
        "/api/v1/auth/token/login",
        data={"username": test_user.email, "password": "Password123!"},
    )

    refresh_a = session_a.json()["refresh_token"]
    refresh_b = session_b.json()["refresh_token"]

    rotated = await client.post(
        "/api/v1/auth/token/refresh",
        json={"refresh_token": refresh_a},
    )
    assert rotated.status_code == 200

    unaffected = await client.post(
        "/api/v1/auth/token/refresh",
        json={"refresh_token": refresh_b},
    )
    assert unaffected.status_code == 200


async def test_refresh_token_reuse_revokes_that_specific_session(
    client: AsyncClient, test_user
):
    session_a = await client.post(
        "/api/v1/auth/token/login",
        data={"username": test_user.email, "password": "Password123!"},
    )
    session_b = await client.post(
        "/api/v1/auth/token/login",
        data={"username": test_user.email, "password": "Password123!"},
    )

    refresh_a = session_a.json()["refresh_token"]
    refresh_b = session_b.json()["refresh_token"]

    rotated = await client.post(
        "/api/v1/auth/token/refresh",
        json={"refresh_token": refresh_a},
    )
    assert rotated.status_code == 200
    rotated_refresh_a = rotated.json()["refresh_token"]

    replay = await client.post(
        "/api/v1/auth/token/refresh",
        json={"refresh_token": refresh_a},
    )
    assert replay.status_code == 401

    revoked_session = await client.post(
        "/api/v1/auth/token/refresh",
        json={"refresh_token": rotated_refresh_a},
    )
    assert revoked_session.status_code == 401

    unaffected_session = await client.post(
        "/api/v1/auth/token/refresh",
        json={"refresh_token": refresh_b},
    )
    assert unaffected_session.status_code == 200


async def test_token_logout_invalidates_refresh_token(client: AsyncClient, test_user):
    login = await client.post(
        "/api/v1/auth/token/login",
        data={"username": test_user.email, "password": "Password123!"},
    )
    tokens = login.json()

    logout = await client.post(
        "/api/v1/auth/token/logout",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert logout.status_code == 204

    refresh_fail = await client.post(
        "/api/v1/auth/token/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_fail.status_code == 401


async def test_browser_and_token_sessions_can_coexist(
    client: AsyncClient, test_user, db_session
):
    browser = await create_web_auth_cookies(db_session, user=test_user)
    token_login = await client.post(
        "/api/v1/auth/token/login",
        data={"username": test_user.email, "password": "Password123!"},
    )
    refresh_token = token_login.json()["refresh_token"]

    browser_me = await client.get("/api/v1/users/me", cookies=browser)
    assert browser_me.status_code == 200

    token_refresh = await client.post(
        "/api/v1/auth/token/refresh",
        json={"refresh_token": refresh_token},
    )
    assert token_refresh.status_code == 200


async def test_bearer_takes_precedence_over_bad_session_cookie(
    client: AsyncClient, test_user
):
    login = await client.post(
        "/api/v1/auth/token/login",
        data={"username": test_user.email, "password": "Password123!"},
    )
    access_token = login.json()["access_token"]

    response = await client.get(
        "/api/v1/users/me",
        cookies={"session": "bad-session-cookie"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200


# --------------- Account lockout ----------------


async def test_failed_login_increments_counter(
    client: AsyncClient, test_user, async_redis_client
):
    await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "WrongPassword"},
    )
    key = f"login_attempts:127.0.0.1:{test_user.email}"
    assert await async_redis_client.get(key) == "1"


async def test_account_locked_after_max_attempts(client: AsyncClient, test_user):
    from app.core.config import settings

    for _ in range(settings.LOGIN_MAX_ATTEMPTS):
        await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "WrongPassword"},
        )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    assert response.status_code == 429
    assert "locked" in response.json()["error"].lower()


async def test_successful_login_resets_counter(
    client: AsyncClient, test_user, async_redis_client
):
    for _ in range(2):
        await client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "WrongPassword"},
        )

    key = f"login_attempts:127.0.0.1:{test_user.email}"
    assert await async_redis_client.get(key) == "2"

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    assert response.status_code == 200
    assert await async_redis_client.get(key) is None
