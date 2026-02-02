import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient, auth_headers, test_user, db_session):
    from app import models

    # Create some projects
    p1 = models.Project(name="P1", project_key="p1-key", user_id=test_user.id)
    p2 = models.Project(name="P2", project_key="p2-key", user_id=test_user.id)
    db_session.add_all([p1, p2])
    await db_session.commit()

    response = await client.get("/api/v1/projects/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    names = [p["name"] for p in data]
    assert "P1" in names
    assert "P2" in names


@pytest.mark.asyncio
async def test_get_project_by_key(
    client: AsyncClient, auth_headers, test_user, db_session
):
    from app import models

    p = models.Project(name="Single", project_key="single-key", user_id=test_user.id)
    db_session.add(p)
    await db_session.commit()

    response = await client.get(
        f"/api/v1/projects/{p.project_key}", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Single"


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient, auth_headers, test_user, db_session):
    from app import models

    p = models.Project(name="Old Name", project_key="old-key", user_id=test_user.id)
    db_session.add(p)
    await db_session.commit()

    response = await client.patch(
        f"/api/v1/projects/{p.project_key}",
        headers=auth_headers,
        json={"name": "New Name"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient, auth_headers, test_user, db_session):
    from app import models

    p = models.Project(name="To Delete", project_key="delete-key", user_id=test_user.id)
    db_session.add(p)
    await db_session.commit()

    response = await client.delete(
        f"/api/v1/projects/{p.project_key}", headers=auth_headers
    )
    assert response.status_code == 204

    # Verify gone
    response = await client.get(
        f"/api/v1/projects/{p.project_key}", headers=auth_headers
    )
    assert response.status_code == 404
