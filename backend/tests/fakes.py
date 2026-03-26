"""Test doubles for external dependencies."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any


class FakePipeline:
    """Fake Redis pipeline for testing."""

    def __init__(self, redis: FakeAsyncRedis) -> None:
        self.redis = redis
        self.commands: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def incr(self, key: str) -> None:
        self.commands.append(("incr", (key,), {}))

    def expire(self, key: str, seconds: int, **kwargs: Any) -> None:
        self.commands.append(("expire", (key, seconds), kwargs))

    async def execute(self) -> list[bool | int]:
        results = []
        for cmd, args, kwargs in self.commands:
            if cmd == "incr":
                results.append(await self.redis.incr(args[0]))
            elif cmd == "expire":
                nx = kwargs.get("nx", False)
                key = args[0]
                # If nx=True and key already has expiration, don't call expire
                if nx and key in self.redis._expirations:
                    results.append(False)
                else:
                    result = await self.redis.expire(key, args[1], nx=nx)
                    results.append(result)
        self.commands.clear()
        return results


class FakeAsyncRedis:
    """In-memory Redis substitute for testing.

    Implements only the methods used by the account-lockout logic so tests
    never need a running Redis server.
    """

    def __init__(self) -> None:
        self._data: dict[str, int] = {}
        self._expirations: set[str] = set()

    async def get(self, key: str) -> str | None:
        val = self._data.get(key)
        return str(val) if val is not None else None

    async def incr(self, key: str) -> int:
        self._data[key] = self._data.get(key, 0) + 1
        return self._data[key]

    async def expire(self, key: str, seconds: int, nx: bool = False) -> bool:
        if nx and key in self._expirations:
            return False
        self._expirations.add(key)
        return True

    async def delete(self, key: str) -> int:
        self._expirations.discard(key)
        return 1 if self._data.pop(key, None) is not None else 0

    async def ping(self) -> bool:
        return True

    async def aclose(self) -> None:
        pass

    @asynccontextmanager
    async def pipeline(self, **kwargs: object) -> AsyncIterator[FakePipeline]:
        """Return a context manager for pipelined commands."""
        pipe = FakePipeline(self)
        try:
            yield pipe
        finally:
            pass
