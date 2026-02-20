from __future__ import annotations

import asyncio
import os
from asyncio.subprocess import Process
from collections.abc import Mapping, Sequence
from functools import cached_property
from pathlib import Path
from typing import Final, Literal, Self

import anyio
import httpx
from attrs import define, field
from jinja2 import Environment, PackageLoader
from loguru import logger

from .config import AgentConfig
from .exceptions import AgentNotFoundError, DistributionError
from .registry import Distribution, fetch_agent
from .registry.model import (
    BinaryDistribution,
    NpxDistribution,
    RegistryAgent,
    UvxDistribution,
)
from .settings import ContainerSettings, Settings, env_settings
from .utils.archive import extract_binary
from .utils.sh import available_programs

_env: Final = Environment(loader=PackageLoader("acp_agent", "templates"))
_containerfile_template: Final = _env.get_template("Containerfile.j2")


async def _prepare_npx(dist: NpxDistribution, extra_args: Sequence[str]) -> list[str]:
    args = [dist.package, *dist.args, *extra_args]
    match await available_programs("bunx", "npx"):
        case "bunx":
            return ["bunx", *args]
        case "npx":
            return ["npx", "-y", *args]
        case _:
            raise ValueError(
                "No available program to run npx package. Please install bunx or npx."
            )


async def _prepare_uvx(
    dist: UvxDistribution,
    extra_args: Sequence[str],
    settings: Settings,
) -> list[str]:
    args = [dist.package, *dist.args, *extra_args]
    match await available_programs("uvx", "pip", "pip3"):
        case "uvx":
            return ["uvx", "--python", settings.python_version, *args]
        case "pip" | "pip3" as pip if settings.allow_pip:
            logger.warning(
                "Using pip as fallback for uvx. "
                "This will install the package globally or in the current env."
            )
            _ = await anyio.run_process((pip, "install", dist.package))
            return args
        case _:
            raise ValueError(
                "No available program to install uvx package. "
                "Please install uvx or allow pip fallback."
            )


async def _prepare_binary(
    dist: BinaryDistribution,
    extra_args: Sequence[str],
    settings: Settings,
) -> list[str]:
    bin_dir_path = anyio.Path(settings.bin_dir_path)
    if not await bin_dir_path.exists():
        await bin_dir_path.mkdir(parents=True, exist_ok=True)

    bin_path = bin_dir_path / Path(dist.cmd).name

    cmd = [str(bin_path), *dist.args, *extra_args]

    if await bin_path.exists():
        logger.info("Binary already exists at {}, skipping download", bin_path)
        return cmd

    logger.info("Downloading binary from {} to {}", dist.archive, bin_path)

    async with (
        anyio.NamedTemporaryFile(delete_on_close=True) as archive_file,
        httpx.AsyncClient(
            timeout=httpx.Timeout(connect=30.0, read=120.0, write=120.0, pool=30.0),
            follow_redirects=True,
        ) as client,
    ):
        response = await client.get(dist.archive)
        response.raise_for_status()
        await archive_file.write(response.content)

        assert isinstance(archive_file.name, str)

        await asyncio.to_thread(
            extract_binary,
            archive_path=Path(archive_file.name),
            binary_name=Path(dist.cmd).name,
            dest_dir=settings.bin_dir_path,
        )

    await bin_path.chmod(0o755)

    return cmd


@define
class ACPAgent:
    agent: RegistryAgent
    config_path: Path | None = None
    credential_path: Path | None = None
    extra_args: tuple[str, ...] = field(factory=tuple)
    env: dict[str, str] = field(factory=dict)
    workdir: Path | None = None
    settings: Settings | None = None

    @classmethod
    async def create(
        cls,
        agent_id: str,
        *,
        config_path: str | Path | Literal[True] | None = None,
        credential_path: str | Path | Literal[True] | None = None,
        extra_args: Sequence[str] = (),
        env: Mapping[str, str] | None = None,
        workdir: str | Path | None = None,
        settings: Settings | None = None,
    ) -> Self:
        agent = await fetch_agent(agent_id)
        if not agent:
            raise AgentNotFoundError(
                f"Agent with ID '{agent_id}' not found in registry."
            )

        config = AgentConfig.get(agent_id)
        resolved_config_path: Path | None = None
        resolved_credential_path: Path | None = None

        match (config_path, config):
            case (str() | Path() as path, _) if path:
                resolved_config_path = Path(path).expanduser().resolve()
            case (True, AgentConfig(config=default_path)):
                resolved_config_path = default_path

        match credential_path:
            case str() | Path() as path if path:
                resolved_credential_path = Path(path).expanduser().resolve()
            case True if config and config.credential:
                resolved_credential_path = config.credential

        return cls(
            agent=agent,
            config_path=resolved_config_path,
            credential_path=resolved_credential_path,
            extra_args=tuple(extra_args),
            env=dict(env or {}),
            workdir=Path(workdir) if workdir else None,
            settings=settings or env_settings,
        )

    @property
    def agent_id(self) -> str:
        return self.agent.id

    @property
    def dist(self) -> Distribution:
        return self.agent.dist

    @cached_property
    def config(self) -> AgentConfig:
        """Load and cache the agent config from registry."""
        if config := AgentConfig.get(self.agent_id):
            return config
        raise AgentNotFoundError(
            f"Agent with ID '{self.agent_id}' not found in registry."
        )

    async def run(self) -> Process:
        """Run agent command and return its process handle."""

        cmd = await self.setup()

        process = await asyncio.create_subprocess_exec(
            *cmd,
            env={**os.environ, **self.dist.env, **self.env},
            cwd=self.workdir,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )

        if process.stdin is None or process.stdout is None:
            raise RuntimeError("Failed to create subprocess pipes")

        return process

    def format_command(self) -> list[str]:
        """Build a runnable command without installing dependencies."""
        return [
            self.dist.format_cmd(),
            *self.dist.format_args(),
            *self.extra_args,
        ]

    async def setup(self) -> list[str]:
        """Build a runnable command, installing/downloading dependencies if needed."""

        match self.agent.dist:
            case NpxDistribution() as npx:
                return await _prepare_npx(npx, extra_args=self.extra_args)
            case UvxDistribution() as uvx:
                if not self.settings:
                    raise ValueError("Spawn settings are required for uvx distribution")
                return await _prepare_uvx(
                    uvx,
                    extra_args=self.extra_args,
                    settings=self.settings,
                )
            case BinaryDistribution() as binary:
                if not self.settings:
                    raise ValueError(
                        "Spawn settings are required for binary distribution"
                    )
                return await _prepare_binary(
                    binary,
                    extra_args=self.extra_args,
                    settings=self.settings,
                )
            case _:
                raise DistributionError(
                    "Agent distribution is not specified or unsupported"
                )

    async def format_containerfile(
        self,
        containerfile: str,
        *,
        container_settings: ContainerSettings | None = None,
        mode: Literal["run", "sleep"] = "run",
    ) -> str:
        """Render a containerfile with command, env vars, and runtime assets."""

        if not container_settings:
            container_settings = ContainerSettings()

        env = container_settings.model_dump(mode="json")
        env = {f"ACP_AGENT_{key.upper()}": value for key, value in env.items()}

        return _containerfile_template.render(
            containerfile=containerfile,
            bin_dir=container_settings.bin_dir_path,
            agent_id=self.agent_id,
            npx=isinstance(self.agent.dist, NpxDistribution),
            env_vars={**env, **self.dist.env, **self.env},
            workdir=self.workdir,
            mode=mode,
        )
