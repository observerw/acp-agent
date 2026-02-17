from __future__ import annotations

import asyncio
import os
import tempfile
from asyncio import StreamReader, StreamWriter
from collections.abc import Mapping, Sequence
from functools import cached_property
from pathlib import Path
from typing import Final, Literal, NamedTuple, Self, overload

import anyio
from acp import Client, connect_to_agent
from acp.client import ClientSideConnection
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
from .settings import SpawnSettings
from .utils.archive import extract_binary
from .utils.sh import available_programs


class AgentStream(NamedTuple):
    input: StreamWriter
    output: StreamReader


_env: Final = Environment(loader=PackageLoader("acp_agent", "templates"))
_containerfile_template: Final = _env.get_template("Containerfile.j2")


async def run_process(
    *cmd: str,
    env: Mapping[str, str] | None = None,
    cwd: str | Path | None = None,
) -> int:
    """Run a subprocess asynchronously and wait for it to complete."""
    process = await asyncio.create_subprocess_exec(*cmd, env=env, cwd=cwd)

    if (returncode := await process.wait()) != 0:
        raise RuntimeError(f"Process failed with return code {process.returncode}")
    return returncode


async def spawn_process(
    *cmd: str,
    env: Mapping[str, str] | None = None,
    cwd: str | Path | None = None,
) -> AgentStream:
    """Spawn a subprocess and return its streams."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        env=env,
        cwd=cwd,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    if process.stdin is None or process.stdout is None:
        raise RuntimeError("Failed to create subprocess pipes")
    return AgentStream(input=process.stdin, output=process.stdout)


async def _prepare_npx(dist: NpxDistribution, extra_args: Sequence[str]) -> list[str]:
    args = [dist.package, *dist.args, *extra_args]
    match await available_programs("bunx", "npx"):
        case "bunx":
            return ["bunx", *args]
        case "npx":
            return ["npx", "-y", *args]
        case _:
            raise AssertionError


async def _prepare_uvx(
    dist: UvxDistribution,
    extra_args: Sequence[str],
    spawn_settings: SpawnSettings,
) -> list[str]:
    args = [dist.package, *dist.args, *extra_args]
    match await available_programs("uvx", "pip", "pip3"):
        case "uvx":
            return ["uvx", "--python", spawn_settings.python_version, *args]
        case "pip" | "pip3" as pip if spawn_settings.allow_pip:
            logger.warning(
                "Using pip as fallback for uvx. "
                "This will install the package globally or in the current env."
            )
            await run_process(pip, "install", dist.package)
            return args
        case _:
            raise ValueError(
                "No available program to install uvx package. "
                "Please install uvx or allow pip fallback."
            )


async def _prepare_binary(
    dist: BinaryDistribution,
    extra_args: Sequence[str],
    settings: SpawnSettings,
) -> list[str]:
    cache_path = anyio.Path(settings.cache_path)
    await cache_path.mkdir(parents=True, exist_ok=True)
    binary_path = cache_path / Path(dist.cmd).name

    if not await binary_path.exists():
        logger.info("Downloading binary from {} to {}", dist.archive, binary_path)

        with tempfile.NamedTemporaryFile() as tmp:
            match await available_programs("curl", "wget"):
                case "curl":
                    await run_process("curl", "-L", "-o", tmp.name, dist.archive)
                case "wget":
                    await run_process("wget", "-O", tmp.name, dist.archive)
                case _:
                    raise ValueError(
                        "No available program to download binary. "
                        "Please install curl or wget."
                    )

            await asyncio.to_thread(
                extract_binary,
                archive_path=tmp.name,
                binary_name=Path(dist.cmd).name,
                dest_dir=Path(cache_path),
            )

        await binary_path.chmod(0o755)

    return [str(binary_path), *dist.args, *extra_args]


@define
class ACPAgent:
    agent: RegistryAgent
    config_path: Path | None = None
    credential_path: Path | None = None
    extra_args: tuple[str, ...] = field(factory=tuple)
    env: dict[str, str] = field(factory=dict)
    workdir: Path | None = None
    spawn_settings: SpawnSettings | None = None

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
        spawn_settings: SpawnSettings | None = None,
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
            case True:
                if config and config.credential:
                    resolved_credential_path = config.credential

        return cls(
            agent=agent,
            config_path=resolved_config_path,
            credential_path=resolved_credential_path,
            extra_args=tuple(extra_args),
            env=dict(env or {}),
            workdir=Path(workdir) if workdir else None,
            spawn_settings=spawn_settings,
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

    @overload
    async def run(self, *, attach: Literal[False] = ...) -> AgentStream: ...

    @overload
    async def run(self, *, attach: Literal[True]) -> int: ...

    async def run(self, *, attach: bool = False) -> AgentStream | int:
        """Run agent command and optionally wait for process completion."""
        cmd = await self.prepare_command()
        env = {**os.environ, **self.env}
        if attach:
            return await run_process(*cmd, env=env, cwd=self.workdir)
        return await spawn_process(*cmd, env=env, cwd=self.workdir)

    async def connect_client(self, client: Client) -> ClientSideConnection:
        """Connect to the agent process using ACP protocol."""
        streams = await self.run(attach=False)
        return connect_to_agent(
            client,
            input_stream=streams.input,
            output_stream=streams.output,
        )

    def format_command(self) -> list[str]:
        """Build a runnable command without installing dependencies."""
        return [
            self.dist.format_cmd(),
            *self.dist.format_args(),
            *self.extra_args,
        ]

    async def prepare_command(self) -> list[str]:
        """Build a runnable command, installing/downloading dependencies if needed."""

        match self.agent.dist:
            case NpxDistribution() as npx:
                return await _prepare_npx(npx, extra_args=self.extra_args)
            case UvxDistribution() as uvx:
                if not self.spawn_settings:
                    raise ValueError("Spawn settings are required for uvx distribution")
                return await _prepare_uvx(
                    uvx,
                    extra_args=self.extra_args,
                    spawn_settings=self.spawn_settings,
                )
            case BinaryDistribution() as binary:
                if not self.spawn_settings:
                    raise ValueError(
                        "Spawn settings are required for binary distribution"
                    )
                return await _prepare_binary(
                    binary,
                    extra_args=self.extra_args,
                    settings=self.spawn_settings,
                )
            case _:
                raise DistributionError(
                    "Agent distribution is not specified or unsupported"
                )

    async def format_containerfile(
        self,
        containerfile: str,
        *,
        mode: Literal["run", "sleep"] = "run",
        bin_dir: str = "/usr/local/bin",
    ) -> str:
        """Render a containerfile with command, env vars, and runtime assets."""

        match mode:
            case "sleep":
                cmd = ["sleep", "infinity"]
            case "run":
                cmd = self.format_command()

        return _containerfile_template.render(
            containerfile=containerfile,
            env_vars={**self.dist.env, **self.env},
            cmd=cmd,
            binary=self.dist if isinstance(self.dist, BinaryDistribution) else None,
            npx=isinstance(self.dist, NpxDistribution),
            uvx=isinstance(self.dist, UvxDistribution),
            bin_dir=bin_dir,
            workdir=str(self.workdir) if self.workdir else None,
        )
