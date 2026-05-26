from __future__ import annotations

import logging
import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All settings have sensible defaults; .env is optional."""

    model_config = SettingsConfigDict(
        env_file=[".env.test"] if os.getenv("TESTING") or os.getenv("PYTEST_CURRENT_TEST") else [".env"],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="127.0.0.1:3000")
    workers: int = Field(default=2)
    dir: str = Field(default="./data", alias="data_dir")
    seed_dir_str: str = Field(default="./images", alias="images_dir")
    cache: bool = Field(default=True)
    cdn: str = Field(default="")
    min_width: int = Field(default=8)
    min_height: int = Field(default=8)
    max_width: int = Field(default=2400)
    max_height: int = Field(default=2400)
    upload_enabled: bool = Field(default=True)
    seed_enabled: bool = Field(default=False)
    watermark_enabled: bool = Field(default=True)
    watermark_image: str = Field(default="static/watermark.png")
    watermark_text: str = Field(default="")
    watermark_position: str = Field(default="bottom-right")
    watermark_opacity: float = Field(default=0.5)

    # Base64 output max dimension (default: 256x256)
    base64_max_size: int = Field(default=256)

    # Google Analytics (optional)
    ga_tracking_id: str = Field(default="")

    # Legal links (GDPR compliance)
    privacy_policy_url: str = Field(default="")
    gdpr_statement_url: str = Field(default="")
    cookie_policy_url: str = Field(default="")

    # Cache TTL / cleanup (default: 336 hours = 2 weeks, cleanup every 12 hours)
    cache_ttl_hours: int = Field(default=336)
    cache_cleanup_interval_minutes: int = Field(default=720)
    cache_max_size_mb: int = Field(default=1024)

    # Processing concurrency limit per worker
    max_concurrent_processing: int = Field(default=4)

    # Logging
    log_level: str = Field(default="INFO")

    # S3-compatible storage (optional)
    s3_enabled: bool = Field(default=False)
    s3_endpoint: str = Field(default="")
    s3_access_key: str = Field(default="")
    s3_secret_key: str = Field(default="")
    s3_bucket: str = Field(default="")
    s3_prefix: str = Field(default="")
    s3_region: str = Field(default="")

    # AI generation via OVHcloud AI Endpoints (experimental)
    ai_generation_enabled: bool = Field(default=False)
    ovh_ai_endpoints_token: str = Field(default="")
    ovh_ai_endpoints_url: str = Field(default="https://endpoints.ai.cloud.ovh.net/v1")
    ai_s3_upload_enabled: bool = Field(default=False)
    ai_max_images_per_category: int = Field(default=100)
    ai_default_steps: int = Field(default=30)
    ai_default_cfg_scale: float = Field(default=7.0)

    # Custom fonts directory (optional, for text overlays)
    font_dir: str = Field(default="")

    @property
    def bind_host(self) -> str:
        return self.host.rsplit(":", 1)[0] if ":" in self.host else self.host

    @property
    def bind_port(self) -> int:
        return int(self.host.rsplit(":", 1)[1]) if ":" in self.host else 3000

    @property
    def images_dir(self) -> Path:
        return Path(self.seed_dir_str).resolve()

    @property
    def seed_dir(self) -> Path:
        return Path(self.seed_dir_str).resolve()

    @property
    def data_dir(self) -> Path:
        return Path(self.dir).resolve()

    @property
    def cache_dir(self) -> Path:
        return Path(".cache").resolve()

    @property
    def font_dir_path(self) -> Path | None:
        if self.font_dir:
            return Path(self.font_dir).resolve()
        return None


settings = Settings()
