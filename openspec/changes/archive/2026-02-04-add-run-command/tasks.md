## 1. CLI Entry Point Setup

- [x] 1.1 Identify the main `cyclopts` app instance in the codebase (likely in `src/acp_agent/cli.py`).
- [x] 1.2 Define a new `run` command function with appropriate `cyclopts` annotations for `agent_id`, `--env`, `--cwd`, `--cache-path`, and extra arguments.

## 2. Parameter Parsing and Mapping

- [x] 2.1 Implement parsing for environment variables from `--env` (strings like `KEY=VAL`) into a dictionary.
- [x] 2.2 Configure `cyclopts` to capture extra positional arguments after `agent_id`.
- [x] 2.3 Map CLI parameters to the `run_local` function arguments in `src/acp_agent/executor.py`.

## 3. Implementation and Async Integration

- [x] 3.1 Implement the `run` command body to call `run_local` using `anyio.run` or an existing async runner if available.
- [x] 3.2 Add basic validation for `--env` format and `--cwd` existence.

## 4. Verification and Testing

- [x] 4.1 Verify `acp-agent run --help` shows correct documentation and argument descriptions.
- [x] 4.2 Perform manual tests with a sample agent ID to verify argument passing, environment variable setting, and custom CWD.
