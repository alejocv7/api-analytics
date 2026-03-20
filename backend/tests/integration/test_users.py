import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_get_me_returns_current_user(
    client: AsyncClient, auth_cookies, test_user
):
    response = await client.get("/api/v1/users/me", cookies=auth_cookies)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name
    assert data["is_active"] is True


async def test_get_me_requires_authentication(client: AsyncClient):
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


async def test_get_me_with_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/v1/users/me",
        cookies={"access_token": "this.is.not.a.valid.jwt"},
    )
    assert response.status_code == 401
