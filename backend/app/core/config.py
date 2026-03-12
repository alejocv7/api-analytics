import os
import secrets
import warnings
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Annotated, Any, Literal, Self

from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    Field,
    PostgresDsn,
    RedisDsn,
    computed_field,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

try:
    __VERSION__ = version("app")
except PackageNotFoundError:
    __VERSION__ = "1.0.0"


def parse_list(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


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
    PROJECT_USER: EmailStr
    PROJECT_PASSWORD: str
    PROJECT_KEY: str
    PROJECT_NAME: str = "API Analytics Service"
    PROJECT_DESCRIPTION: str = "Track and analyze API performance metrics"
    PROJECT_SUFFIX_LENGTH: int = 4
    PROJECT_NAME_PATTERN: str = r"^[a-zA-Z0-9\s_-]+$"

    VERSION: str = __VERSION__

    REQUEST_ID_HEADER: str = "X-Request-ID"

    # Environment
    ENVIRONMENT: Literal["local", "staging", "test", "prod"] = "local"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def IS_PRODUCTION(self) -> bool:
        return self.ENVIRONMENT == "prod"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SHOW_DOCS(self) -> bool:
        return not self.IS_PRODUCTION

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
    # Redis
    REDIS_DB: str = "0"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_POOL_SIZE: int = 20
    REDIS_HEALTH_CHECK_INTERVAL: int = 30

    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_URL(self) -> str:
        return str(
            RedisDsn.build(
                scheme="redis",
                host=self.REDIS_HOST,
                port=self.REDIS_PORT,
                password=self.REDIS_PASSWORD,
                path=self.REDIS_DB,
            )
        )

    # Security
    @computed_field  # type: ignore[prop-decorator]
    @property
    def security_headers(self) -> dict[str, str]:
        headers = {
            # Basic security headers suitable for an API
            "X-Content-Type-Options": "nosniff",
            "Content-Security-Policy": "frame-ancestors 'none';",
            "Cache-Control": "no-store",
        }

        if self.IS_PRODUCTION:
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return headers

    SECURITY_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32), min_length=32
    )
    SECURITY_ALGORITHM: str = "HS256"
    SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    SECURITY_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_WINDOW_SECONDS: int = 900  # 15 minutes

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

    # Metric cleanup scheduler
    METRIC_CLEANUP_INTERVAL_HOURS: int = Field(default=24, ge=1)
    METRIC_RETENTION_DAYS: int = Field(default=90, ge=30, le=365)

    SHUTDOWN_TASKS_CANCEL_TIMEOUT_SECONDS: int = Field(default=5, ge=1, le=60)

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECURITY_KEY", self.SECURITY_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret("REDIS_PASSWORD", self.REDIS_PASSWORD)
        # Project
        self._check_default_secret("PROJECT_PASSWORD", self.PROJECT_PASSWORD)
        self._check_default_secret("PROJECT_USER", self.PROJECT_USER)
        self._check_default_secret("PROJECT_KEY", self.PROJECT_KEY)

        return self


settings = Settings()
