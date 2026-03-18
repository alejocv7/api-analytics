import pytest
from httpx import AsyncClient

from tests.factories import create_api_key, create_project, create_user

pytestmark = pytest.mark.asyncio


async def test_create_project(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/projects/",
        headers=auth_headers,
        json={"name": "Test Project", "description": "Project Description"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["project_key"] == "test-project"
    # A freshly created project has the owner as its sole member and no API keys.
    assert data["member_count"] == 1
    assert data["api_key_count"] == 0


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
    assert data["total"] >= 2
    names = [p["name"] for p in data["items"]]
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
    assert response.json()["member_count"] == 1
    assert response.json()["api_key_count"] == 0


async def test_get_nonexistent_project(client: AsyncClient, auth_headers):
    response = await client.get("/api/v1/projects/nonexistent", headers=auth_headers)
    assert response.status_code == 404


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


async def test_update_project_duplicate_name(
    client: AsyncClient, auth_headers, test_user, db_session
):
    await create_project(
        db_session,
        user=test_user,
        name="Project A",
        project_key="a-key",
    )
    p2 = await create_project(
        db_session,
        user=test_user,
        name="Project B",
        project_key="b-key",
    )

    response = await client.patch(
        f"/api/v1/projects/{p2.project_key}",
        headers=auth_headers,
        json={"name": "Project A"},
    )
    assert response.status_code == 409
    assert "Project name already in use" in response.json()["error"]


async def test_project_counts_reflect_api_keys(
    client: AsyncClient, auth_headers, test_user, db_session
):
    p = await create_project(
        db_session, user=test_user, name="Counted", project_key="counted-key"
    )
    await create_api_key(db_session, project=p, name="Key 1")
    await create_api_key(db_session, project=p, name="Key 2")

    response = await client.get(
        f"/api/v1/projects/{p.project_key}", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["api_key_count"] == 2
    assert response.json()["member_count"] == 1


async def test_project_counts_reflect_members(
    client: AsyncClient, auth_headers, test_user, db_session
):
    from app import models
    from app.core.enums import ProjectRole

    p = await create_project(
        db_session, user=test_user, name="Multi Member", project_key="multi-member-key"
    )
    extra_user = await create_user(
        db_session, email="member@example.com", full_name="Extra Member"
    )
    db_session.add(
        models.UserProject(
            user_id=extra_user.id, project_id=p.id, role=ProjectRole.member
        )
    )
    await db_session.commit()

    response = await client.get(
        f"/api/v1/projects/{p.project_key}", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["member_count"] == 2
    assert response.json()["api_key_count"] == 0


async def test_list_projects_includes_counts(
    client: AsyncClient, auth_headers, test_user, db_session
):
    p = await create_project(
        db_session, user=test_user, name="Listed", project_key="listed-key"
    )
    await create_api_key(db_session, project=p, name="Key A")

    response = await client.get("/api/v1/projects/", headers=auth_headers)
    assert response.status_code == 200
    listed = next(
        i for i in response.json()["items"] if i["project_key"] == "listed-key"
    )
    assert listed["member_count"] == 1
    assert listed["api_key_count"] == 1


async def test_update_project_returns_counts(
    client: AsyncClient, auth_headers, test_user, db_session
):
    p = await create_project(
        db_session,
        user=test_user,
        name="Before Update",
        project_key="update-counts-key",
    )
    await create_api_key(db_session, project=p, name="My Key")

    response = await client.patch(
        f"/api/v1/projects/{p.project_key}",
        headers=auth_headers,
        json={"name": "After Update"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "After Update"
    assert data["member_count"] == 1
    assert data["api_key_count"] == 1


async def test_create_project_name_at_max_length(client: AsyncClient, auth_headers):
    name = "A" * 40
    response = await client.post(
        "/api/v1/projects/",
        headers=auth_headers,
        json={"name": name},
    )
    assert response.status_code == 201
    assert response.json()["name"] == name


async def test_create_project_name_exceeds_max_length(
    client: AsyncClient, auth_headers
):
    response = await client.post(
        "/api/v1/projects/",
        headers=auth_headers,
        json={"name": "A" * 41},
    )
    assert response.status_code == 422


async def test_update_project_name_exceeds_max_length(
    client: AsyncClient, auth_headers, test_user, db_session
):
    p = await create_project(
        db_session,
        user=test_user,
        name="Valid Name",
        project_key="valid-name-key",
    )
    response = await client.patch(
        f"/api/v1/projects/{p.project_key}",
        headers=auth_headers,
        json={"name": "A" * 41},
    )
    assert response.status_code == 422


async def test_rename_project_updates_project_key(
    client: AsyncClient, auth_headers, test_user, db_session
):
    p = await create_project(
        db_session,
        user=test_user,
        name="Original Name",
        project_key="original-name",
    )

    response = await client.patch(
        f"/api/v1/projects/{p.project_key}",
        headers=auth_headers,
        json={"name": "Renamed Project"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Renamed Project"
    assert data["project_key"] == "renamed-project"

    # New key is accessible
    response = await client.get(
        "/api/v1/projects/renamed-project", headers=auth_headers
    )
    assert response.status_code == 200

    # Old key is gone
    response = await client.get(
        "/api/v1/projects/original-name", headers=auth_headers
    )
    assert response.status_code == 404


async def test_create_project_case_insensitive_name_conflict(
    client: AsyncClient, auth_headers, test_user, db_session
):
    await create_project(
        db_session,
        user=test_user,
        name="My API",
        project_key="my-api",
    )

    # "my api" normalizes to "my api", same as "My API"
    response = await client.post(
        "/api/v1/projects/",
        headers=auth_headers,
        json={"name": "my api"},
    )
    assert response.status_code == 409
    assert "already in use" in response.json()["error"]


async def test_rename_project_case_insensitive_name_conflict(
    client: AsyncClient, auth_headers, test_user, db_session
):
    await create_project(
        db_session,
        user=test_user,
        name="My API",
        project_key="my-api",
    )
    p2 = await create_project(
        db_session,
        user=test_user,
        name="Other Project",
        project_key="other-project",
    )

    # "MY API" normalizes to "my api", same as existing "My API"
    response = await client.patch(
        f"/api/v1/projects/{p2.project_key}",
        headers=auth_headers,
        json={"name": "MY API"},
    )
    assert response.status_code == 409
    assert "already in use" in response.json()["error"]


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
