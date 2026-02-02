import pytest
import pytest_asyncio
from app import models
from app.core import security
from httpx import AsyncClient
from sqlalchemy import select


@pytest_asyncio.fixture
async def api_key_and_project(db_session, test_user):
    from app import models

    project = models.Project(
        name="Track Project", project_key="track-key", user_id=test_user.id
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    plain_key = "sk_test_1234567890abcdef"
    api_key = models.APIKey(
        name="Track Key",
        key_hash=security.hash_api_key(plain_key),
        key_prefix=plain_key[:8],
        project_id=project.id,
        is_active=True,
    )
    db_session.add(api_key)
    await db_session.commit()
    return plain_key, project


@pytest.mark.asyncio
async def test_track_metric_success(
    client: AsyncClient, db_session, api_key_and_project
):
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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
