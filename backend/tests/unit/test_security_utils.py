import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core import security
from app.core.config import settings
from app.core.exceptions import AuthenticationError, BearerAuthenticationError
from app.core.types import SecurePassword
from app.schemas import TokenData


def test_hash_ip():
    ip = "192.168.1.1"
    hashed = security.hash_ip(ip)

    assert hashed is not None
    assert len(hashed) == 16
    assert security.hash_ip(ip) == hashed
    assert security.hash_ip("192.168.1.2") != hashed
    assert security.hash_ip(None) is None


def test_generate_api_key():
    full_key, prefix, hashed = security.generate_api_key()

    assert full_key.startswith(settings.API_KEY_PREFIX)
    assert len(full_key) == len(settings.API_KEY_PREFIX) + settings.API_KEY_LENGTH
    assert prefix == full_key[: settings.API_KEY_LOOKUP_PREFIX_LENGTH]
    assert security.compare_auth_secret(full_key, hashed) is True


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
    uid = uuid.uuid4()
    sid = uuid.uuid4()
    token_data = TokenData(user_id=uid, session_id=sid)
    token = security.create_access_token(token_data)

    payload = jwt.decode(
        token, settings.SECURITY_KEY, algorithms=[settings.SECURITY_ALGORITHM]
    )

    assert payload["sub"] == str(uid)
    assert payload["sid"] == str(sid)
    assert "user_id" not in payload
    assert "iat" in payload
    assert "exp" in payload
    assert payload["type"] == "access"


def test_decode_token_round_trip():
    """decode_token reconstructs TokenData correctly from 'sub'."""
    uid = uuid.uuid4()
    sid = uuid.uuid4()
    original = TokenData(user_id=uid, session_id=sid)
    token = security.create_access_token(original)

    decoded = security.decode_token(token)

    assert decoded.user_id == uid
    assert decoded.session_id == sid


def test_decode_token_rejects_expired():
    """decode_token raises BearerAuthenticationError for expired tokens."""
    payload = {
        "sub": "1",
        "sid": str(uuid.uuid4()),
        "type": "access",
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
        "sid": str(uuid.uuid4()),
        "type": "access",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    token = jwt.encode(
        payload,
        "wrong-key-that-is-at-least-32-bytes-long",
        algorithm=settings.SECURITY_ALGORITHM,
    )

    with pytest.raises(BearerAuthenticationError):
        security.decode_token(token)


def test_decode_token_rejects_refresh_token():
    """Access-token decoder must not accept refresh tokens."""
    refresh = security.create_refresh_token(uuid.uuid4(), "secret")

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
    """Opaque refresh tokens use a stable session id prefix."""
    session_id = uuid.uuid4()
    token = security.create_refresh_token(session_id=session_id, secret="secret")
    assert token == f"{session_id}.secret"


def test_decode_refresh_token_round_trip():
    """decode_refresh_token returns the session id and secret."""
    session_id = uuid.uuid4()
    token = security.create_refresh_token(session_id=session_id, secret="secret")

    decoded = security.decode_refresh_token(token)
    assert decoded.session_id == session_id
    assert decoded.secret == "secret"


def test_decode_refresh_token_rejects_access_token():
    """Refresh-token decoder must not accept access tokens."""
    token_data = TokenData(user_id=uuid.uuid4(), session_id=uuid.uuid4())
    access_token = security.create_access_token(token_data)

    with pytest.raises(AuthenticationError):
        security.decode_refresh_token(access_token)


def test_decode_refresh_token_rejects_expired():
    """decode_refresh_token rejects malformed opaque refresh tokens."""
    with pytest.raises(AuthenticationError):
        security.decode_refresh_token("not-a-session-id")


def test_decode_refresh_token_rejects_wrong_signature():
    """decode_refresh_token rejects tokens with an invalid session id prefix."""
    with pytest.raises(AuthenticationError):
        security.decode_refresh_token("not-a-uuid.secret")


def test_validate_password():
    # Weak password
    with pytest.raises(ValueError, match="too weak"):
        security.validate_password(SecurePassword("password"))

    # Strong password
    p = SecurePassword("CorrectHorseBatteryStaple123!")
    assert security.validate_password(p) == p


# ---------------------------------------------------------------------------
# Dummy API key hash (M3)
# ---------------------------------------------------------------------------


def test_dummy_api_key_hash_is_64_hex_chars():
    """SECURITY_DUMMY_API_KEY_HASH must be a valid HMAC-SHA256 hex digest (64 chars)."""
    dummy = settings.SECURITY_DUMMY_API_KEY_HASH
    assert len(dummy) == 64, f"Expected 64 chars, got {len(dummy)}"
    assert all(c in "0123456789abcdef" for c in dummy), (
        "Expected lowercase hex characters only"
    )


def test_dummy_api_key_hash_compare_digest_runs_and_returns_false():
    """compare_auth_secret must not crash and must return False when the stored
    hash is SECURITY_DUMMY_API_KEY_HASH — confirming equal-length comparison."""
    result = security.compare_auth_secret(
        "sk_live_invalid_key_that_does_not_exist",
        settings.SECURITY_DUMMY_API_KEY_HASH,
    )
    assert result is False
