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
    assert (
        "id" not in data
    )  # UserResponse shouldn't have id usually, but let's check what it has

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
    assert "Email already registered" in response.json()["error"]


async def test_login_success(client: AsyncClient, test_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "Password123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_invalid_credentials(client: AsyncClient, test_user):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": test_user.email, "password": "WrongPassword"},
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["error"]
