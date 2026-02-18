from __future__ import annotations

from pathlib import Path
from typing import Annotated, Final

from cyclopts import App, Parameter
from rich.console import Console

from acp_agent import ACPAgent
from acp_agent.debug import DummyAgent
from acp_agent.registry.fetch import list_agents

from .utils import display_agents_table, parse_env

app = App()
console: Final = Console()


@app.command
async def setup(
    agent_id: Annotated[
        str,
        Parameter(
            help="The ID of the agent to setup.",
        ),
    ],
    /,
) -> None:
    """Setup an agent locally by its ID (e.g., install dependencies)."""

    agent = await ACPAgent.create(agent_id=agent_id)
    _ = await agent.setup()


@app.command
async def run(
    agent_id: Annotated[
        str,
        Parameter(
            help="The ID of the agent to run.",
        ),
    ],
    /,
    *,
    env: Annotated[
        list[str] | None,
        Parameter(
            name=["--env", "-e"],
            help="Environment variables in KEY=VAL format.",
        ),
    ] = None,
    cwd: Annotated[
        Path | None,
        Parameter(help="Working directory for the agent."),
    ] = None,
    **kwargs: Annotated[
        str,
        Parameter(
            help="Extra arguments to pass to the start command (e.g., --arg value).",
        ),
    ],
) -> None:
    """Run an agent locally by its ID."""

    extra_args: list[str] = []
    for key, value in kwargs.items():
        extra_args.extend((f"--{key}", value))

    agent = await ACPAgent.create(
        agent_id=agent_id,
        extra_args=extra_args,
        env=parse_env(env or []),
        workdir=cwd,
    )
    process = await agent.run()
    returncode = await process.wait()
    raise SystemExit(returncode)


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
async def search(
    query: Annotated[
        str,
        Parameter(
            help="The search string to match agent names or IDs (fuzzy/substring match).",
        ),
    ],
) -> None:
    """Search for agents by name or ID."""

    agents = await list_agents()
    query = query.lower()
    filtered_agents = [
        agent  #
        for agent in agents
        if query in agent.name.lower() or query in agent.id.lower()
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


@app.command(name="dummy")
async def dummy(
    seed: Annotated[
        int | None,
        Parameter(
            name=["--seed"],
            help="Seed for deterministic random responses.",
        ),
    ] = None,
) -> None:
    """Run a dummy ACP agent for protocol testing."""

    await DummyAgent.run(seed=seed)


if __name__ == "__main__":
    app()
