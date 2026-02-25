import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app import dependencies
from app.core.exceptions import BearerAuthenticationError, ForbiddenError


@pytest.mark.asyncio
async def test_get_redis_raises_when_not_initialized():
    with (
        patch("app.dependencies.redis_manager", client=None),
        pytest.raises(RuntimeError, match="not initialized"),
    ):
        # dependencies.get_redis is an async generator
        async for _ in dependencies.get_redis():
            pass


@pytest.mark.asyncio
async def test_get_current_user_inactive():
    session = AsyncMock()
    user = MagicMock(is_active=False)
    session.get.return_value = user

    with (
        patch(
            "app.core.security.decode_token",
            return_value=MagicMock(user_id=uuid.uuid4()),
        ),
        pytest.raises(ForbiddenError, match="Inactive user"),
    ):
        await dependencies.get_current_user(MagicMock(), session, "valid-token")


@pytest.mark.asyncio
async def test_get_current_user_not_found():
    session = AsyncMock()
    session.get.return_value = None

    with (
        patch(
            "app.core.security.decode_token",
            return_value=MagicMock(user_id=uuid.uuid4()),
        ),
        pytest.raises(BearerAuthenticationError, match="credentials"),
    ):
        await dependencies.get_current_user(MagicMock(), session, "valid-token")
