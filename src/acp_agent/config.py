from __future__ import annotations

from pathlib import Path
from typing import Self

from attrs import frozen


@frozen
class AgentConfig:
    config: Path
    credential: Path | None = None

    @classmethod
    def get(cls, agent_id: str) -> Self | None:
        match agent_id:
            case "opencode":
                return cls(
                    config=Path.home() / ".opencode",
                    credential=Path.home()
                    / ".local"
                    / "share"
                    / "opencode"
                    / "auth.json",
                )
            case "claude-code-acp":
                return cls(config=Path.home() / ".claude")
            case "gemini":
                return cls(config=Path.home() / ".gemini")
