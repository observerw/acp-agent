from __future__ import annotations

import asyncio
import os
import tempfile
from asyncio import StreamReader, StreamWriter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final, Literal, NamedTuple, TypedDict, overload

import anyio
from attrs import define, field
from jinja2 import Environment, PackageLoader
from loguru import logger

from .config import AgentConfig
from .exceptions import AgentNotFoundError, DistributionError
from .registry import fetch_agent
from .registry.model import BinaryDistribution, NpxDistribution, UvxDistribution
from .settings import SpawnSettings, env_settings
from .utils.archive import extract_binary
from .utils.platform import get_platform_key
from .utils.sh import available_programs


class AgentStreamParams(TypedDict):
    input_stream: StreamWriter
    output_stream: StreamReader


class AgentStream(NamedTuple):
    input: StreamWriter
    output: StreamReader

    def as_params(self) -> AgentStreamParams:
        return AgentStreamParams(input_stream=self.input, output_stream=self.output)


class AgentCommand(TypedDict):
    cmd: list[str]
    env: dict[str, str]
    cwd: Path | None


_env: Final = Environment(loader=PackageLoader("acp_agent", "templates"))
_containerfile_template: Final = _env.get_template("Containerfile.j2")


async def run_process(
    cmd: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
    cwd: str | Path | None = None,
) -> int:
    """Run a subprocess asynchronously and wait for it to complete."""
    process = await asyncio.create_subprocess_exec(*cmd, env=env, cwd=cwd)

    if (returncode := await process.wait()) != 0:
        msg = f"Process failed with return code {process.returncode}"
        raise RuntimeError(msg)
    return returncode


async def spawn_process(
    cmd: Sequence[str],
    *,
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


async def _prepare_npx(
    dist: NpxDistribution,
    extra_args: Sequence[str],
    spawn_settings: SpawnSettings,
) -> list[str]:
    del spawn_settings
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
            await run_process([pip, "install", dist.package])
            return args
        case _:
            raise ValueError(
                "No available program to install uvx package. "
                "Please install uvx or allow pip fallback."
            )


async def _prepare_binary(
    dist: BinaryDistribution,
    extra_args: Sequence[str],
    spawn_settings: SpawnSettings,
) -> list[str]:
    cache_path = anyio.Path(spawn_settings.cache_path)
    await cache_path.mkdir(parents=True, exist_ok=True)
    binary_path = cache_path / Path(dist.cmd).name

    if not await binary_path.exists():
        logger.info("Downloading binary from {} to {}", dist.archive, binary_path)

        with tempfile.NamedTemporaryFile(suffix=Path(dist.archive).suffix) as tmp:
            match await available_programs("curl", "wget"):
                case "curl":
                    await run_process(["curl", "-L", "-o", tmp.name, dist.archive])
                case "wget":
                    await run_process(["wget", "-O", tmp.name, dist.archive])
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
    agent_id: str
    _raw_extra_args: Sequence[str] = field(factory=tuple, alias="extra_args")
    _raw_env: Mapping[str, str] = field(factory=dict, alias="env")
    _raw_workdir: str | Path | None = field(default=None, alias="workdir")
    spawn_settings: SpawnSettings | None = None

    extra_args: tuple[str, ...] = field(init=False)
    env: dict[str, str] = field(init=False)
    workdir: Path | None = field(init=False)

    def __attrs_post_init__(self) -> None:
        self.extra_args = tuple(self._raw_extra_args)
        self.env = dict(self._raw_env)
        self.workdir = Path(self._raw_workdir) if self._raw_workdir else None

    @property
    def config(self) -> AgentConfig | None:
        return AgentConfig.get(self.agent_id)

    @overload
    async def run(self, *, attach: Literal[False] = ...) -> AgentStream: ...

    @overload
    async def run(self, *, attach: Literal[True]) -> int: ...

    async def run(self, *, attach: bool = False) -> AgentStream | int:
        cmd = await self.format_command()
        run_cmd = AgentCommand(
            cmd=cmd,
            env={**os.environ, **self.env},
            cwd=self.workdir,
        )
        if attach:
            return await run_process(**run_cmd)
        return await spawn_process(**run_cmd)

    async def format_command(self) -> list[str]:
        agent = await fetch_agent(self.agent_id)
        if not agent:
            msg = f"Agent with ID '{self.agent_id}' not found in registry."
            raise AgentNotFoundError(msg)

        union = agent.dist_union
        spawn_settings = self.spawn_settings or env_settings

        if union.npx:
            return await _prepare_npx(
                union.npx,
                extra_args=self.extra_args,
                spawn_settings=spawn_settings,
            )

        if union.uvx:
            return await _prepare_uvx(
                union.uvx,
                extra_args=self.extra_args,
                spawn_settings=spawn_settings,
            )

        if union.binary:
            platform_key = get_platform_key()
            binary_dist = union.binary.get(platform_key)
            if not binary_dist:
                raise DistributionError(
                    f"No binary distribution found for platform '{platform_key}'"
                )
            return await _prepare_binary(
                binary_dist,
                extra_args=self.extra_args,
                spawn_settings=spawn_settings,
            )

        raise DistributionError("Agent distribution is not specified or unsupported")

    async def format_containerfile(
        self,
        containerfile: str,
        *,
        bin_dir: str = "/usr/local/bin",
        mode: Literal["run", "sleep"] = "run",
    ) -> str:
        agent = await fetch_agent(self.agent_id)
        if not agent:
            msg = f"Agent with id {self.agent_id} not found"
            raise ValueError(msg)

        dist = agent.dist
        archive_url = dist.archive if isinstance(dist, BinaryDistribution) else None

        match mode:
            case "sleep":
                cmd = "sleep"
                args = ("infinity",)
            case "run":
                cmd = dist.format_cmd()
                args = (*dist.format_args(), *self.extra_args)

        return _containerfile_template.render(
            containerfile=containerfile,
            archive_url=archive_url,
            env_vars={**dist.env, **self.env},
            cmd=cmd,
            args=args,
            npx=isinstance(dist, NpxDistribution),
            uvx=isinstance(dist, UvxDistribution),
            bin_dir=bin_dir,
            workdir=str(self.workdir) if self.workdir else None,
        )
