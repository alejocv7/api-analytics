from unittest.mock import AsyncMock, patch

import pytest
import redis.asyncio as redis

from app.core.redis import RedisManager


@pytest.mark.asyncio
async def test_redis_manager_init_idempotent():
    manager = RedisManager()

    # First init
    with patch("redis.asyncio.ConnectionPool.from_url") as mock_pool:
        manager.init()
        assert manager.client is not None
        mock_pool.assert_called_once()

        # Second init should return early
        manager.init()
        mock_pool.assert_called_once()


@pytest.mark.asyncio
async def test_redis_manager_close():
    manager = RedisManager()
    with patch("redis.asyncio.ConnectionPool.from_url"):
        manager.init()

    mock_client = AsyncMock()
    manager.client = mock_client

    await manager.close()
    mock_client.aclose.assert_awaited_once()
    assert manager.client is None
    assert manager.pool is None


@pytest.mark.asyncio
async def test_redis_manager_is_connected():
    manager = RedisManager()

    # Case 1: Client is None
    assert await manager.is_connected() is False

    # Case 2: Client.ping() returns True
    mock_client = AsyncMock()
    mock_client.ping.return_value = True
    manager.client = mock_client
    assert await manager.is_connected() is True

    # Case 3: Client.ping() raises RedisError
    mock_client.ping.side_effect = redis.RedisError("Down")
    assert await manager.is_connected() is False
