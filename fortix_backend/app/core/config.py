from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    APP_NAME: str = Field(default="FortiX Backend")
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./fortix.db",
        description="SQLAlchemy async URL for SQLite using aiosqlite",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


