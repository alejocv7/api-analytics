import pytest
from httpx import AsyncClient

from app import models
from app.core.config import settings
from tests.factories import create_api_key, create_user, create_web_auth_cookies

pytestmark = pytest.mark.asyncio


async def _auth_cookies_for(db_session, user) -> dict[str, str]:
    return await create_web_auth_cookies(db_session, user=user)


async def test_create_api_key(client: AsyncClient, auth_cookies, project):
    response = await client.post(
        f"/api/v1/projects/{project.project_key}/api-keys/",
        cookies=auth_cookies,
        json={"name": "My API Key"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My API Key"
    assert "key" in data  # Plain key shown once
    assert data["key"].startswith("sk_")


async def test_create_api_key_over_limit(
    client: AsyncClient, auth_cookies, project, monkeypatch
):
    API_KEY_TEST_LIMIT = 2

    monkeypatch.setattr(settings, "API_KEY_PROJECT_LIMIT", API_KEY_TEST_LIMIT)
    for i in range(API_KEY_TEST_LIMIT):
        response = await client.post(
            f"/api/v1/projects/{project.project_key}/api-keys/",
            cookies=auth_cookies,
            json={"name": f"K{i}"},
        )
        assert response.status_code == 201

    # Try to create a 3rd key
    response = await client.post(
        f"/api/v1/projects/{project.project_key}/api-keys/",
        cookies=auth_cookies,
        json={"name": "K3"},
    )

    assert response.status_code == 409


async def test_list_api_keys(client: AsyncClient, auth_cookies, project, db_session):
    await create_api_key(
        db_session,
        project=project,
        name="K1",
        plain_key="sk_test_1",
    )

    response = await client.get(
        f"/api/v1/projects/{project.project_key}/api-keys/", cookies=auth_cookies
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert data["items"][0]["name"] == "K1"
    assert "key" not in data["items"][0]  # Hash shouldn't be leaked


async def test_update_api_key(client: AsyncClient, auth_cookies, project, db_session):
    k, _ = await create_api_key(
        db_session,
        project=project,
        name="Old Name",
    )

    response = await client.patch(
        f"/api/v1/projects/{project.project_key}/api-keys/{k.id}",
        cookies=auth_cookies,
        json={"name": "New Name"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


async def test_rotate_api_key(client: AsyncClient, auth_cookies, project, db_session):
    k, _ = await create_api_key(
        db_session,
        project=project,
        name="To Rotate",
        plain_key="sk_old_123",
    )

    response = await client.post(
        f"/api/v1/projects/{project.project_key}/api-keys/{k.id}/rotate",
        cookies=auth_cookies,
    )
    assert response.status_code == 200
    data = response.json()
    assert "key" in data
    assert data["key"] != "sk_old_123"

    # Check old key is inactive
    await db_session.refresh(k)
    assert not k.is_active


async def test_delete_api_key(client: AsyncClient, auth_cookies, project, db_session):
    # Create two keys
    k1, _ = await create_api_key(
        db_session,
        project=project,
        name="K1",
        plain_key="sk_del_1",
        is_active=True,
    )
    await create_api_key(
        db_session,
        project=project,
        name="K2",
        plain_key="sk_del_2",
        is_active=True,
    )

    response = await client.delete(
        f"/api/v1/projects/{project.project_key}/api-keys/{k1.id}",
        cookies=auth_cookies,
    )
    assert response.status_code == 204


async def test_delete_last_active_key(
    client: AsyncClient, auth_cookies, project, db_session
):
    # Conftest project fixture doesn't create a key.
    # Let's create one.
    k1, _ = await create_api_key(
        db_session,
        project=project,
        name="Last Key",
        is_active=True,
    )

    response = await client.delete(
        f"/api/v1/projects/{project.project_key}/api-keys/{k1.id}",
        cookies=auth_cookies,
    )
    assert response.status_code == 400
    assert "Cannot delete the last active API key" in response.json()["error"]


# ---------------------------------------------------------------------------
# Non-owner access control
# ---------------------------------------------------------------------------


async def _add_non_owner(
    db_session, project, email: str, role: models.ProjectRole
) -> dict[str, str]:
    """Create a user with the given role and return their auth cookies."""
    user = await create_user(db_session, email=email)
    membership = models.UserProject(user_id=user.id, project_id=project.id, role=role)
    db_session.add(membership)
    await db_session.commit()
    return await _auth_cookies_for(db_session, user)


@pytest.mark.parametrize("role", [models.ProjectRole.member, models.ProjectRole.viewer])
async def test_non_owner_cannot_create_api_key(
    client: AsyncClient, project, db_session, role
):
    """Members and viewers cannot create API keys."""
    cookies = await _add_non_owner(
        db_session, project, f"{role.value}-create@example.com", role
    )
    response = await client.post(
        f"/api/v1/projects/{project.project_key}/api-keys/",
        cookies=cookies,
        json={"name": "Forbidden Key"},
    )
    assert response.status_code == 403


@pytest.mark.parametrize("role", [models.ProjectRole.member, models.ProjectRole.viewer])
async def test_non_owner_cannot_update_api_key(
    client: AsyncClient, project, db_session, role
):
    """Members and viewers cannot update API keys."""
    k, _ = await create_api_key(db_session, project=project, name="Existing Key")
    cookies = await _add_non_owner(
        db_session, project, f"{role.value}-update@example.com", role
    )
    response = await client.patch(
        f"/api/v1/projects/{project.project_key}/api-keys/{k.id}",
        cookies=cookies,
        json={"name": "Updated Name"},
    )
    assert response.status_code == 403


@pytest.mark.parametrize("role", [models.ProjectRole.member, models.ProjectRole.viewer])
async def test_non_owner_cannot_rotate_api_key(
    client: AsyncClient, project, db_session, role
):
    """Members and viewers cannot rotate API keys."""
    k, _ = await create_api_key(
        db_session, project=project, name="To Rotate", plain_key="sk_rotate_test"
    )
    cookies = await _add_non_owner(
        db_session, project, f"{role.value}-rotate@example.com", role
    )
    response = await client.post(
        f"/api/v1/projects/{project.project_key}/api-keys/{k.id}/rotate",
        cookies=cookies,
    )
    assert response.status_code == 403


@pytest.mark.parametrize("role", [models.ProjectRole.member, models.ProjectRole.viewer])
async def test_non_owner_cannot_delete_api_key(
    client: AsyncClient, project, db_session, role
):
    """Members and viewers cannot delete API keys."""
    k, _ = await create_api_key(
        db_session, project=project, name="To Delete", plain_key="sk_delete_test"
    )
    # Create a second key so deletion of k would otherwise succeed (not the last key).
    await create_api_key(
        db_session, project=project, name="Other Key", plain_key="sk_other_test"
    )
    cookies = await _add_non_owner(
        db_session, project, f"{role.value}-delete@example.com", role
    )
    response = await client.delete(
        f"/api/v1/projects/{project.project_key}/api-keys/{k.id}",
        cookies=cookies,
    )
    assert response.status_code == 403
