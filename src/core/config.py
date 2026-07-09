from functools import cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

LogLevel = Literal["debug", "info", "warning", "error", "critical"]


class StorageConfig(BaseModel):
    dir: Path = BASE_DIR.parent / "storage"
    max_file_size_mb: int = 20


class DatabaseConfig(BaseModel):
    url: PostgresDsn
    test_url: PostgresDsn | None = None
    echo: bool = False
    pool_size: Annotated[int, Field(ge=0)] = 5
    max_overflow: Annotated[int, Field(ge=-1)] = 10


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="APP_CONFIG__",
        env_nested_delimiter="__",
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    storage: StorageConfig = Field(default_factory=StorageConfig)
    db: DatabaseConfig
    log_level: LogLevel = "info"


@cache
def get_settings() -> Settings:
    return Settings()
