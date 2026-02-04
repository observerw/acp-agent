## Why

Currently, the `acp-agent` lacks a direct CLI entry point to execute agents locally using the `run_local` function. Users need a user-friendly command that exposes the flexibility of the underlying executor (extra arguments, environment variables, working directory, etc.) with proper documentation and validation.

## What Changes

- Add a new CLI command `acp-agent run <agent-id>`.
- Support `--args` (or positional remaining args) to pass to the agent.
- Support `--env` (multiple `-e KEY=VAL`) to set environment variables.
- Support `--cwd` to specify the execution directory.
- Support `--cache-path` to override the default binary/package cache location.
- Use `cyclopts` to ensure high-quality help text and type validation.

## Capabilities

### New Capabilities
- `agent-execution`: Defines the requirements for finding, downloading (if needed), and executing an agent locally with user-defined environment and arguments.

### Modified Capabilities
<!-- None -->

## Impact

- `src/acp_agent/cli.py` (or where the main entry point is): Will be modified to include the new `run` command.
- `src/acp_agent/executor.py`: Already contains `run_local`, which will be the primary implementation target.
