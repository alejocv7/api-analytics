import pytest
from httpx import AsyncClient

from tests.factories import create_user

pytestmark = pytest.mark.asyncio


async def test_security_headers(client: AsyncClient):
    """Test that security headers are present in responses."""
    response = await client.get("/")
    assert response.status_code == 200

    # Check for security headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Content-Security-Policy"] == "frame-ancestors 'none';"
    assert "Strict-Transport-Security" not in response.headers

    # Headers we removed as they are not needed for API
    assert "Referrer-Policy" not in response.headers
    assert "Permissions-Policy" not in response.headers


async def test_cors_headers(client: AsyncClient):
    """Test that CORS headers are present when Origin is provided."""
    headers = {"Origin": "http://localhost:3000"}
    response = await client.options("/", headers=headers)

    # If CORS is enabled, it should respond with appropriate headers
    if response.status_code == 200:
        assert "access-control-allow-origin" in response.headers
        assert (
            response.headers["access-control-allow-origin"] == "*"
            or response.headers["access-control-allow-origin"]
            == "http://localhost:3000"
        )


async def test_cors_preflight_headers_on_add_member(
    client: AsyncClient, auth_cookies, project, db_session
):
    """Preflight responses for member creation include the expected CORS headers."""
    await create_user(db_session, email="cors-member@example.com")

    response = await client.options(
        f"/api/v1/projects/{project.project_key}/members",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
        cookies=auth_cookies,
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "POST" in response.headers["access-control-allow-methods"]


async def test_cors_headers_on_add_member_response(
    client: AsyncClient, auth_cookies, project, db_session
):
    """Successful member creation keeps CORS headers on the actual response."""
    new_user = await create_user(db_session, email="cors-response@example.com")

    response = await client.post(
        f"/api/v1/projects/{project.project_key}/members",
        headers={"Origin": "http://localhost:3000"},
        cookies=auth_cookies,
        json={"email": new_user.email, "role": "viewer"},
    )

    assert response.status_code == 201
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


async def test_cors_headers_on_trusted_host_rejection(client: AsyncClient):
    """CORS still applies when outer middleware rejects the request."""
    response = await client.get(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Host": "malicious.example",
        },
    )

    assert response.status_code == 400
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
