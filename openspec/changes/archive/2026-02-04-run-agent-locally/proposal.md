## Why

Users need a way to execute agents discovered via the ACP registry on their local machine. Currently, the `RegistryAgent` data structure defines how an agent *could* be run (npx, uvx, binary), but there is no implementation to actually perform the execution and manage the required system dependencies.

## What Changes

- Implement a `run_local` function that takes an agent `id` to execute it.
- Add system dependency detection and validation for different distribution types:
    - **Npx**: Support `bunx` (preferred) and `npx`.
    - **Uvx**: Support `uvx` (preferred) and `pip` (as fallback or alternative runner).
    - **Binary**: Handle downloading via `curl` (preferred) or `wget` before execution. Support an optional `cache_path` (defaulting to a sensible location like `~/.local/bin`) to store these binaries.
- Implement a fallback mechanism that checks for available system tools and raises a descriptive error if no suitable runners are found.

## Capabilities

### New Capabilities
- `run-local`: Provides an API to detect system runners, validate agent distributions, and execute them in a local environment.

### Modified Capabilities
- None.

## Impact

- `src/acp_agent/registry.py`: Likely where the new function or associated logic will reside.
- System dependencies: Requires access to shell/subprocess and common CLI tools (`bunx`, `npx`, `uvx`, `curl`, `wget`).
