## 1. Setup

- [x] 1.1 Add `rich` to `pyproject.toml` dependencies.
- [x] 1.2 Run `uv sync` (or equivalent) to install `rich`.

## 2. Implementation

- [x] 2.1 Import `rich` and `list_agents` in `src/acp_agent/cli/app.py`.
- [x] 2.2 Define the `list_agents_command` (or similar) using `@app.command`.
- [x] 2.3 Implement the logic to fetch agents and display them in a `rich` table.
- [x] 2.4 Add error handling for registry fetch failures.

## 3. Verification

- [x] 3.1 Execute `acp-agent list` to verify the table display.
- [x] 3.2 Check that the table includes ID, Name, and Description columns.
