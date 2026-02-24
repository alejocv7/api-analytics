import redis.asyncio as redis
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff

from app.core.config import settings


class RedisManager:
    def __init__(self) -> None:
        self.pool: redis.ConnectionPool | None = None
        self.client: redis.Redis | None = None

    def init(self) -> None:
        """Initialize the Redis connection pool and client."""
        if self.client is not None:
            return

        self.pool = redis.ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=settings.REDIS_POOL_SIZE,
            health_check_interval=settings.REDIS_HEALTH_CHECK_INTERVAL,
            retry=Retry(ExponentialBackoff(), 3),
            retry_on_timeout=True,
        )
        self.client = redis.Redis(connection_pool=self.pool)

    async def close(self) -> None:
        """Gracefully close the client and its associated pool."""
        if self.client:
            await self.client.aclose()
            self.client = None
            self.pool = None

    async def is_connected(self) -> bool:
        """Verify Redis connectivity with a ping."""
        if self.client is None:
            return False
        try:
            result = await self.client.ping()  # type: ignore
            return bool(result)
        except redis.RedisError:
            return False


redis_manager = RedisManager()
