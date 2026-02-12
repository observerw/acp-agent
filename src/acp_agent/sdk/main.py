from __future__ import annotations

import asyncio
import os
from asyncio import StreamReader, StreamWriter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, NamedTuple, TypedDict, overload

import anyio
from loguru import logger

from acp_agent.exceptions import AgentNotFoundError, DistributionError
from acp_agent.registry import fetch_agent
from acp_agent.registry.model import (
    BinaryDistribution,
    NpxDistribution,
    UvxDistribution,
)
from acp_agent.settings import SpawnSettings, settings
from acp_agent.utils.archive import extract_binary
from acp_agent.utils.platform import get_platform_key
from acp_agent.utils.sh import available_programs


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


@overload
async def run_local(
    id: str,
    *,
    attach: Literal[False] = ...,
    extra_args: Sequence[str] = ...,
    env: Mapping[str, str] | None = ...,
    cwd: str | Path | None = ...,
    config: SpawnSettings | None = ...,
) -> AgentStream: ...


@overload
async def run_local(
    id: str,
    *,
    attach: Literal[True],
    extra_args: Sequence[str] = ...,
    env: Mapping[str, str] | None = ...,
    cwd: str | Path | None = ...,
    config: SpawnSettings | None = ...,
) -> int: ...


async def run_local(
    id: str,
    *,
    attach: bool = False,
    extra_args: Sequence[str] = (),
    env: Mapping[str, str] | None = None,
    cwd: str | Path | None = None,
    config: SpawnSettings | None = None,
) -> AgentStream | int:
    agent = await fetch_agent(id)
    if not agent:
        msg = f"Agent with ID '{id}' not found in registry."
        raise AgentNotFoundError(msg)

    union = agent.dist_union
    config = config or settings

    if union.npx:
        cmd = await _prepare_npx(union.npx, extra_args=extra_args, config=config)
    elif union.uvx:
        cmd = await _prepare_uvx(union.uvx, extra_args=extra_args, config=config)
    elif union.binary:
        platform_key = get_platform_key()
        binary_dist = union.binary.get(platform_key)
        if not binary_dist:
            raise DistributionError(
                f"No binary distribution found for platform '{platform_key}'"
            )
        cmd = await _prepare_binary(binary_dist, extra_args=extra_args, config=config)
    else:
        raise DistributionError("Agent distribution is not specified or unsupported")

    run_cmd = AgentCommand(
        cmd=cmd,
        env={**os.environ, **(env or {})},
        cwd=Path(cwd) if cwd else None,
    )
    if attach:
        return await run_process(**run_cmd)
    return await spawn_process(**run_cmd)


async def _prepare_npx(
    dist: NpxDistribution,
    extra_args: Sequence[str],
    config: SpawnSettings | None,
) -> list[str]:
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
    config: SpawnSettings,
) -> list[str]:
    args = [dist.package, *dist.args, *extra_args]
    match await available_programs("uvx", "pip", "pip3"):
        case "uvx":
            return ["uvx", "--python", config.python_version, *args]
        case "pip" | "pip3" as pip if config.allow_pip:
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
    config: SpawnSettings,
) -> list[str]:
    cache_path = anyio.Path(config.cache_path)
    await cache_path.mkdir(parents=True, exist_ok=True)
    binary_path = cache_path / Path(dist.cmd).name

    if not await binary_path.exists():
        logger.info("Downloading binary from {} to {}", dist.archive, binary_path)

        import tempfile

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
                # registry cmd may include relative path
                binary_name=Path(dist.cmd).name,
                dest_dir=Path(cache_path),
            )

        await binary_path.chmod(0o755)

    return [str(binary_path), *dist.args, *extra_args]
