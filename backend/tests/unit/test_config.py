from typing import Any

import pytest
from pydantic import ValidationError

from app.core.config import Settings

_VALID_KEY = "a" * 32  # exactly 32 chars, meets min_length
_BASE_SETTINGS: dict[str, Any] = {
    "SECURITY_KEY": _VALID_KEY,
    "PROJECT_USER": "test@example.com",
    "PROJECT_PASSWORD": "password",
    "PROJECT_KEY": "test",
    "POSTGRES_SERVER": "localhost",
    "POSTGRES_USER": "user",
}


def test_security_key_min_length():
    """Test that SECURITY_KEY must be at least 32 characters in all environments."""
    with pytest.raises(ValidationError) as excinfo:
        Settings(
            ENVIRONMENT="test",
            SECURITY_KEY="short",
            PROJECT_USER="test@example.com",
            PROJECT_PASSWORD="password",
            PROJECT_KEY="test",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="user",
        )
    assert "String should have at least 32 characters" in str(excinfo.value)


def test_security_key_exactly_32_chars():
    """Test that a SECURITY_KEY of exactly 32 characters is accepted."""
    settings = Settings(ENVIRONMENT="test", **_BASE_SETTINGS)
    assert len(settings.SECURITY_KEY) == 32


def test_enforce_non_default_secrets_local():
    """Test that default secrets trigger a warning in local environment."""
    with pytest.warns(UserWarning, match='The value of PROJECT_KEY is "changethis"'):
        settings = Settings(
            ENVIRONMENT="local",
            **{**_BASE_SETTINGS, "PROJECT_KEY": "changethis"},
        )
    assert settings.PROJECT_KEY == "changethis"


@pytest.mark.parametrize("env", ["test", "staging", "prod"])
@pytest.mark.parametrize(
    "field_name,override",
    [
        ("PROJECT_KEY", {"PROJECT_KEY": "changethis"}),
        ("PROJECT_PASSWORD", {"PROJECT_PASSWORD": "changethis"}),
        ("POSTGRES_PASSWORD", {"POSTGRES_PASSWORD": "changethis"}),
        ("REDIS_PASSWORD", {"REDIS_PASSWORD": "changethis"}),
    ],
)
def test_enforce_non_default_secrets(
    env: str, field_name: str, override: dict[str, str]
) -> None:
    """
    Test that all non-local environments reject 'changethis'
    for each monitored field.
    """
    with pytest.raises(ValidationError) as excinfo:
        Settings(ENVIRONMENT=env, **{**_BASE_SETTINGS, **override})
    assert f'The value of {field_name} is "changethis"' in str(excinfo.value)
