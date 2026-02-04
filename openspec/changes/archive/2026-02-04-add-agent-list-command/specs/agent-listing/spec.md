## ADDED Requirements

### Requirement: CLI command to list agents
The `acp-agent` CLI SHALL provide a `list` command that displays a table of available agents from the ACP registry.

#### Scenario: Successfully list agents
- **WHEN** user runs `acp-agent list`
- **THEN** system fetches agent list from the registry and displays it in a table with columns for ID, Name, and Description.

### Requirement: Visual formatting with rich
The `list` command SHALL use the `rich` library to present the agent information in an aesthetically pleasing table.

#### Scenario: Table display
- **WHEN** user runs `acp-agent list`
- **THEN** the output is a formatted table with headers and borders.
