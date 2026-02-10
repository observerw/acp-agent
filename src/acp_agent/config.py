from __future__ import annotations

from pathlib import Path

import platformdirs
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CACHE_PATH = platformdirs.user_cache_path(
    appname="acp-agent", ensure_exists=True
)


class SpawnConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ACP_AGENT_",
        env_file=".env",
        extra="ignore",
    )

    python_version: str = "3.12"
    cache_path: Path = Field(default=DEFAULT_CACHE_PATH)


settings = SpawnConfig()
