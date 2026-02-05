from __future__ import annotations

import httpx

from .model import Registry, RegistryAgent

REGISTRY_URL = "https://cdn.agentclientprotocol.com/registry/v1/latest/registry.json"


async def fetch_registry() -> Registry:
    """Fetch the ACP registry data."""
    async with httpx.AsyncClient() as client:
        response = await client.get(REGISTRY_URL, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        data = response.json()
    return Registry.model_validate(data)


async def list_agents() -> list[RegistryAgent]:
    """List all agents from the ACP registry."""
    registry = await fetch_registry()
    return registry.agents


async def fetch_agent(id: str) -> RegistryAgent | None:
    agents = await list_agents()
    return next((a for a in agents if a.id == id), None)
