from typing import Any

import pytest
from pydantic import ValidationError

from app.core.config import Settings

_VALID_KEY = "abcdefghij" + "a" * 22  # at least 10 unique chars, 32 total
_BASE_SETTINGS: dict[str, Any] = {
    "SECURITY_KEY": _VALID_KEY,
    "PROJECT_USER": "test@example.com",
    "PROJECT_PASSWORD": "password",
    "PROJECT_ID": "00000000-0000-0000-0000-000000000000",
    "POSTGRES_SERVER": "localhost",
    "POSTGRES_USER": "user",
    "POSTGRES_PASSWORD": "password",
    "REDIS_PASSWORD": "password",
    "POSTGRES_SSL": True,
    "REDIS_SSL": True,
}


def test_security_key_min_length():
    """Test that SECURITY_KEY must be at least 32 characters in all environments."""
    with pytest.raises(ValidationError) as excinfo:
        Settings(
            ENVIRONMENT="test",
            SECURITY_KEY="short",
            PROJECT_USER="test@example.com",
            PROJECT_PASSWORD="password",
            PROJECT_ID="00000000-0000-0000-0000-000000000000",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="user",
        )
    assert "String should have at least 32 characters" in str(excinfo.value)


def test_security_key_exactly_32_chars():
    """Test that a SECURITY_KEY of exactly 32 characters is accepted."""
    settings = Settings(ENVIRONMENT="test", **_BASE_SETTINGS)
    assert len(settings.SECURITY_KEY) == 32


def test_enable_self_metrics_can_be_disabled():
    settings = Settings(ENVIRONMENT="test", ENABLE_SELF_METRICS=False, **_BASE_SETTINGS)
    assert settings.ENABLE_SELF_METRICS is False


def test_enforce_non_default_secrets_local():
    """Test that default secrets trigger a warning in local environment."""
    with pytest.warns(
        UserWarning, match='The value of PROJECT_PASSWORD is "changethis"'
    ):
        settings = Settings(
            ENVIRONMENT="local",
            **{**_BASE_SETTINGS, "PROJECT_PASSWORD": "changethis"},
        )
    assert settings.PROJECT_PASSWORD == "changethis"


@pytest.mark.parametrize("env", ["test", "staging", "prod"])
@pytest.mark.parametrize(
    "field_name,override",
    [
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


def test_redis_url_ssl_scheme():
    """Test that REDIS_URL uses 'rediss' only when REDIS_SSL is True."""
    settings = Settings(ENVIRONMENT="test", **{**_BASE_SETTINGS, "REDIS_SSL": False})
    assert settings.REDIS_URL.startswith("redis://")

    settings = Settings(ENVIRONMENT="test", **{**_BASE_SETTINGS, "REDIS_SSL": True})
    assert settings.REDIS_URL.startswith("rediss://")


@pytest.mark.parametrize("env", ["staging", "prod"])
def test_enforce_ssl_in_remote_envs(env: str):
    """Test that prod/staging environments require SSL to be True."""
    # Both True (default) -> Success
    settings = Settings(ENVIRONMENT=env, **_BASE_SETTINGS)
    assert settings.POSTGRES_SSL is True
    assert settings.REDIS_SSL is True

    # Explicitly setting one to False -> Error
    with pytest.raises(ValidationError) as excinfo:
        Settings(ENVIRONMENT=env, **{**_BASE_SETTINGS, "POSTGRES_SSL": False})
    assert "POSTGRES_SSL must be True" in str(excinfo.value)

    with pytest.raises(ValidationError) as excinfo:
        Settings(ENVIRONMENT=env, **{**_BASE_SETTINGS, "REDIS_SSL": False})
    assert "REDIS_SSL must be True" in str(excinfo.value)


def test_security_key_entropy_remote_envs():
    """Test that SECURITY_KEY must have >= 10 unique chars in remote envs (M8)."""
    low_entropy_key = "a" * 32
    with pytest.raises(ValidationError) as excinfo:
        Settings(
            ENVIRONMENT="prod",
            **{**_BASE_SETTINGS, "SECURITY_KEY": low_entropy_key},
        )
    assert "entropy" in str(excinfo.value)

    # Local env should still allow low entropy for dev convenience
    settings = Settings(
        ENVIRONMENT="local", **{**_BASE_SETTINGS, "SECURITY_KEY": low_entropy_key}
    )
    assert low_entropy_key == settings.SECURITY_KEY


def test_security_algorithm_restriction():
    """Test that only HS256, HS384, HS512 are allowed (M9)."""
    # Valid
    for alg in ["HS256", "HS384", "HS512"]:
        settings = Settings(
            ENVIRONMENT="test", SECURITY_ALGORITHM=alg, **_BASE_SETTINGS
        )
        assert alg == settings.SECURITY_ALGORITHM

    # Invalid
    with pytest.raises(ValidationError) as excinfo:
        Settings(ENVIRONMENT="test", SECURITY_ALGORITHM="none", **_BASE_SETTINGS)
    assert "Input should be 'HS256', 'HS384' or 'HS512'" in str(excinfo.value)

    with pytest.raises(ValidationError):
        Settings(ENVIRONMENT="test", SECURITY_ALGORITHM="RS256", **_BASE_SETTINGS)
