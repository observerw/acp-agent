from __future__ import annotations

import os
import shutil
from asyncio import StreamReader, StreamWriter
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple, TypedDict

import anyio
from loguru import logger

from acp_agent.utils.platform import get_platform_key
from acp_agent.utils.sh import available_programs

from .exceptions import AgentNotFoundError, DistributionError
from .models import BinaryDistribution, NpxDistribution, UvxDistribution
from .registry import fetch_agent


class AgentStreamParams(TypedDict):
    input_stream: StreamWriter
    output_stream: StreamReader


class AgentStream(NamedTuple):
    input: StreamWriter
    output: StreamReader

    def as_params(self) -> AgentStreamParams:
        return AgentStreamParams(input_stream=self.input, output_stream=self.output)


async def run_local(
    id: str,
    *,
    extra_args: Sequence[str] = (),
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
    **kwargs,
) -> None:
    """Run an agent locally by its ID."""

    agent = await fetch_agent(id)
    if not agent:
        msg = f"Agent with ID '{id}' not found in registry."
        raise AgentNotFoundError(msg)

    dist = agent.distribution

    if dist.npx:
        await execute_npx(dist.npx, extra_args=extra_args, env=env, cwd=cwd, **kwargs)
    elif dist.uvx:
        await execute_uvx(dist.uvx, extra_args=extra_args, env=env, cwd=cwd, **kwargs)
    elif dist.binary:
        platform_key = get_platform_key()
        binary_dist = dist.binary.get(platform_key)
        if not binary_dist:
            msg = f"No binary distribution found for platform '{platform_key}'"
            raise DistributionError(msg)
        await execute_binary(
            binary_dist, extra_args=extra_args, env=env, cwd=cwd, **kwargs
        )
    else:
        msg = f"Agent '{id}' has no supported distribution method."
        raise DistributionError(msg)


async def execute_npx(
    dist: NpxDistribution,
    *,
    extra_args: Sequence[str] = (),
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
    **kwargs,
) -> None:
    tool = await available_programs("bunx", "npx")
    cmd = [tool, dist.package, *dist.args, *extra_args]
    full_env = {**os.environ, **dist.env, **(env or {})}

    logger.debug("Executing command: {}", cmd)
    await anyio.run_process(cmd, env=full_env, cwd=cwd)


async def execute_uvx(
    dist: UvxDistribution,
    *,
    extra_args: Sequence[str] = (),
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
    python_version: str = "3.12",
    **kwargs,
) -> None:
    tool = await available_programs("uvx", "pip")
    if tool == "uvx":
        cmd = ["uvx", "--python", python_version, dist.package, *dist.args, *extra_args]
    else:
        logger.warning(
            "Using pip as fallback for uvx. This will install the package globally or in the current env."
        )
        await anyio.run_process(["python", "-m", "pip", "install", dist.package])
        cmd = [dist.package, *dist.args, *extra_args]

    full_env = {**os.environ, **dist.env, **(env or {})}
    logger.debug("Executing command: {}", cmd)
    await anyio.run_process(cmd, env=full_env, cwd=cwd)


async def execute_binary(
    dist: BinaryDistribution,
    extra_args: Sequence[str] = (),
    env: dict[str, str] | None = None,
    cwd: str | Path | None = None,
    cache_path: Path | None = None,
    **kwargs,
) -> None:
    if cache_path is None:
        cache_path = Path.home() / ".local" / "bin"

    cache_path.mkdir(parents=True, exist_ok=True)
    binary_path = cache_path / Path(dist.cmd).name

    if not binary_path.exists():
        logger.info("Downloading binary from {} to {}", dist.archive, binary_path)
        downloader = await available_programs("curl", "wget")

        import tempfile

        with tempfile.NamedTemporaryFile(suffix=Path(dist.archive).suffix) as tmp:
            if downloader == "curl":
                await anyio.run_process(["curl", "-L", "-o", tmp.name, dist.archive])
            else:
                await anyio.run_process(["wget", "-O", tmp.name, dist.archive])

            if dist.archive.endswith(".zip"):
                import zipfile

                with zipfile.ZipFile(tmp.name, "r") as zip_ref:
                    # Extract the specific command binary
                    zip_ref.extract(Path(dist.cmd).name, path=cache_path)
            elif dist.archive.endswith((".tar.gz", ".tgz")):
                import tarfile

                with tarfile.open(tmp.name, "r:gz") as tar_ref:
                    tar_ref.extract(Path(dist.cmd).name, path=cache_path)
            else:
                shutil.copy(tmp.name, binary_path)

        binary_path.chmod(0o755)

    cmd = [str(binary_path), *dist.args, *extra_args]
    full_env = {**os.environ, **dist.env, **(env or {})}
    logger.debug("Executing command: {}", cmd)
    await anyio.run_process(cmd, env=full_env, cwd=cwd)
