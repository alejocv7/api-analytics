"""Test doubles for external dependencies."""


class FakeAsyncRedis:
    """In-memory Redis substitute for testing.

    Implements only the methods used by the account-lockout logic so tests
    never need a running Redis server.
    """

    def __init__(self) -> None:
        self._data: dict[str, int] = {}

    async def get(self, key: str) -> str | None:
        val = self._data.get(key)
        return str(val) if val is not None else None

    async def incr(self, key: str) -> int:
        self._data[key] = self._data.get(key, 0) + 1
        return self._data[key]

    async def expire(self, key: str, seconds: int) -> bool:
        return True

    async def delete(self, key: str) -> int:
        return 1 if self._data.pop(key, None) is not None else 0

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        pass
