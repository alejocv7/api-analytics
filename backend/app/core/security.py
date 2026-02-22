import hashlib
import hmac
import logging
import secrets
from datetime import UTC, datetime, timedelta

import jwt
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import ValidationError
from zxcvbn import zxcvbn

from app.core.config import settings
from app.core.exceptions import BearerAuthenticationError
from app.core.types import SecurePassword
from app.schemas import RefreshTokenData, TokenData

password_hash = PasswordHash.recommended()
logger = logging.getLogger(__name__)


# --------------- IP ----------------
def hash_ip(ip: str | None, salt: str) -> str | None:
    """
    Hashes an IP address using HMAC-SHA256.
    Returns the first 16 characters of the hex digest.
    """
    if not ip:
        return None

    hash_obj = hmac.new(salt.encode(), msg=ip.encode(), digestmod=hashlib.sha256)
    return hash_obj.hexdigest()[:16]


# --------------- API Key ----------------
def generate_api_key() -> tuple[str, str, str]:
    """
    Generates a random API key.
    """
    random_part = secrets.token_urlsafe(settings.API_KEY_LENGTH)[
        : settings.API_KEY_LENGTH
    ]
    full_key = f"{settings.API_KEY_PREFIX}{random_part}"
    key_prefix = full_key[: settings.API_KEY_LOOKUP_PREFIX_LENGTH]

    return full_key, key_prefix, hash_api_key(full_key)


def hash_api_key(api_key: str) -> str:
    """
    Hashes an API key using SHA256.
    """
    return hmac.new(
        settings.SECURITY_KEY.encode(), msg=api_key.encode(), digestmod=hashlib.sha256
    ).hexdigest()


def compare_api_key(plain_api_key: str, hashed_api_key: str) -> bool:
    """
    Compares an API key with its hash.
    """
    return hmac.compare_digest(hash_api_key(plain_api_key), hashed_api_key)


# --------------- Password ----------------
def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return password_hash.hash(password)


def verify_password(
    plain_password: str, hashed_password: str
) -> tuple[bool, str | None]:
    """Verify a password against a hash."""
    return password_hash.verify_and_update(plain_password, hashed_password)


def validate_password(password: SecurePassword) -> SecurePassword:
    """Validate password meets security requirements."""
    result = zxcvbn(password.get_secret_value())
    if result["score"] < 3:
        feedback = ", ".join(result["feedback"]["suggestions"])
        raise ValueError(f"Password is too weak. Suggestions: {feedback}")

    return password


# --------------- JWT Token ----------------
def create_access_token(token_data: TokenData) -> str:
    """Create a JWT access token."""
    now = datetime.now(UTC)
    payload = {
        "sub": str(token_data.user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(
        payload, settings.SECURITY_KEY, algorithm=settings.SECURITY_ALGORITHM
    )


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token, settings.SECURITY_KEY, algorithms=[settings.SECURITY_ALGORITHM]
        )

        if payload.get("type") == "refresh":
            raise BearerAuthenticationError("Invalid token type")

        return TokenData(user_id=int(payload["sub"]))

    except (InvalidTokenError, ValidationError, KeyError, ValueError) as e:
        logger.warning("Invalid token: %s", e)
        raise BearerAuthenticationError("Invalid authentication credentials") from None


def create_refresh_token(user_id: int, token_version: int) -> str:
    """Create a long-lived JWT refresh token.

    Refresh tokens carry only the user identity and a 'type: refresh' claim
    so they cannot be confused with access tokens.
    """
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "rtv": token_version,
        "iat": now,
        "exp": now + timedelta(days=settings.SECURITY_REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(
        payload, settings.SECURITY_KEY, algorithm=settings.SECURITY_ALGORITHM
    )


def decode_refresh_token(token: str) -> RefreshTokenData:
    """Decode and validate a JWT refresh token. Returns the user_id."""
    try:
        payload = jwt.decode(
            token, settings.SECURITY_KEY, algorithms=[settings.SECURITY_ALGORITHM]
        )

        if payload.get("type") != "refresh":
            raise BearerAuthenticationError("Invalid token type")

        return RefreshTokenData(
            user_id=int(payload["sub"]),
            token_version=int(payload["rtv"]),
        )

    except (InvalidTokenError, ValidationError, KeyError, ValueError) as e:
        logger.warning("Invalid refresh token: %s", e)
        raise BearerAuthenticationError("Invalid authentication credentials") from None
