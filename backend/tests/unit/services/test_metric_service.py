"""Unit tests for metric_service — focused on retry behaviour."""

from http import HTTPMethod
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app import schemas
from app.services import metric_service

pytestmark = pytest.mark.asyncio

_METRIC_IN = schemas.MetricCreate(
    url_path="/api/v1/test",
    method=HTTPMethod.GET,
    response_status_code=200,
    response_time_ms=42.0,
)


async def test_add_metric_retries_on_transient_db_error_and_raises():
    """
    add_metric retries up to 3 times on SQLAlchemyError and then propagates
    the exception. rollback is called after each failed commit.
    """
    session = AsyncMock()
    session.commit.side_effect = SQLAlchemyError("transient DB error")

    with patch("asyncio.sleep", new=AsyncMock()), pytest.raises(SQLAlchemyError):
        await metric_service.add_metric(_METRIC_IN, project_id=1, session=session)

    assert session.commit.call_count == 3
    assert session.rollback.call_count == 3


async def test_add_metric_succeeds_after_transient_failure():
    """
    add_metric retries and returns the metric when a transient failure is
    followed by a successful commit.
    """
    session = AsyncMock()
    session.commit.side_effect = [SQLAlchemyError("transient"), None]

    with patch("asyncio.sleep", new=AsyncMock()):
        result = await metric_service.add_metric(
            _METRIC_IN, project_id=1, session=session
        )

    assert session.commit.call_count == 2
    assert session.rollback.call_count == 1
    assert result.url_path == "/api/v1/test"
    assert result.project_id == 1


async def test_add_metric_hashes_ip_and_removes_raw_field():
    """
    add_metric converts the raw `ip` field to a hashed `ip_hash` and does
    not pass `ip` to the Metric constructor.
    """
    session = AsyncMock()
    metric_in = schemas.MetricCreate(
        url_path="/api/v1/test",
        method=HTTPMethod.POST,
        response_status_code=201,
        response_time_ms=10.0,
        ip="192.168.1.1",
    )

    result = await metric_service.add_metric(metric_in, project_id=5, session=session)

    assert result.ip_hash is not None
    assert result.project_id == 5
