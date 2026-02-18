from __future__ import annotations

from pathlib import Path
from typing import ClassVar, Final

import platformdirs
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CACHE_PATH = platformdirs.user_cache_path(
    appname="acp-agent", ensure_exists=True
)

DEFAULT_BIN_DIR_PATH = Path.home() / ".local" / "bin"


class Settings(BaseSettings):
    model_config: ClassVar = SettingsConfigDict(
        env_prefix="ACP_AGENT_",
        env_file=".env",
        extra="ignore",
    )

    python_version: str = "3.12"
    """Python version to use for spawning agents. Default is 3.12."""

    allow_pip: bool = False
    """Whether to allow pip global installation when uv is not available."""

    cache_path: Path = Field(default=DEFAULT_CACHE_PATH)
    """Path to cache directory for storing downloaded binaries."""

    bin_dir_path: Path = Field(default=DEFAULT_BIN_DIR_PATH)


env_settings: Final = Settings()
