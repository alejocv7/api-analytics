from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core import security
from app.core.config import settings
from app.core.exceptions import BearerAuthenticationError
from app.schemas import TokenData


def test_hash_ip():
    ip = "192.168.1.1"
    salt = "test-salt"
    hashed = security.hash_ip(ip, salt)

    assert hashed is not None
    assert len(hashed) == 16
    assert security.hash_ip(ip, salt) == hashed
    assert security.hash_ip("192.168.1.2", salt) != hashed
    assert security.hash_ip(None, salt) is None


def test_generate_api_key():
    full_key, prefix, hashed = security.generate_api_key()

    assert full_key.startswith(settings.API_KEY_PREFIX)
    assert len(full_key) == len(settings.API_KEY_PREFIX) + settings.API_KEY_LENGTH
    assert prefix == full_key[: settings.API_KEY_LOOKUP_PREFIX_LENGTH]
    assert security.compare_api_key(full_key, hashed) is True


def test_password_hashing():
    password = "MySecurePassword123!"
    hashed = security.hash_password(password)

    assert hashed != password

    match, new_hash = security.verify_password(password, hashed)
    assert match is True
    assert new_hash is None or isinstance(new_hash, str)

    match, _ = security.verify_password("wrong-password", hashed)
    assert match is False


# --------------- Access token ----------------


def test_create_access_token_payload():
    """JWT payload uses 'sub' for user identity — no redundant 'user_id' field."""
    token_data = TokenData(user_id=42)
    token = security.create_access_token(token_data)

    payload = jwt.decode(
        token, settings.SECURITY_KEY, algorithms=[settings.SECURITY_ALGORITHM]
    )

    assert payload["sub"] == "42"
    assert "user_id" not in payload
    assert "iat" in payload
    assert "exp" in payload
    assert payload.get("type") is None  # not a refresh token


def test_decode_token_round_trip():
    """decode_token reconstructs TokenData correctly from 'sub'."""
    original = TokenData(user_id=99)
    token = security.create_access_token(original)

    decoded = security.decode_token(token)

    assert decoded.user_id == 99


def test_decode_token_rejects_expired():
    """decode_token raises BearerAuthenticationError for expired tokens."""
    payload = {
        "sub": "1",
        "exp": datetime.now(UTC) - timedelta(seconds=1),
    }
    expired_token = jwt.encode(
        payload, settings.SECURITY_KEY, algorithm=settings.SECURITY_ALGORITHM
    )

    with pytest.raises(BearerAuthenticationError):
        security.decode_token(expired_token)


def test_decode_token_rejects_wrong_signature():
    """decode_token raises BearerAuthenticationError for bad signatures."""
    payload = {
        "sub": "1",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    token = jwt.encode(payload, "wrong-key", algorithm=settings.SECURITY_ALGORITHM)

    with pytest.raises(BearerAuthenticationError):
        security.decode_token(token)


def test_decode_token_rejects_refresh_token():
    """Access-token decoder must not accept refresh tokens."""
    refresh = security.create_refresh_token(user_id=7, token_version=0)

    with pytest.raises(BearerAuthenticationError):
        security.decode_token(refresh)


def test_decode_token_rejects_missing_claims():
    """decode_token raises BearerAuthenticationError when required claims are absent."""
    payload = {
        "something": "else",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    token = jwt.encode(
        payload, settings.SECURITY_KEY, algorithm=settings.SECURITY_ALGORITHM
    )

    with pytest.raises(BearerAuthenticationError):
        security.decode_token(token)


# --------------- Refresh token ----------------


def test_create_refresh_token_payload():
    """Refresh token payload uses 'sub' and 'type: refresh'."""
    token = security.create_refresh_token(user_id=5, token_version=3)

    payload = jwt.decode(
        token, settings.SECURITY_KEY, algorithms=[settings.SECURITY_ALGORITHM]
    )

    assert payload["sub"] == "5"
    assert payload["type"] == "refresh"
    assert payload["rtv"] == 3
    assert "iat" in payload
    assert "exp" in payload


def test_decode_refresh_token_round_trip():
    """decode_refresh_token returns the original user_id."""
    token = security.create_refresh_token(user_id=17, token_version=9)

    decoded = security.decode_refresh_token(token)
    assert decoded.user_id == 17
    assert decoded.token_version == 9


def test_decode_refresh_token_rejects_access_token():
    """Refresh-token decoder must not accept access tokens."""
    token_data = TokenData(user_id=3)
    access_token = security.create_access_token(token_data)

    with pytest.raises(BearerAuthenticationError):
        security.decode_refresh_token(access_token)


def test_decode_refresh_token_rejects_expired():
    """decode_refresh_token raises BearerAuthenticationError for expired tokens."""
    payload = {
        "sub": "1",
        "type": "refresh",
        "exp": datetime.now(UTC) - timedelta(seconds=1),
    }
    expired = jwt.encode(
        payload, settings.SECURITY_KEY, algorithm=settings.SECURITY_ALGORITHM
    )

    with pytest.raises(BearerAuthenticationError):
        security.decode_refresh_token(expired)


def test_decode_refresh_token_rejects_wrong_signature():
    """decode_refresh_token raises BearerAuthenticationError for bad signatures."""
    payload = {
        "sub": "1",
        "type": "refresh",
        "exp": datetime.now(UTC) + timedelta(days=1),
    }
    token = jwt.encode(payload, "wrong-key", algorithm=settings.SECURITY_ALGORITHM)

    with pytest.raises(BearerAuthenticationError):
        security.decode_refresh_token(token)
