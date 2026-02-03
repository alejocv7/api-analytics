from typing import Annotated, Any, Literal

from pydantic import AfterValidator, AnyUrl, BeforeValidator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_list(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


def normalize_urls(v: list[AnyUrl] | str) -> list[str]:
    return [str(origin).rstrip("/") for origin in v]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
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
    ENVIRONMENT: Literal["local", "staging", "testing", "production"] = "local"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # API
    API_V1_STR: str = "/api/v1"
    API_PREFIX: str = API_V1_STR

    # Database
    SQLALCHEMY_DATABASE_URI: str
    REDIS_URL: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def ASYNC_SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
            return self.SQLALCHEMY_DATABASE_URI.replace(
                "sqlite:///", "sqlite+aiosqlite:///"
            )
        if self.SQLALCHEMY_DATABASE_URI.startswith("postgresql"):
            return self.SQLALCHEMY_DATABASE_URI.replace(
                "postgresql://", "postgresql+asyncpg://"
            )
        return self.SQLALCHEMY_DATABASE_URI

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
        return self.ENVIRONMENT == "production"


settings = Settings()  # type: ignore
