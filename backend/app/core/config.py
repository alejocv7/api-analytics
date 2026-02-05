import os
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import (
    AfterValidator,
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


def normalize_urls(v: list[AnyUrl] | str) -> list[str]:
    return [str(origin).rstrip("/") for origin in v]


def get_env_file():
    env = os.getenv("ENVIRONMENT", "local")
    base_dir = Path(__file__).resolve().parent.parent.parent

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
    REDIS_URL: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    # Security
    SECURITY_KEY: str
    SECURITY_ALGORITHM: str = "HS256"
    SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    # Dummy hash to use for timing attack prevention when user is not found.
    # This is an Argon2 hash of a random password, used to ensure constant-time comparison
    SECURITY_DUMMY_HASH: str = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"

    # CORS & Trusted Hosts
    TRUSTED_HOSTS: Annotated[list[str] | str, BeforeValidator(parse_list)] = []
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_list), AfterValidator(normalize_urls)
    ] = []

    # API Keys
    API_KEY_LENGTH: int = 32
    API_KEY_PREFIX: str = "sk_live_"
    API_KEY_LOOKUP_PREFIX_LENGTH: int = 20
    API_KEY_PROJECT_LIMIT: int = 10
    API_KEY_DEFAULT_EXPIRY_DAYS: int = 60

    @computed_field  # type: ignore[prop-decorator]
    @property
    def IS_PRODUCTION(self) -> bool:
        return self.ENVIRONMENT == "prod"

    @model_validator(mode="after")
    def validate_security_key(self):
        key = self.SECURITY_KEY.strip()
        if self.IS_PRODUCTION and (not key or key == "change_this"):
            raise ValueError(
                "SECURITY_KEY must be set to a secure value in production!"
            )
        self.SECURITY_KEY = key
        return self


settings = Settings()  # type: ignore
