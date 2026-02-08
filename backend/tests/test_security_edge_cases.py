from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import AsyncClient

from app.core.config import settings
from tests.factories import create_api_key

# --- JWT Edge Cases ---


@pytest.mark.asyncio
async def test_expired_jwt_token(client: AsyncClient, test_user):
    """Test using an expired JWT token."""
    # Create a token that expired 1 minute ago manually
    payload = {
        "sub": str(test_user.id),
        "email": test_user.email,
        "exp": datetime.now(UTC) - timedelta(minutes=1),
    }
    expired_token = jwt.encode(
        payload, settings.SECURITY_KEY, algorithm=settings.SECURITY_ALGORITHM
    )

    response = await client.get(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_invalid_jwt_signature(client: AsyncClient, test_user):
    """Test using a JWT with invalid signature (different key)."""
    payload = {
        "sub": str(test_user.id),
        "email": test_user.email,
        "exp": datetime.now(UTC) + timedelta(minutes=15),
    }
    # Sign with a different key
    fake_token = jwt.encode(
        payload, "wrong-secret-key", algorithm=settings.SECURITY_ALGORITHM
    )

    response = await client.get(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {fake_token}"},
    )
    assert response.status_code == 403


# --- API Key Edge Cases ---


@pytest.mark.asyncio
async def test_api_key_expired(client: AsyncClient, project, db_session):
    """Test using an expired API key."""
    # Create expired key
    expired_at = datetime.now(UTC) - timedelta(days=1)
    _, plain_key = await create_api_key(
        db_session, project=project, expires_at=expired_at
    )

    # Try to track metric
    response = await client.post(
        "/api/v1/track/",
        headers={"X-API-Key": plain_key},
        json={
            "url_path": "/test",
            "method": "GET",
            "status_code": 200,
            "response_time_ms": 100,
        },
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["error"]


@pytest.mark.asyncio
async def test_api_key_inactive(client: AsyncClient, project, db_session):
    """Test using a disabled/inactive API key."""
    _, plain_key = await create_api_key(db_session, project=project, is_active=False)

    response = await client.post(
        "/api/v1/track/",
        headers={"X-API-Key": plain_key},
        json={
            "url_path": "/test",
            "method": "GET",
            "status_code": 200,
            "response_time_ms": 100,
        },
    )
    assert response.status_code == 401
