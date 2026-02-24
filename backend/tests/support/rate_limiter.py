from typing import Any, cast

from limits.storage import storage_from_string

from app.core.rate_limiter import limiter


def configure_test_limiter_storage(storage_uri: str) -> None:
    """Test-only helper to swap SlowAPI storage while keeping route bindings."""
    limiter_any = cast(Any, limiter)

    storage = storage_from_string(storage_uri, **limiter_any._storage_options)
    limiter_any._storage_uri = storage_uri
    limiter_any._storage = storage
    limiter_any._limiter = limiter_any._limiter.__class__(storage)
    limiter_any._storage_dead = False
