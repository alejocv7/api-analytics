from datetime import datetime, timezone
from typing import Annotated

from pydantic import AfterValidator, AwareDatetime, BeforeValidator, SecretStr


def get_default_start_date() -> AwareDatetime:
    return datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)


def get_default_end_date() -> AwareDatetime:
    return datetime.now(timezone.utc).replace(
        hour=23, minute=59, second=59, microsecond=999999
    )


def normalize_url_path(url_path: str) -> str:
    if not url_path.startswith("/"):
        raise ValueError("url_path must start with '/'")
    return url_path.rstrip("/") or "/"


def validate_secure_password(password: SecretStr) -> SecretStr:
    from app.core import security

    return security.validate_password(password)


NormalizedUrlPath = Annotated[str, BeforeValidator(normalize_url_path)]
SecurePassword = Annotated[SecretStr, AfterValidator(validate_secure_password)]
