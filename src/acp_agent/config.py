from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class SpawnConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ACP_AGENT_",
        env_file=".env",
        extra="ignore",
    )

    python_version: str = "3.12"
    cache_path: Path | None = None


settings = SpawnConfig()
