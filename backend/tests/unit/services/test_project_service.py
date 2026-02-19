from unittest.mock import AsyncMock

import pytest

from app import models, schemas
from app.core.exceptions import ConflictError
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
