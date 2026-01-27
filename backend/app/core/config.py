from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )

    # Project
    PROJECT_ID: int = 0
    PROJECT_NAME: str
    PROJECT_DESCRIPTION: str
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    # API
    API_V1_STR: str = "/api/v1"
    API_PREFIX: str = API_V1_STR

    # Database
    SQLALCHEMY_DATABASE_URI: str
    REDIS_URL: str

    # Security
    SECURITY_KEY: str
    SECURITY_ALGORITHM: str = "HS256"
    SECURITY_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


settings = Settings()  # type: ignore
