import pytest
from httpx import AsyncClient

from tests.factories import create_project

pytestmark = pytest.mark.asyncio


async def test_create_project(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/projects/",
        headers=auth_headers,
        json={"name": "Test Project", "description": "Project Description"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Project"
    assert "project_key" in data


async def test_list_projects(client: AsyncClient, auth_headers, test_user, db_session):
    # Create some projects
    await create_project(
        db_session,
        user=test_user,
        name="P1",
        project_key="p1-key",
    )
    await create_project(
        db_session,
        user=test_user,
        name="P2",
        project_key="p2-key",
    )

    response = await client.get("/api/v1/projects/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    names = [p["name"] for p in data]
    assert "P1" in names
    assert "P2" in names


async def test_get_project_by_key(
    client: AsyncClient, auth_headers, test_user, db_session
):
    p = await create_project(
        db_session,
        user=test_user,
        name="Single",
        project_key="single-key",
    )

    response = await client.get(
        f"/api/v1/projects/{p.project_key}", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Single"


async def test_update_project(client: AsyncClient, auth_headers, test_user, db_session):
    p = await create_project(
        db_session,
        user=test_user,
        name="Old Name",
        project_key="old-key",
    )

    response = await client.patch(
        f"/api/v1/projects/{p.project_key}",
        headers=auth_headers,
        json={"name": "New Name"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


async def test_delete_project(client: AsyncClient, auth_headers, test_user, db_session):
    p = await create_project(
        db_session,
        user=test_user,
        name="To Delete",
        project_key="delete-key",
    )

    response = await client.delete(
        f"/api/v1/projects/{p.project_key}", headers=auth_headers
    )
    assert response.status_code == 204

    # Verify gone
    response = await client.get(
        f"/api/v1/projects/{p.project_key}", headers=auth_headers
    )
    assert response.status_code == 404
