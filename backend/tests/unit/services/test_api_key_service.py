from unittest.mock import AsyncMock, patch

import pytest

from app import models, schemas
from app.core.config import settings
from app.core.exceptions import BadRequestError, ConflictError
from app.services import api_key_service

pytestmark = pytest.mark.asyncio


async def test_create_api_key_limit(monkeypatch):
    session = AsyncMock()
    project = models.Project(id=1, name="Test Project")
    key_in = schemas.APIKeyCreate(name="Limit Key")

    monkeypatch.setattr(settings, "API_KEY_PROJECT_LIMIT", 5)

    # Service uses `await session.scalar(stmt) or 0` after the Step 1 fix
    session.scalar.return_value = 5  # Already 5 active keys

    with pytest.raises(ConflictError) as exc:
        await api_key_service.create_api_key(key_in, project, session)
    assert "maximum number of API keys" in str(exc.value)


async def test_delete_last_active_key_fails():
    session = AsyncMock()
    project_id = 1
    api_key_id = 10
    api_key = models.APIKey(id=api_key_id, project_id=project_id, is_active=True)

    with patch(
        "app.services.api_key_service.get_api_key", new_callable=AsyncMock
    ) as mock_get:
        mock_get.return_value = api_key
        session.scalar.return_value = 0  # No other active keys

        with pytest.raises(BadRequestError) as exc:
            await api_key_service.delete_api_key(api_key_id, project_id, session)
        assert "Cannot delete the last active API key" in str(exc.value)
