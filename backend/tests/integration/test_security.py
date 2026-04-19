import pytest
from httpx import AsyncClient

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
