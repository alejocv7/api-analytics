import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select

from tests.factories import create_api_key, create_project

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def api_key_and_project(db_session, test_user):
    project = await create_project(
        db_session,
        user=test_user,
        name="Track Project",
        project_key="track-key",
    )
    _, plain_key = await create_api_key(
        db_session,
        project=project,
        name="Track Key",
        plain_key="sk_test_1234567890abcdef",
        is_active=True,
    )
    return plain_key, project


async def test_track_metric_success(
    client: AsyncClient, db_session, api_key_and_project
):
    from app import models

    plain_key, project = api_key_and_project

    response = await client.post(
        "/api/v1/track/",
        headers={"X-API-Key": plain_key},
        json={
            "url_path": "/api/v1/users",
            "method": "GET",
            "response_status_code": 200,
            "response_time_ms": 120.5,
            "user_agent": "Test Agent",
            "ip": "1.2.3.4",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["url_path"] == "/api/v1/users"

    # Verify in DB
    result = await db_session.execute(
        select(models.Metric).where(models.Metric.project_id == project.id)
    )
    metric = result.scalar_one_or_none()
    assert metric is not None
    assert metric.response_time_ms == 120.5
    assert metric.ip_hash is not None
    assert metric.ip_hash != "1.2.3.4"


async def test_track_metric_invalid_key(client: AsyncClient):
    response = await client.post(
        "/api/v1/track/",
        headers={"X-API-Key": "invalid_key"},
        json={
            "url_path": "/api/v1/users",
            "method": "GET",
            "response_status_code": 200,
            "response_time_ms": 120.5,
        },
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["error"]


async def test_track_metric_missing_key(client: AsyncClient):
    response = await client.post(
        "/api/v1/track/",
        json={
            "url_path": "/api/v1/users",
            "method": "GET",
            "response_status_code": 200,
            "response_time_ms": 120.5,
        },
    )
    assert response.status_code == 401
    assert "API key required" in response.json()["error"]
