import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import HTTPException, status
from jwt import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import ValidationError

from app import schemas
from app.core.config import settings

password_hash = PasswordHash.recommended()


def hash_ip(ip: str | None, salt: str) -> str | None:
    """
    Hashes an IP address using HMAC-SHA256.
    Returns the first 16 characters of the hex digest.
    """
    if not ip:
        return None

    hash_obj = hmac.new(salt.encode(), msg=ip.encode(), digestmod=hashlib.sha256)
    return hash_obj.hexdigest()[:16]


def hash_api_key(api_key: str) -> str:
    """
    Hashes an API key using SHA256.
    """
    return hmac.new(
        settings.SECURITY_KEY.encode(), msg=api_key.encode(), digestmod=hashlib.sha256
    ).hexdigest()


def hash_password(password: str) -> str:
    """Hash a password for storage."""
    return password_hash.hash(password)


def verify_password(
    plain_password: str, hashed_password: str
) -> tuple[bool, str | None]:
    """Verify a password against a hash."""
    return password_hash.verify_and_update(plain_password, hashed_password)


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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authentication credentials",
        )
