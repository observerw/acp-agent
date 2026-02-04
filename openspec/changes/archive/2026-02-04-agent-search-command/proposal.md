## Why

Users currently have to list all agents and manually find the one they need. Providing a search command with fuzzy matching improves discoverability and efficiency when working with a large number of agents.

## What Changes

- Add a new CLI command `acp-agent search <fuzzy_string>`.
- The command will perform a fuzzy search across agent names in the registry.
- It will display a list of matching agents (similar to the `list` command).

## Capabilities

### New Capabilities
- `agent-search`: Provides the ability to search for agents by name using fuzzy matching and list matching agents.

### Modified Capabilities
- None

## Impact

- CLI: New `search` command in `acp-agent`.
- Registry: Utility for fuzzy searching agent metadata.
