import pytest
from httpx import AsyncClient

from app.core.config import settings
from tests.factories import create_project

pytestmark = pytest.mark.asyncio


async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == settings.PROJECT_NAME
    assert data["description"] == settings.PROJECT_DESCRIPTION
    assert "version" in data
    assert "docs" in data
    assert "openapi" in data


async def test_pagination_fields(
    client: AsyncClient, auth_cookies, test_user, db_session
):
    # Create 3 projects
    for i in range(3):
        await create_project(
            db_session,
            user=test_user,
            name=f"Project {i}",
        )

    # Request page 1 with page_size 2
    response = await client.get(
        "/api/v1/projects",
        cookies=auth_cookies,
        params={"page": 1, "page_size": 2},
    )
    assert response.status_code == 200
    data = response.json()

    # Check pagination fields
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] == 3
    assert data["has_next"] is True
    assert data["has_previous"] is False
    assert len(data["items"]) == 2

    # Request page 2 with page_size 2
    response = await client.get(
        "/api/v1/projects",
        cookies=auth_cookies,
        params={"page": 2, "page_size": 2},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["page"] == 2
    assert data["has_next"] is False
    assert data["has_previous"] is True
    assert len(data["items"]) == 1
