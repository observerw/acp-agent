## Context

The `acp-agent` CLI needs a way to list available agents from the remote registry. The registry data is already accessible via `src/acp_agent/registry.py`. The project uses `cyclopts` for CLI management.

## Goals / Non-Goals

**Goals:**
- Add `acp-agent list` command.
- Use `rich` library to render a formatted table.
- Display columns: ID, Name, Description, and possibly Version/Author.

**Non-Goals:**
- Adding filtering or search to the `list` command (keep it simple for now).
- Local caching of the registry list.

## Decisions

- **CLI Framework**: Use existing `cyclopts` application in `src/acp_agent/cli/app.py`.
- **Output Rendering**: Use `rich.console.Console` and `rich.table.Table` for high-quality terminal output.
- **Dependency Management**: Add `rich` to `pyproject.toml`.
- **Data Source**: Use `list_agents()` from `src/acp_agent/registry.py`.

## Risks / Trade-offs

- **[Risk] Network Failure** → Mitigation: Use `httpx` with sensible timeouts and handle `httpx.HTTPError` gracefully by showing a user-friendly error message.
- **[Risk] Large Registry** → Mitigation: `rich` handles truncation well, but if the list grows very large, we might need pagination in the future (out of scope for now).
