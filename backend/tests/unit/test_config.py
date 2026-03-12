import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_security_key_generation(monkeypatch):
    """Test that SECURITY_KEY is generated automatically if not provided."""
    monkeypatch.delenv("SECURITY_KEY", raising=False)
    settings = Settings(
        ENVIRONMENT="test",
        PROJECT_USER="test@example.com",
        PROJECT_PASSWORD="password",
        PROJECT_KEY="test",
        POSTGRES_SERVER="localhost",
        POSTGRES_USER="user",
    )
    assert settings.SECURITY_KEY is not None
    assert len(settings.SECURITY_KEY) >= 32


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


def test_enforce_non_default_secrets_non_local():
    """Test that default secrets are not allowed in non-local environments."""
    with pytest.raises(ValidationError) as excinfo:
        Settings(
            ENVIRONMENT="test",
            PROJECT_KEY="changethis",
            PROJECT_USER="test@example.com",
            PROJECT_PASSWORD="password",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="user",
        )
    assert 'The value of PROJECT_KEY is "changethis"' in str(excinfo.value)


def test_enforce_non_default_secrets_local():
    """Test that default secrets trigger a warning in local environment."""
    with pytest.warns(UserWarning, match='The value of PROJECT_KEY is "changethis"'):
        Settings(
            ENVIRONMENT="local",
            PROJECT_KEY="changethis",
            PROJECT_USER="test@example.com",
            PROJECT_PASSWORD="password",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="user",
        )
