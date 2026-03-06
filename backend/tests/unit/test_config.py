import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_security_key_length_production():
    """Test that SECURITY_KEY must be at least 32 characters in production."""
    # Production environment with short key should fail
    with pytest.raises(ValidationError) as excinfo:
        Settings(
            ENVIRONMENT="prod",
            SECURITY_KEY="short",
            PROJECT_USER="test@example.com",
            PROJECT_PASSWORD="password",
            PROJECT_KEY="test",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="user",
        )
    assert "SECURITY_KEY must be at least 32 characters in production" in str(
        excinfo.value
    )


def test_security_key_length_non_production():
    """Test that SECURITY_KEY does not need to be 32 characters in non-production."""
    # Test environment with short key should pass
    settings = Settings(
        ENVIRONMENT="test",
        SECURITY_KEY="short",
        PROJECT_USER="test@example.com",
        PROJECT_PASSWORD="password",
        PROJECT_KEY="test",
        POSTGRES_SERVER="localhost",
        POSTGRES_USER="user",
    )
    assert settings.SECURITY_KEY == "short"


def test_security_key_secure_value_production():
    """Test that SECURITY_KEY must be a secure value in production."""
    # Note: Currently, all blacklisted words are caught by the length check (32 chars).
    # Len validation error takes priority, even for blacklisted words like "changethis"
    with pytest.raises(ValidationError) as excinfo:
        Settings(
            ENVIRONMENT="prod",
            SECURITY_KEY="changethis",
            PROJECT_USER="test@example.com",
            PROJECT_PASSWORD="password",
            PROJECT_KEY="test",
            POSTGRES_SERVER="localhost",
            POSTGRES_USER="user",
        )
    assert "SECURITY_KEY must be at least 32 characters in production" in str(
        excinfo.value
    )
