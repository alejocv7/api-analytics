import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio

async def test_security_headers(client: AsyncClient):
    """Test that security headers are present in responses."""
    response = await client.get("/")
    assert response.status_code == 200

    # Check for security headers
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


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
