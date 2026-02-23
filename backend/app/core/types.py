from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, SecretStr


def normalize_url_path(url_path: str) -> str:
    if not url_path.startswith("/"):
        raise ValueError("url_path must start with '/'")
    return url_path.rstrip("/") or "/"


def validate_secure_password(password: SecretStr) -> SecretStr:
    from app.core import security

    return security.validate_password(password)


NormalizedUrlPath = Annotated[str, BeforeValidator(normalize_url_path)]
SecurePassword = Annotated[SecretStr, AfterValidator(validate_secure_password)]
