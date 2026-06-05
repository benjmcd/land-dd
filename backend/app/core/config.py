from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

StorageBackend = Literal["memory", "postgres"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = Field(default="land-diligence", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    storage_backend: StorageBackend = Field(default="memory", alias="APP_STORAGE_BACKEND")
    database_url: str = Field(
        default="postgresql+psycopg://land:land@localhost:5432/land_diligence",
        alias="DATABASE_URL",
    )
    object_store_root: str = Field(
        default="./local_artifacts/object_store", alias="OBJECT_STORE_ROOT"
    )
    enable_live_connectors: bool = Field(default=False, alias="ENABLE_LIVE_CONNECTORS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
