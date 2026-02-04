from __future__ import annotations

import anyio
from cyclopts import App, Parameter
from pathlib import Path
from typing import Annotated, List, Optional
import os

from acp_agent.executor import run_local

app = App()


@app.command
async def run(
    agent_id: str,
    *extra_args: str,
    env: Annotated[
        Optional[List[str]],
        Parameter(
            name=["--env", "-e"], help="Environment variables in KEY=VAL format."
        ),
    ] = None,
    cwd: Annotated[
        Optional[Path], Parameter(help="Working directory for the agent.")
    ] = None,
    cache_path: Annotated[
        Optional[Path], Parameter(help="Directory to cache agent binaries/packages.")
    ] = None,
):
    """Run an agent locally by its ID.

    Parameters
    ----------
    agent_id
        The ID of the agent to run.
    extra_args
        Additional arguments to pass to the agent.
    """

    env_dict = {}
    if env:
        for item in env:
            if "=" not in item:
                print(
                    f"Error: Invalid environment variable format '{item}'. Expected KEY=VAL."
                )
                raise SystemExit(1)
            key, val = item.split("=", 1)
            env_dict[key] = val

    if cwd and not cwd.exists():
        print(f"Error: Working directory '{cwd}' does not exist.")
        raise SystemExit(1)

    await run_local(
        agent_id,
        extra_args=extra_args,
        env=env_dict,
        cwd=cwd,
        cache_path=cache_path,
    )


def main():
    app()


if __name__ == "__main__":
    main()
