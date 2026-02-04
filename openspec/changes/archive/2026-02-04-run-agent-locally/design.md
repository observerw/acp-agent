## Context

The `acp-agent` project defines a registry of agents with multiple distribution methods (`npx`, `uvx`, `binary`). To make these agents useful locally, we need a reliable way to launch them using system-available tools.

## Goals / Non-Goals

**Goals:**
- Provide a `run_local(agent_id: str, extra_args: Sequence[str] = (), env: dict[str, str] | None = None, cwd: str | Path | None = None, cache_path: Path | None = None)` function.
- Automatically detect and use preferred system runners (`bunx` > `npx`, `uvx` > `pip`).
- Download and cache binary distributions using `curl` or `wget`.
- Raise clear errors when a distribution type is unsupported by the current system environment.

**Non-Goals:**
- Managing the lifecycle of the agent process (e.g., auto-restart, monitoring). This function just starts the process and waits for it to complete.
- Installing `bun`, `npm`, `uv`, or `python` for the user.
- Sandboxing the agent execution.

## Decisions

- **Tool Detection**: Use `shutil.which` to locate executables in the system PATH.
- **Priority Logic**:
    - `NpxDistribution`: Prefer `bunx` for speed, fallback to `npx`.
    - `UvxDistribution`: Prefer `uvx`, fallback to `pip install` (though `pip` is trickier for "run once", we might just support `uvx` for now or use `python -m pip` to install to a temp venv). *Correction*: User suggested `uvx` (priority) and `pip`. For `pip`, we'll likely need to install the package first.
    - `BinaryDistribution`: Prefer `curl -L -o`, fallback to `wget -O`.
- **Cache Path**: Default to `Path.home() / ".local" / "bin"`. Ensure the directory exists before downloading.
- **Execution**: Use `subprocess.run` (or `subprocess.Popen` for better control) with `env`, `args`, and `cwd`. 
    - Merge `RegistryAgent.distribution.env` with the provided `env` parameter.
    - Combine `RegistryAgent.distribution.args` with `extra_args`.
- **Logging**: Use a dedicated logger for `acp_agent.registry`. Log key events:
    - Tool detection results (e.g., "Found bunx at /usr/local/bin/bunx").
    - Download progress for binaries.
    - Subprocess execution commands (at DEBUG level).
    - Errors and fallbacks.
- **Error Handling**: Use a hierarchy of custom exceptions:
    - `RegistryError` (base)
        - `AgentNotFoundError`: Agent ID not found in registry.
        - `DistributionError`: No valid distribution found for current platform.
        - `RunnerNotFoundError`: No suitable system tools found for the distro (e.g., missing both `uvx` and `pip`).
        - `ExecutionError`: Subprocess returned non-zero exit code.
        - `DownloadError`: Failed to fetch binary.

## Risks / Trade-offs

- **Security**: Executing binaries or packages from a registry carries risks. 
    - *Mitigation*: The registry itself is assumed to be a trusted source for the user's intent.
- **Pip Complexity**: `pip` is not a direct runner like `uvx`. 
    - *Mitigation*: If `uvx` is missing, we might inform the user or attempt a `pip install` to a managed location, but `uvx` is strongly preferred.
- **Binary Compatibility**: Downloaded binaries might not match the user's architecture.
    - *Mitigation*: The registry's `binary` field is a mapping (e.g., `{"linux-x64": ...}`). We must detect the current platform/arch to pick the right one.
