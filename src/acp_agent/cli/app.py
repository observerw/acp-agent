from __future__ import annotations

from pathlib import Path
from typing import Annotated, Final

from cyclopts import App, Parameter
from rich.console import Console

from acp_agent.registry.fetch import list_agents
from acp_agent.sdk import run_local

from .utils import display_agents_table, parse_env

app = App()
console: Final = Console()


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
) -> None:
    """Run an agent locally by its ID.

    Parameters
    ----------
    agent_id
        The ID of the agent to run.
    extra_args
        Additional arguments to pass to the agent.
    """

    exit_code = await run_local(
        agent_id,
        attach=True,
        extra_args=extra_args,
        env=parse_env(env or []),
        cwd=cwd,
    )
    raise SystemExit(exit_code)


@app.command(name="list")
async def list_agents_cmd() -> None:
    """List all available agents from the registry."""
    agents = await list_agents()
    display_agents_table(
        agents,
        "Available Agents",
        console=console,
    )


@app.command
async def search(query: str) -> None:
    """Search for agents in the registry by name or ID.

    Parameters
    ----------
    query
        The search string (fuzzy/substring match).
    """

    agents = await list_agents()
    query = query.lower()
    filtered_agents = [
        agent
        for agent in agents
        if query in agent.name.lower()  #
        or query in agent.id.lower()
    ]

    if not filtered_agents:
        console.print(
            f"[yellow]No agents found matching '[bold]{query}[/bold]'.[/yellow]"
        )
        return

    display_agents_table(
        filtered_agents,
        f"Search Results for '{query}'",
        console=console,
    )


if __name__ == "__main__":
    app()
