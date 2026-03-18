import uuid
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.models.api_key import APIKey
from app.models.base import UTCDateTime
from app.models.metric import Metric
from app.models.project import Project


def test_api_key_is_expired():
    # Never expires
    key_never = APIKey(name="N", project_id=uuid.uuid4(), expires_at=None)
    assert key_never.is_expired is False

    # Expired
    past = datetime.now(UTC) - timedelta(days=1)
    key_past = APIKey(name="P", project_id=uuid.uuid4(), expires_at=past)
    assert key_past.is_expired is True

    # Not expired yet
    future = datetime.now(UTC) + timedelta(days=1)
    key_future = APIKey(name="F", project_id=uuid.uuid4(), expires_at=future)
    assert key_future.is_expired is False


def test_api_key_is_valid():
    key = APIKey(name="T", project_id=uuid.uuid4(), is_active=True, expires_at=None)
    assert key.is_valid is True

    key.is_active = False
    assert key.is_valid is False

    key.is_active = True
    key.expires_at = datetime.now(UTC) - timedelta(days=1)
    assert key.is_valid is False


def test_project_key_generated_as_name_slug():
    p = Project(name="My Awesome Project", user_id=uuid.uuid4())
    assert p.project_key == "my-awesome-project"


def test_project_key_is_mutable():
    p = Project(name="Test Project", user_id=uuid.uuid4())
    # Should not raise; project_key can be updated (e.g. on rename)
    p.project_key = "renamed-project"
    assert p.project_key == "renamed-project"


def test_model_reprs():
    pid = uuid.uuid4()
    ak = APIKey(id=uuid.uuid4(), name="MyKey", project_id=pid)
    assert "MyKey" in repr(ak)
    assert str(pid) in repr(ak)

    m = Metric(id=uuid.uuid4(), url_path="/x", method="GET", project_id=pid)
    assert "/x" in repr(m)
    assert "GET" in repr(m)


def test_utcdatetime_logic():
    decorator = UTCDateTime()

    # 1. Write: Naive raises ValueError
    naive = datetime(2026, 1, 1, 12, 0)  # noqa: DTZ001
    with pytest.raises(ValueError, match="Naive datetime not allowed"):
        decorator.process_bind_param(naive, None)

    # 2. Write: Converts aware to UTC
    aware_est = datetime(2026, 1, 1, 12, 0, tzinfo=ZoneInfo("America/New_York"))
    result_write = decorator.process_bind_param(aware_est, None)
    assert result_write == aware_est.astimezone(UTC)

    # 3. Read: Attaches UTC to naive
    naive_from_db = datetime(2026, 1, 1, 12, 0)  # noqa: DTZ001
    result_read = decorator.process_result_value(naive_from_db, None)
    assert result_read == naive_from_db.replace(tzinfo=UTC)

    # 4. Write/Read: None returns None
    assert decorator.process_bind_param(None, None) is None
    assert decorator.process_result_value(None, None) is None
