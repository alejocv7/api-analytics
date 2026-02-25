from unittest.mock import AsyncMock, MagicMock

import pytest

from app import models, schemas
from app.core.exceptions import ConflictError, NotFoundError
from app.services import project_service

pytestmark = pytest.mark.asyncio


async def test_update_project_name_exists():
    session = AsyncMock()
    project = models.Project(id=1, name="Old", user_id=1)
    update_data = schemas.ProjectUpdate(name="New")

    # Mock session.scalar to be awaited and return True
    session.scalar.return_value = True  # Name "New" already exists

    with pytest.raises(ConflictError) as exc:
        await project_service.update_user_project(project, update_data, session)
    assert "Project name already in use" in str(exc.value)


async def test_update_user_project_same_name_no_conflict():
    session = AsyncMock()
    project = models.Project(id=1, name="Same Name", user_id=1)
    update_data = schemas.ProjectUpdate(name="Same Name")

    # scalar should NOT be called if name hasn't changed
    await project_service.update_user_project(project, update_data, session)
    session.scalar.assert_not_called()


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
