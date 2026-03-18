from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import func, select

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
    base_time = datetime.now(UTC).replace(hour=12, minute=0, second=0, microsecond=0)

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
    assert len(data["items"]) == 2  # /users and /posts

    users_stat = next(d for d in data["items"] if d["url_path"] == "/users")
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
    assert len(data["items"]) >= 1
    assert "timestamp" in data["items"][0]
    assert "request_count" in data["items"][0]


async def test_cleanup_metrics(db_session, project_with_data):
    from app import models
    from app.services.metric_service import cleanup_old_metrics

    # Add a very old metric
    old_time = datetime.now(UTC) - timedelta(days=100)
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
    assert len(data["items"]) == 2
    assert data["total"] == 3

    # Request page 2 with page_size 2
    response = await client.get(
        f"/api/v1/projects/{project_with_data.project_key}/metrics/",
        headers=auth_headers,
        params={"page": 2, "page_size": 2},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["total"] == 3


async def test_metrics_range_too_long(client: AsyncClient, auth_headers, project):
    start = datetime.now(UTC)
    end = start + timedelta(days=61)
    response = await client.get(
        f"/api/v1/projects/{project.project_key}/metrics/",
        headers=auth_headers,
        params={"start_date": start.isoformat(), "end_date": end.isoformat()},
    )
    assert response.status_code == 422
    assert "60 days or less" in response.text


async def test_metrics_range_too_short(client: AsyncClient, auth_headers, project):
    start = datetime.now(UTC)
    end = start + timedelta(seconds=30)
    response = await client.get(
        f"/api/v1/projects/{project.project_key}/metrics/",
        headers=auth_headers,
        params={"start_date": start.isoformat(), "end_date": end.isoformat()},
    )
    assert response.status_code == 422
    assert "at least 1 minute" in response.text


async def test_self_metrics_are_recorded_when_enabled(
    client: AsyncClient, auth_headers, session_factory, monkeypatch
):
    from app import models
    from app.core import db as core_db
    from app.core.config import settings
    from app.core.seed import seed_initial_data
    from app.main import app

    request_path = "/api/v1/projects/"
    monkeypatch.setattr(settings, "ENABLE_SELF_METRICS", True)
    monkeypatch.setattr(core_db, "AsyncSessionLocal", session_factory)

    async with session_factory() as session:
        await seed_initial_data(session)
        project_result = await session.execute(
            select(models.Project).where(
                models.Project.project_key == settings.PROJECT_KEY
            )
        )
        self_monitoring_project: models.Project = project_result.scalar_one()

        before_count = await session.scalar(
            select(func.count(models.Metric.id)).where(
                models.Metric.project_id == self_monitoring_project.id,
            )
        )
        assert before_count is not None

    response = await client.get(request_path, headers=auth_headers)
    assert response.status_code == 200

    await app.state.metric_middleware.drain_background_tasks(timeout_seconds=1)

    async with session_factory() as session:
        after_count = await session.scalar(
            select(func.count(models.Metric.id)).where(
                models.Metric.project_id == self_monitoring_project.id,
            )
        )
        assert after_count is not None
        metric_result = await session.execute(
            select(models.Metric)
            .where(
                models.Metric.project_id == self_monitoring_project.id,
            )
            .order_by(models.Metric.timestamp.desc())
        )
        recorded_metric = metric_result.scalars().first()

    assert after_count == before_count + 1
    assert recorded_metric is not None
    assert recorded_metric.url_path in {request_path, request_path.rstrip("/")}
    assert recorded_metric.method.value == "GET"
    assert recorded_metric.response_status_code == 200
    assert recorded_metric.response_time_ms > 0


async def test_endpoint_stats_sort_by_request_count(
    client: AsyncClient, auth_headers, project_with_data
):
    # /users has 2 requests, /posts has 1 — default sort is request_count desc
    response = await client.get(
        f"/api/v1/projects/{project_with_data.project_key}/metrics/endpoints",
        headers=auth_headers,
        params={"sort_by": "request_count", "sort_order": "desc"},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["url_path"] == "/users"
    assert items[1]["url_path"] == "/posts"


async def test_endpoint_stats_sort_by_request_count_asc(
    client: AsyncClient, auth_headers, project_with_data
):
    response = await client.get(
        f"/api/v1/projects/{project_with_data.project_key}/metrics/endpoints",
        headers=auth_headers,
        params={"sort_by": "request_count", "sort_order": "asc"},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["url_path"] == "/posts"
    assert items[1]["url_path"] == "/users"


async def test_endpoint_stats_sort_by_avg_response_time(
    client: AsyncClient, auth_headers, project_with_data
):
    # /users avg = (50 + 500) / 2 = 275ms, /posts avg = 150ms
    response = await client.get(
        f"/api/v1/projects/{project_with_data.project_key}/metrics/endpoints",
        headers=auth_headers,
        params={"sort_by": "avg_response_time_ms", "sort_order": "desc"},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["url_path"] == "/users"

    response = await client.get(
        f"/api/v1/projects/{project_with_data.project_key}/metrics/endpoints",
        headers=auth_headers,
        params={"sort_by": "avg_response_time_ms", "sort_order": "asc"},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["url_path"] == "/posts"


async def test_endpoint_stats_invalid_sort_field(
    client: AsyncClient, auth_headers, project_with_data
):
    response = await client.get(
        f"/api/v1/projects/{project_with_data.project_key}/metrics/endpoints",
        headers=auth_headers,
        params={"sort_by": "nonexistent_field"},
    )
    assert response.status_code == 422


async def test_metrics_empty_project_summary(
    client: AsyncClient, auth_headers, project
):
    response = await client.get(
        f"/api/v1/projects/{project.project_key}/metrics/summary",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["request_count"] == 0
    assert data["error_count"] == 0
    assert data["requests_per_minute"] == 0.0
