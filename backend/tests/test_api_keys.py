import pytest
from httpx import AsyncClient

from tests.factories import create_api_key

pytestmark = pytest.mark.asyncio


async def test_create_api_key(client: AsyncClient, auth_headers, project):
    response = await client.post(
        f"/api/v1/projects/{project.project_key}/api-keys/",
        headers=auth_headers,
        json={"name": "My API Key"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My API Key"
    assert "key" in data  # Plain key shown once
    assert data["key"].startswith("sk_")


async def test_list_api_keys(client: AsyncClient, auth_headers, project, db_session):
    await create_api_key(
        db_session,
        project=project,
        name="K1",
        plain_key="sk_test_1",
    )

    response = await client.get(
        f"/api/v1/projects/{project.project_key}/api-keys/", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "K1"
    assert "key" not in data[0]  # Hash shouldn't be leaked


async def test_rotate_api_key(client: AsyncClient, auth_headers, project, db_session):
    k, _ = await create_api_key(
        db_session,
        project=project,
        name="To Rotate",
        plain_key="sk_old_123",
    )

    response = await client.post(
        f"/api/v1/projects/{project.project_key}/api-keys/{k.id}/rotate",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "key" in data
    assert data["key"] != "sk_old_123"

    # Check old key is inactive
    await db_session.refresh(k)
    assert not k.is_active


async def test_delete_api_key(client: AsyncClient, auth_headers, project, db_session):
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
        headers=auth_headers,
    )
    assert response.status_code == 204
