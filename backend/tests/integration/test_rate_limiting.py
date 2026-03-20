"""Integration tests for rate limiting enforcement."""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_global_rate_limit_exceeded(client: AsyncClient):
    """Test that global rate limit returns 429 after exceeding limit."""
    # The global limit is 120/minute, but we'll test a smaller endpoint
    # Auth register is 5/minute, easier to test
    responses = []
    for _ in range(6):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"test{_}@example.com",
                "password": "StrongPassword123!",
                "full_name": "Test User",
            },
        )
        responses.append(response)

    # First 5 should succeed or fail for other reasons (not rate limit)
    # 6th should be rate limited
    last_response = responses[-1]
    assert last_response.status_code == 429


async def test_rate_limit_response_format(client: AsyncClient):
    """Test that 429 response has correct format and headers."""
    # Trigger rate limit on auth register (5/minute)
    for _ in range(6):
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": f"ratelimit{_}@example.com",
                "password": "StrongPassword123!",
                "full_name": "Test User",
            },
        )

    # Last response should be 429
    assert response.status_code == 429

    # Check response body
    data = response.json()
    assert "error" in data
    assert data["error"] == "Rate limit exceeded"
    assert "details" in data
    assert "request_id" in data

    # Check Retry-After header
    assert "retry-after" in response.headers


async def test_per_user_rate_limit_isolation(
    client: AsyncClient, db_session, auth_cookies
):
    """Test that per-user rate limits only affect the specific user."""
    from tests.factories import create_user

    # Create a second user
    user2 = await create_user(db_session, email="user2@example.com")
    from app.services import auth_service

    token_resp2 = auth_service.create_user_token(user2)
    auth_cookies2 = {"access_token": token_resp2.access_token}

    # User 1 creates projects up to rate limit (20/minute)
    user1_responses = []
    for i in range(21):
        response = await client.post(
            "/api/v1/projects/",
            json={"name": f"User1 Project {i}"},
            cookies=auth_cookies,
        )
        user1_responses.append(response)

    # User 1's last request should be rate limited
    assert user1_responses[-1].status_code == 429

    # User 2 should still be able to create a project
    response = await client.post(
        "/api/v1/projects/",
        json={"name": "User2 Project"},
        cookies=auth_cookies2,
    )
    # Should not be rate limited (could be 201 or other error, but not 429)
    assert response.status_code != 429


async def test_auth_rate_limiting_by_ip(client: AsyncClient):
    """Test that auth endpoints are rate limited by IP."""
    # Login endpoint is 10/minute.
    # Must use OAuth2 form data (not JSON) so requests reach the rate limiter.
    responses = []
    for _ in range(11):
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "wrong"},
        )
        responses.append(response)

    # Last response should be rate limited
    assert responses[-1].status_code == 429


async def test_metrics_endpoints_are_rate_limited(
    client: AsyncClient, auth_cookies, project
):
    """Test that metrics endpoints have rate limiting applied."""
    # Metrics read endpoints should have DATA_READ limit (60/minute)
    responses = []
    for _ in range(61):
        response = await client.get(
            f"/api/v1/projects/{project.project_key}/metrics/",
            cookies=auth_cookies,
        )
        responses.append(response)

    # Last response should be rate limited
    assert responses[-1].status_code == 429
