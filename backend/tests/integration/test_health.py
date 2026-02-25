import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_health_endpoint(client: AsyncClient, monkeypatch):
    import app.health

    async def mock_is_db_connected():
        return True

    async def mock_is_redis_connected():
        return True

    monkeypatch.setattr(app.health, "is_db_connected", mock_is_db_connected)
    monkeypatch.setattr(
        "app.health.redis_manager.is_connected", mock_is_redis_connected
    )

    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["components"]["database"] == "healthy"
    assert data["components"]["redis"] == "healthy"
    assert "version" in data
    assert "timestamp" in data
    assert "environment" in data
