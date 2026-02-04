from __future__ import annotations

from pathlib import Path
from typing import Annotated

from cyclopts import Parameter
from loguru import logger

from ..executor import run_local
from .app import app


def _parse_env(env_list: list[str] | None) -> dict[str, str]:
    if not env_list:
        return {}

    env_dict = {}
    for item in env_list:
        if "=" not in item:
            msg = f"Invalid environment variable format '{item}'. Expected KEY=VAL."
            raise ValueError(msg)
        key, val = item.split("=", 1)
        env_dict[key] = val
    return env_dict


@app.command
async def run(
    agent_id: str,
    *extra_args: str,
    env: Annotated[
        list[str] | None,
        Parameter(
            name=["--env", "-e"], help="Environment variables in KEY=VAL format."
        ),
    ] = None,
    cwd: Annotated[
        Path | None,
        Parameter(help="Working directory for the agent."),
    ] = None,
    cache_path: Annotated[
        Path | None,
        Parameter(help="Directory to cache agent binaries/packages."),
    ] = None,
) -> None:
    """Run an agent locally by its ID.

    Parameters
    ----------
    agent_id
        The ID of the agent to run.
    extra_args
        Additional arguments to pass to the agent.
    """
    try:
        env_dict = _parse_env(env)
    except ValueError as e:
        logger.error(str(e))
        raise SystemExit(1) from e

    if cwd and not cwd.exists():
        logger.error("Working directory '{}' does not exist.", cwd)
        raise SystemExit(1)

    await run_local(
        agent_id,
        extra_args=extra_args,
        env=env_dict,
        cwd=cwd,
        cache_path=cache_path,
    )
