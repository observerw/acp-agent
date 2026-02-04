## Why

Currently, there is no way for users to discover available agents via the `acp-agent` CLI. Users must manually check the registry JSON or other documentation. Providing a `list` command improves discoverability and user experience.

## What Changes

- Add a new `list` command to the `acp-agent` CLI.
- Fetch agent data from the ACP registry using existing `list_agents` function.
- Display the agents in a clean, formatted table using the `rich` library.

## Capabilities

### New Capabilities
- `agent-listing`: Provides a CLI command to fetch and display all available agents from the ACP registry in a human-readable table format.

### Modified Capabilities
<!-- No requirement changes to existing capabilities -->

## Impact

- `src/acp_agent/cli/app.py`: Will be updated to include the new `list` command.
- `src/acp_agent/registry.py`: Already provides `list_agents`, used by the new command.
- Dependencies: Add `rich` to the project if not already present.
