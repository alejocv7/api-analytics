from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from tests.factories import create_metric


@pytest.mark.asyncio
async def test_get_metrics_summary_empty(
    client: AsyncClient, auth_headers, project, db_session
):
    """Test metrics summary when there are no metrics."""
    response = await client.get(
        f"/api/v1/projects/{project.project_key}/metrics/summary",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["request_count"] == 0
    assert data["requests_per_minute"] == 0
    assert data["error_rate"] == 0


@pytest.mark.asyncio
async def test_get_metrics_invalid_date_range(
    client: AsyncClient, auth_headers, project
):
    """Test that end_date before start_date raises an error."""
    start_date = datetime.now(timezone.utc)
    end_date = start_date - timedelta(days=1)

    response = await client.get(
        f"/api/v1/projects/{project.project_key}/metrics/summary",
        headers=auth_headers,
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_pagination_edge_cases(
    client: AsyncClient, auth_headers, project, db_session
):
    """Test pagination limits and offsets."""
    # Create 15 metrics
    for _ in range(15):
        await create_metric(db_session, project=project, url_path="/test")

    # Page 1, size 10
    response = await client.get(
        f"/api/v1/projects/{project.project_key}/metrics/time-series",
        headers=auth_headers,
        params={"page": 1, "page_size": 10, "granularity": "minute"},
    )
    assert response.status_code == 200
    # Note: time-series groups by time, so we might get fewer points than raw metrics if they are in same minute.
    # But let's check basic response structure.
    data = response.json()
    assert isinstance(data, list)

    # Test invalid page size
    response = await client.get(
        f"/api/v1/projects/{project.project_key}/metrics/time-series",
        headers=auth_headers,
        params={"page_size": 10001},  # Exceeds max
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_metrics_large_volume_simulation(
    client: AsyncClient, auth_headers, project, db_session
):
    """Simulate a larger volume of metrics to ensure query performance/correctness."""
    # Create many metrics in bulk if possible, or loop
    # For test speed, we'll keep it reasonable (e.g., 50)
    for i in range(50):
        # Distribute over last hour
        ts = datetime.now(timezone.utc) - timedelta(minutes=i)
        await create_metric(
            db_session,
            project=project,
            response_time_ms=100 + i,
            timestamp=ts,
            response_status_code=200 if i % 10 != 0 else 500,
        )

    response = await client.get(
        f"/api/v1/projects/{project.project_key}/metrics/summary",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["request_count"] == 50
    assert data["error_count"] == 5  # 50 / 10 = 5 errors
    assert data["avg_response_time_ms"] > 100
