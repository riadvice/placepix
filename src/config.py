from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All settings have sensible defaults; .env is optional."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="127.0.0.1:3000")
    dir: str = Field(default="./images")
    cache: bool = Field(default=True)
    cdn: str = Field(default="")
    min_width: int = Field(default=8)
    min_height: int = Field(default=8)
    max_width: int = Field(default=2000)
    max_height: int = Field(default=2000)
    upload_enabled: bool = Field(default=True)

    @property
    def bind_host(self) -> str:
        return self.host.rsplit(":", 1)[0] if ":" in self.host else self.host

    @property
    def bind_port(self) -> int:
        return int(self.host.rsplit(":", 1)[1]) if ":" in self.host else 3000

    @property
    def images_dir(self) -> Path:
        return Path(self.dir).resolve()

    @property
    def cache_dir(self) -> Path:
        return Path(".cache").resolve()


settings = Settings()
