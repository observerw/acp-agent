from __future__ import annotations

from rich.console import Console
from rich.table import Table

from ..models import RegistryAgent


def parse_env(env_list: list[str] | None) -> dict[str, str]:
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
