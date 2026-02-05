from __future__ import annotations

from abc import ABC, abstractmethod
from functools import cached_property
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from acp_agent.utils.platform import get_platform_key


class Distribution(BaseModel, ABC):
    args: list[str] = Field(default_factory=list)
    env: dict[str, str] = Field(default_factory=dict)

    @abstractmethod
    def format_cmd(self) -> str: ...

    @abstractmethod
    def format_args(self) -> tuple[str, ...]: ...


class NpxDistribution(Distribution):
    package: str

    def format_cmd(self) -> str:
        return "bunx"

    def format_args(self) -> tuple[str, ...]:
        return (
            self.package,
            *self.args,
        )


class UvxDistribution(Distribution):
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


class BinaryDistribution(Distribution):
    archive: str
    cmd: str

    def format_cmd(self) -> str:
        return Path(self.cmd).name

    def format_args(self) -> tuple[str, ...]:
        return (*self.args,)


class DistributionUnion(BaseModel):
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
    dist_union: DistributionUnion = Field(alias="distribution")

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"

    @cached_property
    def dist(self) -> Distribution:
        match self.dist_union:
            case DistributionUnion(npx=NpxDistribution() as npx):
                return npx
            case DistributionUnion(uvx=UvxDistribution() as uvx):
                return uvx
            case DistributionUnion(binary=dict() as binaries):
                platform_key = get_platform_key()
                if binary_distro := binaries.get(platform_key):
                    return binary_distro

                raise ValueError(
                    f"No binary distribution found for platform '{platform_key}' "
                )
            case _:
                raise ValueError("Unsupported distribution type.")


class Registry(BaseModel):
    version: str
    agents: list[RegistryAgent]
    extensions: list[Any] = Field(default_factory=list)
