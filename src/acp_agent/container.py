from __future__ import annotations

from typing import Final

from jinja2 import Environment, PackageLoader

from acp_agent.registry import fetch_agent
from acp_agent.registry.model import (
    BinaryDistribution,
    NpxDistribution,
    UvxDistribution,
)

env: Final = Environment(loader=PackageLoader("acp_agent", "templates"))
containerfile_template: Final = env.get_template("Containerfile.j2")


async def format_containerfile(
    agent_id: str,
    containerfile: str,
    *,
    bin_dir: str = "/usr/local/bin",
) -> str:
    agent = await fetch_agent(agent_id)
    if not agent:
        raise ValueError(f"Agent with id {agent_id} not found")

    dist = agent.dist
    archive_url = dist.archive if isinstance(dist, BinaryDistribution) else None

    return containerfile_template.render(
        containerfile=containerfile,
        archive_url=archive_url,
        env_vars=dist.env,
        cmd=dist.format_cmd(),
        args=dist.format_args(),
        npx=isinstance(dist, NpxDistribution),
        uvx=isinstance(dist, UvxDistribution),
        bin_dir=bin_dir,
    )
