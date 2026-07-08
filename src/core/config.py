from functools import cache
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class StorageConfig(BaseModel):
    dir: Path = BASE_DIR.parent / "storage"
    max_file_size_mb: int = 20


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_CONFIG__",
        env_nested_delimiter="__",
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    storage: StorageConfig = Field(default_factory=StorageConfig)


@cache
def get_settings() -> Settings:
    return Settings()
