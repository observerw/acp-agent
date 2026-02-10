from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic import BaseModel

from acp_agent.registry import Distribution, RegistryAgent


class AgentMetadata(BaseModel):
    id: str


class ACPAgent(ABC):
    metadata: ClassVar[AgentMetadata]

    @property
    @abstractmethod
    def agent(self) -> RegistryAgent: ...

    @property
    def dist(self) -> Distribution:
        return self.agent.dist
