import os
from pathlib import Path
from typing import Annotated, Any, ClassVar, Literal, Self

from pydantic import (
    AnyUrl,
    BeforeValidator,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_list(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


def validate_redis_url(v: str) -> str:
    if not any(v.startswith(p) for p in ["redis://", "rediss://", "memory://"]):
        raise ValueError("REDIS_URL must start with redis://, rediss://, or memory://")
    return v


def get_env_file() -> Path:
    env = os.getenv("ENVIRONMENT", "local")
    base_dir = Path(__file__).resolve().parent.parent.parent.parent

    env_file_name = f".env.{env}" if env != "local" else ".env"
    candidate = base_dir / env_file_name

    return candidate if candidate.exists() else base_dir / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=get_env_file(),
        env_ignore_empty=True,
        extra="ignore",
    )

    # Project
    PROJECT_ID: int = 0
    PROJECT_NAME: str = "API Analytics Service"
    PROJECT_DESCRIPTION: str = "Track and analyze API performance metrics"
    PROJECT_SUFFIX_LENGTH: int = 4
    PROJECT_NAME_PATTERN: str = r"^[a-zA-Z0-9\s_-]+$"

    # Environment
    ENVIRONMENT: Literal["local", "staging", "test", "prod"] = "local"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def IS_PRODUCTION(self) -> bool:
        return self.ENVIRONMENT == "prod"

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # API
    API_V1_STR: str = "/api/v1"
    API_PREFIX: str = API_V1_STR

    # Database
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    REDIS_URL: Annotated[str, BeforeValidator(validate_redis_url)]

    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ASYNC_SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    # Security
    CSP_STRICT: ClassVar[dict[str, str]] = {
        "default-src": "'self'",
        "script-src": "'self'",
        "style-src": "'self'",
        "img-src": "'self' data: https:",
        "connect-src": "'self'",
        "font-src": "'self'",
        "object-src": "'none'",
        "base-uri": "'self'",
        "form-action": "'self'",
        "frame-ancestors": "'none'",
        "upgrade-insecure-requests": "",
    }
    CSP_BASIC: ClassVar[dict[str, str]] = {
        "default-src": "'self'",
        "script-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        "style-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        "font-src": "'self' data: https://cdn.jsdelivr.net",
        "connect-src": "'self' https://cdn.jsdelivr.net",
        "img-src": "'self' data: https://fastapi.tiangolo.com",
    }
    CSP_BY_ENV: ClassVar[dict[str, dict[str, str]]] = {
        "local": CSP_BASIC,
        "staging": CSP_STRICT,
        "test": CSP_STRICT,
        "prod": CSP_STRICT,
    }

    @computed_field  # type: ignore[prop-decorator]
    @property
    def security_headers(self) -> dict[str, str]:
        csp_directives = self.CSP_BY_ENV.get(self.ENVIRONMENT, self.CSP_STRICT)
        csp = "; ".join(f"{k} {v}".strip() for k, v in csp_directives.items()) + ";"

        headers = {
            "Content-Security-Policy": csp,
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "geolocation=(), microphone=(), camera=(), payment=()"
            ),
        }

        if self.IS_PRODUCTION:
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return headers

    SECURITY_KEY: str
    SECURITY_ALGORITHM: str = "HS256"
    SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    # Dummy hash to use for timing attack prevention when user is not found.
    # This is an Argon2 hash of a random password,
    # used to ensure constant-time comparison
    SECURITY_DUMMY_HASH: str = (
        "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZT"
        "I0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"
    )

    # CORS & Trusted Hosts
    TRUSTED_HOSTS: Annotated[list[str] | str, BeforeValidator(parse_list)] = []
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_list)
    ] = []

    @computed_field  # type: ignore[prop-decorator]
    @property
    def cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS]

    # API Keys
    API_KEY_LENGTH: int = 32
    API_KEY_PREFIX: str = "sk_live_"
    API_KEY_LOOKUP_PREFIX_LENGTH: int = 20
    API_KEY_PROJECT_LIMIT: int = 10
    API_KEY_DEFAULT_EXPIRY_DAYS: int = 60

    @model_validator(mode="after")
    def validate_security_key(self) -> Self:
        key = self.SECURITY_KEY.strip()
        if self.IS_PRODUCTION and (not key or key == "change_this"):
            raise ValueError(
                "SECURITY_KEY must be set to a secure value in production!"
            )
        self.SECURITY_KEY = key
        return self


settings = Settings()
