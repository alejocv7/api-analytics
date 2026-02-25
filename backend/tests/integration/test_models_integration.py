from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select

from app.models.metric import Metric
from tests.factories import create_project

pytestmark = pytest.mark.asyncio


async def test_metric_timestamp_utc_round_trip(db_session, test_user):
    project = await create_project(db_session, user=test_user, name="UTC Test")

    # Use a non-UTC timezone to ensure conversion happens
    ts = datetime(2026, 2, 25, 15, 0, 0, tzinfo=ZoneInfo("America/New_York"))

    metric = Metric(
        project_id=project.id,
        url_path="/utc-test",
        method="GET",
        response_status_code=200,
        response_time_ms=10.5,
        timestamp=ts,
    )
    db_session.add(metric)
    await db_session.commit()
    await db_session.refresh(metric)

    # 1. Check refresh returns UTC
    assert metric.timestamp == ts.astimezone(UTC)

    # 2. Re-fetch from DB
    stmt = select(Metric).where(Metric.id == metric.id)
    result = await db_session.execute(stmt)
    db_metric = result.scalar_one()

    assert db_metric.timestamp.tzinfo == UTC
    assert db_metric.timestamp == ts.astimezone(UTC)


async def test_metric_server_default_is_read_as_utc(db_session, test_user):
    project = await create_project(db_session, user=test_user, name="Default Test")

    # Let server_default handle timestamp
    metric = Metric(
        project_id=project.id,
        url_path="/default-test",
        method="GET",
        response_status_code=200,
        response_time_ms=10.5,
    )
    db_session.add(metric)
    await db_session.commit()
    await db_session.refresh(metric)

    assert metric.timestamp is not None
    assert metric.timestamp.tzinfo == UTC
