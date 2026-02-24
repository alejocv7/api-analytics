"""Integration tests for project member management."""

import uuid

import pytest
from httpx import AsyncClient, Response

from app import models
from app.services import auth_service
from tests.factories import create_user

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _add_member(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project_key: str,
    email: str,
    role: str = "viewer",
) -> Response:
    return await client.post(
        f"/api/v1/projects/{project_key}/members/",
        headers=auth_headers,
        json={"email": email, "role": role},
    )


def _auth_headers_for(user) -> dict[str, str]:
    """Build Authorization headers for a given user."""
    token = auth_service.create_user_token(user)
    return {"Authorization": f"Bearer {token.access_token}"}


# ---------------------------------------------------------------------------
# List members
# ---------------------------------------------------------------------------


async def test_list_members_includes_owner(
    client: AsyncClient, auth_headers, test_user, project
):
    """Owner row is automatically created and appears in the member list."""
    response = await client.get(
        f"/api/v1/projects/{project.project_key}/members/",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert data["page_size"] == 20
    owner = data["items"][0]
    assert owner["user_id"] == str(test_user.id)
    assert owner["role"] == "owner"
    assert owner["email"] == test_user.email
    assert owner["full_name"] == test_user.full_name


async def test_list_members_total_reflects_all_members(
    client: AsyncClient, auth_headers, project, db_session
):
    """Pagination total matches actual member count.

    Regression test for count_members bug.
    """
    user_a = await create_user(db_session, email="count-a@example.com")
    user_b = await create_user(db_session, email="count-b@example.com")
    await _add_member(client, auth_headers, project.project_key, user_a.email)
    await _add_member(client, auth_headers, project.project_key, user_b.email)

    response = await client.get(
        f"/api/v1/projects/{project.project_key}/members/",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 3  # owner + 2 members


async def test_list_members_non_member_cannot_access(
    client: AsyncClient, db_session, project
):
    """A user with no project membership gets 404, not 403."""
    other = await create_user(db_session, email="other@example.com")

    response = await client.get(
        f"/api/v1/projects/{project.project_key}/members/",
        headers=_auth_headers_for(other),
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Add member
# ---------------------------------------------------------------------------


async def test_add_member(
    client: AsyncClient,
    auth_headers,
    test_user,  # noqa: ARG001
    project,
    db_session,
):
    """Owner can add a new member."""

    new_user = await create_user(db_session, email="member@example.com")

    response = await _add_member(
        client, auth_headers, project.project_key, new_user.email, role="viewer"
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == str(new_user.id)
    assert data["project_id"] == str(project.id)
    assert data["role"] == "viewer"
    assert data["email"] == new_user.email
    assert data["full_name"] == new_user.full_name


async def test_add_member_with_member_role(
    client: AsyncClient, auth_headers, project, db_session
):
    """Owner can add a user with the 'member' role."""
    new_user = await create_user(db_session, email="collab@example.com")
    response = await _add_member(
        client, auth_headers, project.project_key, new_user.email, role="member"
    )
    assert response.status_code == 201
    assert response.json()["role"] == "member"


async def test_add_member_non_owner_forbidden(client: AsyncClient, project, db_session):
    """A non-owner member cannot invite other users."""
    viewer = await create_user(db_session, email="viewer@example.com")
    membership = models.UserProject(
        user_id=viewer.id, project_id=project.id, role=models.ProjectRole.viewer
    )
    db_session.add(membership)
    await db_session.commit()

    another = await create_user(db_session, email="another@example.com")
    response = await _add_member(
        client, _auth_headers_for(viewer), project.project_key, another.email
    )
    assert response.status_code == 403


async def test_add_owner_as_member_fails(
    client: AsyncClient, auth_headers, test_user, project
):
    """Cannot add the project owner as a member (they already are)."""
    response = await _add_member(
        client, auth_headers, project.project_key, test_user.email
    )
    assert response.status_code == 409


async def test_add_duplicate_member_fails(
    client: AsyncClient, auth_headers, project, db_session
):
    """Adding an already-existing member is a conflict."""
    new_user = await create_user(db_session, email="dup@example.com")
    await _add_member(client, auth_headers, project.project_key, new_user.email)

    response = await _add_member(
        client, auth_headers, project.project_key, new_user.email
    )
    assert response.status_code == 409


async def test_add_member_with_owner_role_fails(
    client: AsyncClient, auth_headers, project, db_session
):
    """The 'owner' role cannot be assigned via this endpoint."""
    new_user = await create_user(db_session, email="noowner@example.com")
    response = await _add_member(
        client, auth_headers, project.project_key, new_user.email, role="owner"
    )
    assert response.status_code == 422


async def test_add_member_nonexistent_user_fails(
    client: AsyncClient, auth_headers, project
):
    """Adding a non-existent email returns 404."""
    response = await _add_member(
        client, auth_headers, project.project_key, "nonexistent@example.com"
    )
    assert response.status_code == 404


async def test_add_member_invalid_email_format(
    client: AsyncClient, auth_headers, project
):
    """Invalid email format returns 422."""
    response = await client.post(
        f"/api/v1/projects/{project.project_key}/members/",
        headers=auth_headers,
        json={"email": "not-an-email", "role": "viewer"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Remove member
# ---------------------------------------------------------------------------


async def test_remove_member(client: AsyncClient, auth_headers, project, db_session):
    """Owner can remove an existing member."""
    new_user = await create_user(db_session, email="todelete@example.com")
    await _add_member(client, auth_headers, project.project_key, new_user.email)

    response = await client.delete(
        f"/api/v1/projects/{project.project_key}/members/{new_user.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204


async def test_remove_owner_fails(
    client: AsyncClient, auth_headers, test_user, project
):
    """The owner cannot be removed from their own project."""
    response = await client.delete(
        f"/api/v1/projects/{project.project_key}/members/{test_user.id}",
        headers=auth_headers,
    )
    assert response.status_code == 403


async def test_remove_nonexistent_member_fails(
    client: AsyncClient, auth_headers, project
):
    """Removing a user who is not a member returns 404."""
    response = await client.delete(
        f"/api/v1/projects/{project.project_key}/members/{uuid.uuid4()}",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Update member role
# ---------------------------------------------------------------------------


async def test_update_member_role(
    client: AsyncClient, auth_headers, project, db_session
):
    """Owner can change an existing member's role."""
    new_user = await create_user(db_session, email="upgrade@example.com")
    await _add_member(
        client, auth_headers, project.project_key, new_user.email, role="viewer"
    )

    response = await client.patch(
        f"/api/v1/projects/{project.project_key}/members/{new_user.id}",
        headers=auth_headers,
        json={"role": "member"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "member"


async def test_update_owner_role_fails(
    client: AsyncClient, auth_headers, test_user, project
):
    """The owner's role cannot be changed."""
    response = await client.patch(
        f"/api/v1/projects/{project.project_key}/members/{test_user.id}",
        headers=auth_headers,
        json={"role": "viewer"},
    )
    assert response.status_code == 403


async def test_update_member_role_to_owner_fails(
    client: AsyncClient, auth_headers, project, db_session
):
    """Cannot promote a member to the 'owner' role via this endpoint."""
    new_user = await create_user(db_session, email="promote@example.com")
    await _add_member(
        client, auth_headers, project.project_key, new_user.email, role="viewer"
    )

    response = await client.patch(
        f"/api/v1/projects/{project.project_key}/members/{new_user.id}",
        headers=auth_headers,
        json={"role": "owner"},
    )
    assert response.status_code == 422


async def test_update_nonexistent_member_role_fails(
    client: AsyncClient, auth_headers, project
):
    """Updating a role for a non-member returns 404."""
    response = await client.patch(
        f"/api/v1/projects/{project.project_key}/members/{uuid.uuid4()}",
        headers=auth_headers,
        json={"role": "member"},
    )
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Ownership uniqueness: owner can't have two projects with same name
# ---------------------------------------------------------------------------


async def test_owner_cannot_have_duplicate_project_names(
    client: AsyncClient, auth_headers
):
    """An owner cannot create two projects with the same name."""
    response1 = await client.post(
        "/api/v1/projects/",
        headers=auth_headers,
        json={"name": "Unique Project"},
    )
    assert response1.status_code == 201

    response2 = await client.post(
        "/api/v1/projects/",
        headers=auth_headers,
        json={"name": "Unique Project"},
    )
    assert response2.status_code == 409


# ---------------------------------------------------------------------------
# Member can access project via junction table
# ---------------------------------------------------------------------------


async def test_member_can_read_project(
    client: AsyncClient, auth_headers, project, db_session
):
    """A user added as a member can access the project."""
    member_user = await create_user(db_session, email="reader@example.com")
    await _add_member(
        client, auth_headers, project.project_key, member_user.email, role="viewer"
    )

    response = await client.get(
        f"/api/v1/projects/{project.project_key}",
        headers=_auth_headers_for(member_user),
    )
    assert response.status_code == 200
    assert response.json()["name"] == project.name


async def test_member_cannot_delete_project(
    client: AsyncClient, auth_headers, project, db_session
):
    """A non-owner member cannot delete the project."""
    member_user = await create_user(db_session, email="nodelete@example.com")
    await _add_member(
        client, auth_headers, project.project_key, member_user.email, role="member"
    )

    response = await client.delete(
        f"/api/v1/projects/{project.project_key}",
        headers=_auth_headers_for(member_user),
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Member-role user cannot manage members
# ---------------------------------------------------------------------------


async def _make_member_headers(
    client: AsyncClient,
    auth_headers: dict[str, str],
    project,
    db_session,
    email: str,
) -> tuple[models.User, dict[str, str]]:
    """Create a user with member role and return (user, auth_headers)."""
    member_user = await create_user(db_session, email=email)
    await _add_member(
        client, auth_headers, project.project_key, member_user.email, role="member"
    )
    return member_user, _auth_headers_for(member_user)


async def test_member_role_user_cannot_add_member(
    client: AsyncClient, auth_headers, project, db_session
):
    """A member-role user cannot add new members."""
    _member_user, member_headers = await _make_member_headers(
        client, auth_headers, project, db_session, "member-add@example.com"
    )
    another = await create_user(db_session, email="another-add@example.com")
    response = await _add_member(
        client, member_headers, project.project_key, another.email
    )
    assert response.status_code == 403


async def test_member_role_user_cannot_remove_member(
    client: AsyncClient, auth_headers, project, db_session
):
    """A member-role user cannot remove members."""
    _member_user, member_headers = await _make_member_headers(
        client, auth_headers, project, db_session, "member-rem@example.com"
    )
    another = await create_user(db_session, email="another-rem@example.com")
    await _add_member(client, auth_headers, project.project_key, another.email)
    response = await client.delete(
        f"/api/v1/projects/{project.project_key}/members/{another.id}",
        headers=member_headers,
    )
    assert response.status_code == 403


async def test_member_role_user_cannot_update_role(
    client: AsyncClient, auth_headers, project, db_session
):
    """A member-role user cannot update another member's role."""
    _member_user, member_headers = await _make_member_headers(
        client, auth_headers, project, db_session, "member-upd@example.com"
    )
    another = await create_user(db_session, email="another-upd@example.com")
    await _add_member(client, auth_headers, project.project_key, another.email)
    response = await client.patch(
        f"/api/v1/projects/{project.project_key}/members/{another.id}",
        headers=member_headers,
        json={"role": "member"},
    )
    assert response.status_code == 403
