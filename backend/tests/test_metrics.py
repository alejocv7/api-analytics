from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient

from tests.factories import create_metric, create_project

pytestmark = pytest.mark.asyncio


@pytest_asyncio.fixture
async def project_with_data(db_session, test_user):
    project = await create_project(
        db_session,
        user=test_user,
        name="Data Project",
        project_key="data-key",
    )

    # Add some metrics within Today's range
    base_time = datetime.now(timezone.utc).replace(
        hour=12, minute=0, second=0, microsecond=0
    )

    await create_metric(
        db_session,
        project=project,
        url_path="/users",
        method="GET",
        response_status_code=200,
        response_time_ms=50.0,
        timestamp=base_time,
    )
    await create_metric(
        db_session,
        project=project,
        url_path="/users",
        method="GET",
        response_status_code=500,
        response_time_ms=500.0,
        timestamp=base_time + timedelta(minutes=2),
    )
    await create_metric(
        db_session,
        project=project,
        url_path="/posts",
        method="POST",
        response_status_code=201,
        response_time_ms=150.0,
        timestamp=base_time + timedelta(minutes=10),
    )
    return project


async def test_get_metrics_summary(
    client: AsyncClient, auth_headers, project_with_data
):
    response = await client.get(
        f"/api/v1/projects/{project_with_data.project_key}/metrics/summary",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["request_count"] == 3
    assert data["error_count"] == 1
    assert data["error_rate"] == pytest.approx(33.33, 0.01)


async def test_get_metrics_endpoints(
    client: AsyncClient, auth_headers, project_with_data
):
    response = await client.get(
        f"/api/v1/projects/{project_with_data.project_key}/metrics/endpoints",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # /users and /posts

    users_stat = next(d for d in data if d["url_path"] == "/users")
    assert users_stat["request_count"] == 2
    assert users_stat["error_count"] == 1


@pytest.mark.parametrize("granularity", ["minute", "hour", "day"])
async def test_get_metrics_time_series(
    client: AsyncClient, auth_headers, project_with_data, granularity
):
    response = await client.get(
        f"/api/v1/projects/{project_with_data.project_key}/metrics/time-series",
        headers=auth_headers,
        params={"granularity": granularity},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "timestamp" in data[0]
    assert "request_count" in data[0]


async def test_cleanup_metrics(db_session, project_with_data):
    from app import models
    from app.services.metric_service import cleanup_old_metrics
    from sqlalchemy import select

    # Add a very old metric
    old_time = datetime.now(timezone.utc) - timedelta(days=100)
    await create_metric(
        db_session,
        project=project_with_data,
        url_path="/old",
        method="GET",
        response_status_code=200,
        response_time_ms=10.0,
        timestamp=old_time,
    )

    # Run cleanup (90 days retention)
    deleted_count = await cleanup_old_metrics(db_session, retention_days=90)
    assert deleted_count == 1

    # Verify it's gone
    result = await db_session.execute(
        select(models.Metric).where(models.Metric.url_path == "/old")
    )
    assert result.scalar_one_or_none() is None

    # Verify recent metrics are still there
    result = await db_session.execute(
        select(models.Metric).where(models.Metric.project_id == project_with_data.id)
    )
    assert len(result.scalars().all()) == 3


async def test_metrics_pagination(client: AsyncClient, auth_headers, project_with_data):
    # project_with_data has 3 metrics
    # Request page 1 with page_size 2
    response = await client.get(
        f"/api/v1/projects/{project_with_data.project_key}/metrics/",
        headers=auth_headers,
        params={"page": 1, "page_size": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Request page 2 with page_size 2
    response = await client.get(
        f"/api/v1/projects/{project_with_data.project_key}/metrics/",
        headers=auth_headers,
        params={"page": 2, "page_size": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
