import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app import models, schemas
from app.core.config import settings
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.services import api_key_service

pytestmark = pytest.mark.asyncio


async def test_create_api_key_limit(monkeypatch):
    session = AsyncMock()
    project = models.Project(id=uuid.uuid4(), name="Test Project")
    key_in = schemas.APIKeyCreate(name="Limit Key")

    monkeypatch.setattr(settings, "API_KEY_PROJECT_LIMIT", 5)

    # Service uses `await session.scalar(stmt) or 0` after the Step 1 fix
    session.scalar.return_value = 5  # Already 5 active keys

    with pytest.raises(ConflictError) as exc:
        await api_key_service.create_api_key(key_in, project, session)
    assert "maximum number of API keys" in str(exc.value)


async def test_delete_last_active_key_fails():
    session = AsyncMock()
    project_id = uuid.uuid4()
    api_key_id = uuid.uuid4()
    api_key = models.APIKey(id=api_key_id, project_id=project_id, is_active=True)

    with patch(
        "app.services.api_key_service.get_api_key", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = api_key
        session.scalar.return_value = 0  # No other active keys

        with pytest.raises(BadRequestError) as exc:
            await api_key_service.delete_api_key(api_key_id, project_id, session)
        assert "Cannot delete the last active API key" in str(exc.value)


# ---------------------------------------------------------------------------
# APIKey.record_usage
# ---------------------------------------------------------------------------


def test_record_usage_increments_total_requests():
    api_key = models.APIKey(name="Test", project_id=1, total_requests=0)
    assert api_key.total_requests == 0

    api_key.record_usage()

    assert api_key.total_requests == 1
    assert api_key.last_used_at is not None


def test_record_usage_accumulates_across_calls():
    api_key = models.APIKey(name="Test", project_id=1)
    api_key.total_requests = 5

    api_key.record_usage()
    api_key.record_usage()

    assert api_key.total_requests == 7


def test_record_usage_sets_last_used_at_to_utc_now():
    api_key = models.APIKey(name="Test", project_id=1, total_requests=0)
    before = datetime.now(UTC)

    api_key.record_usage()

    after = datetime.now(UTC)
    assert api_key.last_used_at is not None
    assert before <= api_key.last_used_at <= after


async def test_rotate_inactive_key_fails():
    session = AsyncMock()
    project_id = uuid.uuid4()
    key_id = uuid.uuid4()
    api_key = models.APIKey(id=key_id, project_id=project_id, is_active=False)

    with (
        patch("app.services.api_key_service.get_api_key", return_value=api_key),
        pytest.raises(BadRequestError, match="inactive or expired"),
    ):
        await api_key_service.rotate_api_key(key_id, project_id, session)


async def test_rotate_expired_key_fails():
    session = AsyncMock()
    project_id = uuid.uuid4()
    key_id = uuid.uuid4()
    past = datetime.now(UTC) - timedelta(days=1)
    api_key = models.APIKey(
        id=key_id, project_id=project_id, expires_at=past, is_active=True
    )

    with (
        patch("app.services.api_key_service.get_api_key", return_value=api_key),
        pytest.raises(BadRequestError, match="inactive or expired"),
    ):
        await api_key_service.rotate_api_key(key_id, project_id, session)


async def test_rotate_already_rotated_name_no_double_suffix():
    session = AsyncMock()
    project_id = uuid.uuid4()
    key_id = uuid.uuid4()
    api_key = models.APIKey(
        id=key_id, project_id=project_id, name="K (rotated)", is_active=True
    )

    with (
        patch("app.services.api_key_service.get_api_key", return_value=api_key),
        patch("app.models.APIKey.new_key") as mock_new,
    ):
        new_key_obj = models.APIKey(name="K (rotated)", project_id=project_id)
        mock_new.return_value = (new_key_obj, "sk_new")

        await api_key_service.rotate_api_key(key_id, project_id, session)

        assert api_key.name == "K (rotated)"  # Not "K (rotated) (rotated)"


async def test_get_api_key_not_found():
    session = AsyncMock()
    # await session.scalars(...) returns a mock object that has a .first() method
    mock_result = MagicMock()
    mock_result.first.return_value = None
    session.scalars.return_value = mock_result

    with pytest.raises(NotFoundError):
        await api_key_service.get_api_key(uuid.uuid4(), uuid.uuid4(), session)
