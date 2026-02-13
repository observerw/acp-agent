from __future__ import annotations

from typing import Final

import httpx

from .model import Registry, RegistryAgent

REGISTRY_URL = "https://cdn.agentclientprotocol.com/registry/v1/latest/registry.json"

_BUILTIN_AGENTS: Final[tuple[RegistryAgent, ...]] = (
    RegistryAgent.model_validate(
        {
            "id": "dummy",
            "name": "Dummy",
            "version": "0.2.0",
            "description": "Built-in ACP dummy agent for protocol testing",
            "repository": "https://github.com/observerw/acp-agent",
            "authors": ["observerw"],
            "license": "MIT",
            "distribution": {
                "uvx": {
                    "package": "acp-agent",
                    "args": ["dummy"],
                }
            },
        }
    ),
)


def _builtin_agent(agent_id: str) -> RegistryAgent | None:
    return next((agent for agent in _BUILTIN_AGENTS if agent.id == agent_id), None)


def _merge_builtin_agents(agents: list[RegistryAgent]) -> list[RegistryAgent]:
    existing_ids = {agent.id for agent in agents}
    extras = [agent for agent in _BUILTIN_AGENTS if agent.id not in existing_ids]
    return [*agents, *extras]


async def fetch_registry() -> Registry:
    """Fetch the ACP registry data."""
    async with httpx.AsyncClient() as client:
        response = await client.get(REGISTRY_URL, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        data = response.json()
    return Registry.model_validate(data)


def fetch_registry_sync() -> Registry:
    """Fetch the ACP registry data (synchronous)."""
    with httpx.Client() as client:
        response = client.get(REGISTRY_URL, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        data = response.json()
    return Registry.model_validate(data)


async def list_agents() -> list[RegistryAgent]:
    """List all agents from the ACP registry."""
    registry = await fetch_registry()
    return _merge_builtin_agents(registry.agents)


def list_agents_sync() -> list[RegistryAgent]:
    """List all agents from the ACP registry (synchronous)."""
    registry = fetch_registry_sync()
    return _merge_builtin_agents(registry.agents)


async def fetch_agent(id: str) -> RegistryAgent | None:
    if agent := _builtin_agent(id):
        return agent

    agents = await list_agents()
    return next((a for a in agents if a.id == id), None)


def fetch_agent_sync(id: str) -> RegistryAgent | None:
    if agent := _builtin_agent(id):
        return agent

    agents = list_agents_sync()
    return next((a for a in agents if a.id == id), None)
