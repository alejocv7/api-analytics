"""Unit tests for member_service."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app import models
from app.core.enums import ProjectRole
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.services import member_service

pytestmark = pytest.mark.asyncio


def _make_project(owner_id: uuid.UUID | None = None) -> models.Project:
    oid = owner_id or uuid.uuid4()
    return models.Project(
        id=uuid.uuid4(),
        name="Test Project",
        user_id=oid,
        project_key="test-project-abc123",
    )


def _make_user(user_id: uuid.UUID | None = None) -> models.User:
    uid = user_id or uuid.uuid4()
    user = MagicMock(spec=models.User)
    user.id = uid
    user.email = f"user-{uid}@example.com"
    user.full_name = "Test User"
    return user


# ---------------------------------------------------------------------------
# add_member
# ---------------------------------------------------------------------------


async def test_add_member_owner_role_forbidden():
    """add_member raises ForbiddenError when role=owner is requested."""
    session = AsyncMock()
    project = _make_project()
    with pytest.raises(ForbiddenError, match="owner role cannot be assigned"):
        await member_service.add_member(
            project, "anyone@example.com", ProjectRole.owner, session
        )


async def test_add_member_user_not_found():
    """add_member raises NotFoundError when no user matches the email."""
    session = AsyncMock()
    project = _make_project()

    with (
        patch(
            "app.services.member_service.user_service.get_user_by_email",
            new_callable=AsyncMock,
            return_value=None,
        ),
        pytest.raises(NotFoundError, match="User not found"),
    ):
        await member_service.add_member(
            project, "ghost@example.com", ProjectRole.viewer, session
        )


async def test_add_member_user_is_owner():
    """add_member raises ConflictError when the invited user is already the owner."""
    owner_id = uuid.uuid4()
    project = _make_project(owner_id=owner_id)
    user = _make_user(user_id=owner_id)
    session = AsyncMock()

    with (
        patch(
            "app.services.member_service.user_service.get_user_by_email",
            new_callable=AsyncMock,
            return_value=user,
        ),
        pytest.raises(ConflictError, match="already the owner"),
    ):
        await member_service.add_member(
            project, user.email, ProjectRole.viewer, session
        )


async def test_add_member_already_a_member():
    """add_member raises ConflictError when the user is already a member."""
    project = _make_project()
    user = _make_user()
    session = AsyncMock()
    existing_membership = MagicMock(spec=models.UserProject)

    with patch(
        "app.services.member_service.user_service.get_user_by_email",
        new_callable=AsyncMock,
        return_value=user,
    ):
        session.get.return_value = existing_membership
        with pytest.raises(ConflictError, match="already a member"):
            await member_service.add_member(
                project, user.email, ProjectRole.viewer, session
            )


async def test_add_member_happy_path():
    """add_member returns the UserProject with user loaded on success."""
    project = _make_project()
    user = _make_user()
    session = AsyncMock()

    expected_membership = MagicMock(spec=models.UserProject)
    mock_scalars_result = MagicMock()
    mock_scalars_result.one.return_value = expected_membership
    session.get.return_value = None
    session.scalars.return_value = mock_scalars_result

    with patch(
        "app.services.member_service.user_service.get_user_by_email",
        new_callable=AsyncMock,
        return_value=user,
    ):
        result = await member_service.add_member(
            project, user.email, ProjectRole.viewer, session
        )

    assert result is expected_membership
    session.add.assert_called_once()
    session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# remove_member
# ---------------------------------------------------------------------------


async def test_remove_member_owner_cannot_be_removed():
    """remove_member raises ForbiddenError when trying to remove the owner."""
    owner_id = uuid.uuid4()
    project = _make_project(owner_id=owner_id)
    session = AsyncMock()

    with pytest.raises(ForbiddenError, match="owner cannot be removed"):
        await member_service.remove_member(project, owner_id, session)


async def test_remove_member_not_found():
    """remove_member raises NotFoundError when the user is not a member."""
    project = _make_project()
    session = AsyncMock()
    session.get.return_value = None

    with pytest.raises(NotFoundError, match="Member not found"):
        await member_service.remove_member(project, uuid.uuid4(), session)


async def test_remove_member_happy_path():
    """remove_member deletes the membership and commits."""
    project = _make_project()
    session = AsyncMock()
    membership = MagicMock(spec=models.UserProject)
    session.get.return_value = membership

    await member_service.remove_member(project, uuid.uuid4(), session)

    session.delete.assert_called_once_with(membership)
    session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# update_member_role
# ---------------------------------------------------------------------------


async def test_update_member_role_owner_role_protected():
    """update_member_role raises ForbiddenError when targeting the owner."""
    owner_id = uuid.uuid4()
    project = _make_project(owner_id=owner_id)
    session = AsyncMock()

    with pytest.raises(ForbiddenError, match="owner's role cannot be changed"):
        await member_service.update_member_role(
            project, owner_id, ProjectRole.viewer, session
        )


async def test_update_member_role_owner_role_cannot_be_assigned():
    """update_member_role raises ForbiddenError when assigning owner role."""
    project = _make_project()
    session = AsyncMock()

    with pytest.raises(ForbiddenError, match="owner role cannot be assigned"):
        await member_service.update_member_role(
            project, uuid.uuid4(), ProjectRole.owner, session
        )


async def test_update_member_role_not_found():
    """update_member_role raises NotFoundError when the membership doesn't exist."""
    project = _make_project()
    session = AsyncMock()
    session.get.return_value = None

    with pytest.raises(NotFoundError, match="Member not found"):
        await member_service.update_member_role(
            project, uuid.uuid4(), ProjectRole.member, session
        )


async def test_update_member_role_happy_path():
    """update_member_role updates the role and returns the loaded membership."""
    project = _make_project()
    session = AsyncMock()
    membership = MagicMock(spec=models.UserProject)
    session.get.return_value = membership

    expected_membership = MagicMock(spec=models.UserProject)
    mock_scalars_result = MagicMock()
    mock_scalars_result.one.return_value = expected_membership
    session.scalars.return_value = mock_scalars_result

    result = await member_service.update_member_role(
        project, uuid.uuid4(), ProjectRole.member, session
    )

    assert membership.role == ProjectRole.member
    session.commit.assert_called_once()
    assert result is expected_membership
