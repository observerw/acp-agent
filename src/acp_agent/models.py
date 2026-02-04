from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class DistributionBase(BaseModel, ABC):
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)

    @abstractmethod
    def format_cmd(self) -> str: ...

    @abstractmethod
    def format_args(self) -> tuple[str, ...]: ...


class NpxDistribution(DistributionBase):
    package: str

    def format_cmd(self) -> str:
        return "bunx"

    def format_args(self) -> tuple[str, ...]:
        return (
            self.package,
            *self.args,
        )


class UvxDistribution(DistributionBase):
    package: str

    def format_cmd(self) -> str:
        return "uvx"

    def format_args(self) -> tuple[str, ...]:
        return (
            "--python",
            "3.12",  # avoid python 3.14 compatibility issues
            self.package,
            *self.args,
        )


class BinaryDistribution(DistributionBase):
    archive: str
    cmd: str

    def format_cmd(self) -> str:
        return Path(self.cmd).name

    def format_args(self) -> tuple[str, ...]:
        return (*self.args,)


class Distribution(BaseModel):
    npx: NpxDistribution | None = None
    uvx: UvxDistribution | None = None
    binary: dict[str, BinaryDistribution] | None = None


class RegistryAgent(BaseModel):
    id: str
    name: str
    version: str
    description: str
    repository: str | None = None
    authors: list[str] = Field(default_factory=list)
    license: str
    icon: str | None = None
    distribution: Distribution

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"


class Registry(BaseModel):
    version: str
    agents: list[RegistryAgent]
    extensions: list[Any] = Field(default_factory=list)
