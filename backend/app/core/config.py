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
    PROJECT_NAME: str
    PROJECT_DESCRIPTION: str
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    # API
    API_V1_STR: str = "/api/v1"

    # Database
    SQLALCHEMY_DATABASE_URI: str

    # Security
    HASH_SALT: str = "change_me_in_production"


settings = Settings()  # type: ignore
