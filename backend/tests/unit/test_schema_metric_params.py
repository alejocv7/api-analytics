from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from app.schemas.metric import MetricParams


def test_metric_params_dates_normalization():
    start = datetime(2026, 1, 1, 10, 30, 45, tzinfo=UTC)
    end = datetime(2026, 1, 1, 11, 45, 12, tzinfo=UTC)
    params = MetricParams(start_date=start, end_date=end)

    # Truncation check
    assert params.start_date.second == 0
    assert params.start_date.microsecond == 0
    assert params.end_date.second == 59
    assert params.end_date.microsecond == 999999


def test_metric_params_range_too_long():
    start = datetime.now(UTC)
    end = start + timedelta(days=61)
    with pytest.raises(ValidationError, match="60 days or less"):
        MetricParams(start_date=start, end_date=end)


def test_metric_params_range_too_short():
    start = datetime.now(UTC)
    end = start + timedelta(seconds=30)
    with pytest.raises(ValidationError, match="at least 1 minute"):
        MetricParams(start_date=start, end_date=end)


def test_metric_params_end_before_start():
    start = datetime.now(UTC)
    end = start - timedelta(minutes=5)
    with pytest.raises(ValidationError, match="cannot be before"):
        MetricParams(start_date=start, end_date=end)


def test_metric_params_exact_one_minute():
    start = datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
    end = start + timedelta(minutes=1)
    params = MetricParams(start_date=start, end_date=end)
    assert params.end_date > params.start_date
