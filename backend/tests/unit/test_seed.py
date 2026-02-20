"""Unit tests for seed.py idempotency."""

from unittest.mock import AsyncMock, patch

import pytest

from app import models
from app.core.config import settings
from app.core.seed import seed_initial_data

pytestmark = pytest.mark.asyncio


async def test_seed_skips_when_project_key_not_set(monkeypatch):
    """seed_initial_data exits early and logs an error when PROJECT_KEY is empty."""
    monkeypatch.setattr(settings, "PROJECT_KEY", "")
    session = AsyncMock()

    with patch("app.core.seed.logger") as mock_logger:
        await seed_initial_data(session)

    session.add.assert_not_called()
    mock_logger.error.assert_called_once()


async def test_seed_creates_user_and_project_on_first_run(monkeypatch):
    """First run: creates the system user and self-monitoring project."""
    monkeypatch.setattr(settings, "PROJECT_KEY", "test-self-key")
    monkeypatch.setattr(settings, "PROJECT_USER", "system@example.com")
    monkeypatch.setattr(settings, "PROJECT_PASSWORD", "StrongPassword123!")
    monkeypatch.setattr(settings, "PROJECT_NAME", "Test Service")
    monkeypatch.setattr(settings, "PROJECT_DESCRIPTION", "Test Desc")

    session = AsyncMock()

    async def _fake_refresh(obj: object) -> None:
        # Simulate the DB assigning a primary key on commit+refresh.
        if isinstance(obj, models.User):
            obj.id = 99

    session.refresh.side_effect = _fake_refresh

    with (
        patch("app.core.seed.security.hash_password", return_value="$hashed$"),
        patch(
            "app.core.seed.user_service.get_user_by_email",
            new=AsyncMock(return_value=None),
        ),
        patch(
            "app.core.seed.project_service.get_user_project_by_key",
            new=AsyncMock(return_value=None),
        ),
    ):
        await seed_initial_data(session)

    # user, project, and owner UserProject membership
    assert session.add.call_count == 3
    # one commit for the user, one for the project+membership
    assert session.commit.call_count == 2


async def test_seed_is_idempotent_when_both_exist(monkeypatch):
    """Subsequent run: nothing is created when user and project already exist."""
    monkeypatch.setattr(settings, "PROJECT_KEY", "test-self-key")
    monkeypatch.setattr(settings, "PROJECT_USER", "system@example.com")

    session = AsyncMock()
    existing_user = models.User(id=1, email="system@example.com", hashed_password="x")
    existing_project = models.Project(
        name="Test Self-Monitoring", user_id=1, project_key="test-self-key"
    )

    with (
        patch(
            "app.core.seed.user_service.get_user_by_email",
            new=AsyncMock(return_value=existing_user),
        ),
        patch(
            "app.core.seed.project_service.get_user_project_by_key",
            new=AsyncMock(return_value=existing_project),
        ),
    ):
        await seed_initial_data(session)

    session.add.assert_not_called()
    session.commit.assert_not_called()


async def test_seed_creates_project_when_user_already_exists(monkeypatch):
    """Partial state: user exists but project does not — only the project is created."""
    monkeypatch.setattr(settings, "PROJECT_KEY", "test-self-key")
    monkeypatch.setattr(settings, "PROJECT_USER", "system@example.com")
    monkeypatch.setattr(settings, "PROJECT_NAME", "Test Service")
    monkeypatch.setattr(settings, "PROJECT_DESCRIPTION", "Test Desc")

    session = AsyncMock()
    existing_user = models.User(id=1, email="system@example.com", hashed_password="x")

    with (
        patch(
            "app.core.seed.user_service.get_user_by_email",
            new=AsyncMock(return_value=existing_user),
        ),
        patch(
            "app.core.seed.project_service.get_user_project_by_key",
            new=AsyncMock(return_value=None),
        ),
    ):
        await seed_initial_data(session)

    # project + owner UserProject membership
    assert session.add.call_count == 2
    assert session.commit.call_count == 1
