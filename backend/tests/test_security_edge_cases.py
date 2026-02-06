from datetime import datetime, timedelta, timezone

import jwt
import pytest
from app.core.config import settings
from httpx import AsyncClient
from tests.factories import create_api_key

# --- JWT Edge Cases ---


@pytest.mark.asyncio
async def test_expired_jwt_token(client: AsyncClient, test_user):
    """Test using an expired JWT token."""
    # Create a token that expired 1 minute ago manually
    payload = {
        "sub": str(test_user.id),
        "email": test_user.email,
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
    }
    expired_token = jwt.encode(
        payload, settings.SECURITY_KEY, algorithm=settings.SECURITY_ALGORITHM
    )

    response = await client.get(
        "/api/v1/projects/",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    # Depending on jwt library version and fastAPI-jwt, it might vary, but usually decoding expired raises specific error
    # transformed into 403 or 401. Let's accept both for robustness, or check exception details.
    # In security.py: decode_token raises APIError(403) on InvalidTokenError.
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_invalid_jwt_signature(client: AsyncClient, test_user):
    """Test using a JWT with invalid signature (different key)."""
    payload = {
        "sub": str(test_user.id),
        "email": test_user.email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
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
    expired_at = datetime.now(timezone.utc) - timedelta(days=1)
    api_key, plain_key = await create_api_key(
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
    api_key, plain_key = await create_api_key(
        db_session, project=project, is_active=False
    )

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
