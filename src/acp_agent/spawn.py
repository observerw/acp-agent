from __future__ import annotations

import asyncio
import os
from asyncio import StreamReader, StreamWriter
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple, TypedDict

from loguru import logger

from acp_agent.utils.platform import get_platform_key
from acp_agent.utils.sh import available_programs

from .config import SpawnConfig, settings
from .exceptions import AgentNotFoundError, DistributionError
from .registry import fetch_agent
from .registry.model import BinaryDistribution, NpxDistribution, UvxDistribution
from .utils.archive import extract_binary


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
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
) -> int:
    """Run a subprocess asynchronously and wait for it to complete."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        env=env,
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    await process.communicate()
    if (returncode := process.returncode) != 0:
        msg = f"Process failed with return code {process.returncode}"
        raise RuntimeError(msg)
    return returncode


async def spawn_process(
    cmd: Sequence[str],
    *,
    env: dict[str, str] | None = None,
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


async def run_local(
    id: str,
    *,
    extra_args: Sequence[str] = (),
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
    config: SpawnConfig | None = None,
) -> AgentStream:
    """Run an agent locally by its ID."""
    cmd_info = await _resolve_agent_command(
        id, extra_args=extra_args, env=env, cwd=cwd, config=config
    )
    return await spawn_process(**cmd_info)


async def run_local_attached(
    id: str,
    *,
    extra_args: Sequence[str] = (),
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
    config: SpawnConfig | None = None,
) -> int:
    cmd_info = await _resolve_agent_command(
        id, extra_args=extra_args, env=env, cwd=cwd, config=config
    )
    return await run_process(**cmd_info)


async def _resolve_agent_command(
    id: str,
    *,
    extra_args: Sequence[str] = (),
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
    config: SpawnConfig | None = None,
) -> AgentCommand:
    """Resolve agent ID to executable command."""
    agent = await fetch_agent(id)
    if not agent:
        msg = f"Agent with ID '{id}' not found in registry."
        raise AgentNotFoundError(msg)

    dist = agent.dist_union
    config = config or settings

    if dist.npx:
        return await _prepare_npx(
            dist.npx, extra_args=extra_args, env=env, cwd=cwd, config=config
        )

    if dist.uvx:
        return await _prepare_uvx(
            dist.uvx, extra_args=extra_args, env=env, cwd=cwd, config=config
        )

    if dist.binary:
        platform_key = get_platform_key()
        binary_dist = dist.binary.get(platform_key)
        if not binary_dist:
            msg = f"No binary distribution found for platform '{platform_key}'"
            raise DistributionError(msg)
        return await _prepare_binary(
            binary_dist, extra_args=extra_args, env=env, cwd=cwd, config=config
        )

    raise DistributionError(f"Agent '{id}' has no supported distribution method.")


async def _prepare_npx(
    dist: NpxDistribution,
    *,
    extra_args: Sequence[str] = (),
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
    config: SpawnConfig | None = None,
) -> AgentCommand:
    args = [dist.package, *dist.args, *extra_args]
    match await available_programs("bunx", "npx"):
        case "bunx":
            cmd = ["bunx", *args]
        case "npx":
            cmd = ["npx", "-y", *args]
        case _:
            raise AssertionError

    full_env = {**os.environ, **dist.env, **(env or {})}

    logger.debug("Preparing command: {}", cmd)
    return AgentCommand(cmd=cmd, env=full_env, cwd=Path(cwd) if cwd else None)


async def _prepare_uvx(
    dist: UvxDistribution,
    *,
    extra_args: Sequence[str] = (),
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
    config: SpawnConfig | None = None,
) -> AgentCommand:
    config = config or settings
    args = [dist.package, *dist.args, *extra_args]
    match await available_programs("uvx", "pip", "pip3"):
        case "uvx":
            cmd = ["uvx", "--python", config.python_version, *args]
        case "pip" | "pip3":
            logger.warning(
                "Using pip as fallback for uvx. This will install the package globally or in the current env."
            )
            await run_process(["python", "-m", "pip", "install", dist.package])
            cmd = [*args]
        case _:
            raise AssertionError

    full_env = {**os.environ, **dist.env, **(env or {})}
    logger.debug("Preparing command: {}", cmd)
    return AgentCommand(cmd=cmd, env=full_env, cwd=Path(cwd) if cwd else None)


async def _prepare_binary(
    dist: BinaryDistribution,
    *,
    extra_args: Sequence[str] = (),
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
    config: SpawnConfig | None = None,
) -> AgentCommand:
    config = config or settings
    cache_path = config.cache_path
    if cache_path is None:
        cache_path = Path.home() / ".local" / "bin"

    cache_path.mkdir(parents=True, exist_ok=True)
    binary_path = cache_path / Path(dist.cmd).name

    if not binary_path.exists():
        logger.info("Downloading binary from {} to {}", dist.archive, binary_path)

        import tempfile

        with tempfile.NamedTemporaryFile(suffix=Path(dist.archive).suffix) as tmp:
            match await available_programs("curl", "wget"):
                case "curl":
                    await run_process(["curl", "-L", "-o", tmp.name, dist.archive])
                case "wget":
                    await run_process(["wget", "-O", tmp.name, dist.archive])
                case _:
                    raise AssertionError

            await asyncio.to_thread(
                extract_binary,
                archive_path=tmp.name,
                binary_name=Path(dist.cmd).name,
                dest_dir=cache_path,
            )

        binary_path.chmod(0o755)

    cmd = [str(binary_path), *dist.args, *extra_args]
    full_env = {**os.environ, **dist.env, **(env or {})}
    logger.debug("Preparing command: {}", cmd)
    return AgentCommand(cmd=cmd, env=full_env, cwd=Path(cwd) if cwd else None)
