import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture
async def test_project(db_session, test_user):
    from app import models

    project = models.Project(
        name="PK Project", project_key="pk-key", user_id=test_user.id
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_create_api_key(client: AsyncClient, auth_headers, test_project):
    response = await client.post(
        f"/api/v1/projects/{test_project.project_key}/api-keys/",
        headers=auth_headers,
        json={"name": "My API Key"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My API Key"
    assert "key" in data  # Plain key shown once
    assert data["key"].startswith("sk_")


@pytest.mark.asyncio
async def test_list_api_keys(
    client: AsyncClient, auth_headers, test_project, db_session
):
    from app import models
    from app.core import security

    k1 = models.APIKey(
        name="K1",
        key_hash=security.hash_api_key("sk_test_1"),
        key_prefix="sk_test_1"[:8],
        project_id=test_project.id,
    )
    db_session.add(k1)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/projects/{test_project.project_key}/api-keys/", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["name"] == "K1"
    assert "key" not in data[0]  # Hash shouldn't be leaked


@pytest.mark.asyncio
async def test_rotate_api_key(
    client: AsyncClient, auth_headers, test_project, db_session
):
    from app import models
    from app.core import security

    k = models.APIKey(
        name="To Rotate",
        key_hash=security.hash_api_key("sk_old_123"),
        key_prefix="sk_old_123"[:8],
        project_id=test_project.id,
    )
    db_session.add(k)
    await db_session.commit()
    await db_session.refresh(k)

    response = await client.post(
        f"/api/v1/projects/{test_project.project_key}/api-keys/{k.id}/rotate",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "key" in data
    assert data["key"] != "sk_old_123"

    # Check old key is inactive
    await db_session.refresh(k)
    assert not k.is_active


@pytest.mark.asyncio
async def test_delete_api_key(
    client: AsyncClient, auth_headers, test_project, db_session
):
    from app import models
    from app.core import security

    # Create two keys
    k1 = models.APIKey(
        name="K1",
        key_hash=security.hash_api_key("sk_del_1"),
        key_prefix="sk_del_1"[:8],
        project_id=test_project.id,
        is_active=True,
    )
    k2 = models.APIKey(
        name="K2",
        key_hash=security.hash_api_key("sk_del_2"),
        key_prefix="sk_del_2"[:8],
        project_id=test_project.id,
        is_active=True,
    )
    db_session.add_all([k1, k2])
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/projects/{test_project.project_key}/api-keys/{k1.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204
