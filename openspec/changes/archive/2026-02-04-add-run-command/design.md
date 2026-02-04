## Context

Currently, `acp-agent` has a robust `run_local` function in `src/acp_agent/executor.py` capable of executing agents from various distributions (npx, uvx, binary). However, this functionality is not exposed via the CLI. We need to integrate this into the `cyclopts`-based CLI to provide a seamless user experience for running agents.

## Goals / Non-Goals

**Goals:**
- Expose `run_local` functionality through an `acp-agent run` command.
- Provide user-friendly arguments for environment variables, working directory, and extra arguments.
- Maintain consistency with existing CLI patterns in `acp-agent`.
- Ensure robust error handling and informative help messages.

**Non-Goals:**
- Implementing remote execution (this is strictly for `run_local`).
- Modifying the core logic of `run_local` unless necessary for CLI integration.
- Adding complex orchestration or scheduling features.

## Decisions

### 1. Command Structure
We will add a `run` command to the main `app` (or equivalent `cyclopts` instance).
- **Rationale**: `run` is the most intuitive verb for this action.
- **Alternatives**: `execute`, `start`. `run` is standard across similar tools (e.g., `npm run`, `uv run`).

### 2. Handling Environment Variables
Use a list of strings for `--env` or `-e`, parsed into a dictionary.
- **Rationale**: This matches the convention of `docker run -e KEY=VAL`. Cyclopts handles list accumulation easily.
- **Implementation**: A helper or validator will split `KEY=VAL` strings.

### 3. Extra Arguments
Use a `*args` (positional remainder) approach for arguments passed to the agent.
- **Rationale**: Allows users to run `acp-agent run agent-id --agent-arg1 --agent-arg2` naturally.
- **Alternatives**: A dedicated `--args` flag. Positional remainder is more ergonomic.

### 4. Integration with Async
Since `run_local` is `async`, the CLI command must be handled within an event loop.
- **Rationale**: `cyclopts` supports async functions if the application runner handles them (usually via `anyio.run` or similar).

## Risks / Trade-offs

- [Risk] → **Argument Collision**: If the agent and `acp-agent run` share flag names, there might be ambiguity.
  - Mitigation: Use `--` to separate `acp-agent` args from agent args, or rely on positional remainder after the agent ID.
- [Risk] → **Environment Variable Parsing**: Improperly formatted `KEY=VAL` strings.
  - Mitigation: Add clear error messages if the split fails.
