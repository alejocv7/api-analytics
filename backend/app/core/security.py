import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import status
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import ValidationError
from zxcvbn import zxcvbn

from app import schemas
from app.core.config import settings
from app.core.exceptions import APIError

password_hash = PasswordHash.recommended()


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


def validate_password(password: str) -> str:
    """Validate password meets security requirements."""
    result = zxcvbn(password)
    if result["score"] < 3:
        feedback = ", ".join(result["feedback"]["suggestions"])
        raise ValueError(f"Password is too weak. Suggestions: {feedback}")

    return password


# --------------- JWT Token ----------------
def create_access_token(token_data: schemas.TokenData) -> str:
    """Create a JWT access token."""
    now = datetime.now(timezone.utc)
    payload = {
        **token_data.model_dump(),
        "sub": str(token_data.user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    return jwt.encode(
        payload, settings.SECURITY_KEY, algorithm=settings.SECURITY_ALGORITHM
    )


def decode_token(token: str) -> schemas.TokenData:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token, settings.SECURITY_KEY, algorithms=[settings.SECURITY_ALGORITHM]
        )
        return schemas.TokenData(**payload)

    except (InvalidTokenError, ValidationError):
        raise APIError(
            status_code=status.HTTP_403_FORBIDDEN,
            message="Invalid authentication credentials",
        )
