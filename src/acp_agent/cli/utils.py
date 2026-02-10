from __future__ import annotations

from collections.abc import Sequence

from rich.console import Console
from rich.table import Table

from acp_agent.registry import RegistryAgent


def parse_env(env_list: Sequence[str]) -> dict[str, str]:
    def parse(item: str) -> list[str]:
        if "=" not in item:
            msg = f"Invalid environment variable format '{item}'. Expected KEY=VAL."
            raise ValueError(msg)
        return item.split("=", 1)

    return dict(parse(item) for item in env_list)


def display_agents_table(
    agents: list[RegistryAgent],
    title: str,
    *,
    console: Console | None = None,
) -> None:
    console = console or Console()
    table = Table(title=title)

    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="magenta")
    table.add_column("Description")

    for agent in agents:
        table.add_row(agent.id, agent.name, agent.description)

    console.print(table)
