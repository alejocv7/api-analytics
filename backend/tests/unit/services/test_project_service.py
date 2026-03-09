import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app import models, schemas
from app.core.exceptions import ConflictError, NotFoundError
from app.services import project_service

pytestmark = pytest.mark.asyncio


def _make_project(**kwargs) -> models.Project:
    """Build a Project with enough fields to serialize into ProjectResponse."""
    defaults = {
        "id": uuid.uuid4(),
        "name": "Test Project",
        "description": None,
        "project_key": "test-key",
        "user_id": uuid.uuid4(),
        "is_active": True,
        "created_at": datetime.now(UTC),
        "updated_at": None,
    }
    return models.Project(**{**defaults, **kwargs})


async def test_update_project_name_exists():
    session = AsyncMock()
    project = _make_project(name="Old")
    update_data = schemas.ProjectUpdate(name="New")

    session.scalar.return_value = True  # simulate name conflict exists

    with pytest.raises(ConflictError) as exc:
        await project_service.update_user_project(project, update_data, session)
    assert "Project name already in use" in str(exc.value)


async def test_update_user_project_same_name_no_conflict():
    session = AsyncMock()
    project = _make_project(name="Same Name")
    update_data = schemas.ProjectUpdate(name="Same Name")

    # Counts query returns (0, 0); the conflict-check scalar should never be called.
    mock_result = MagicMock()
    mock_result.one.return_value = (0, 0)
    session.execute.return_value = mock_result

    result = await project_service.update_user_project(project, update_data, session)

    assert isinstance(result, schemas.ProjectResponse)
    assert result.name == "Same Name"
    assert result.member_count == 0
    assert result.api_key_count == 0


async def test_find_project_by_key_not_found():
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.one_or_none.return_value = None
    session.scalars.return_value = mock_result

    result = await project_service.find_project_by_key("ghost", session)
    assert result is None


async def test_get_project_by_key_not_found():
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.one_or_none.return_value = None
    session.scalars.return_value = mock_result

    with pytest.raises(NotFoundError):
        await project_service.get_project_by_key("ghost", session)
