## ADDED Requirements

### Requirement: Search Agents by Name
The `acp-agent` CLI SHALL provide a `search` command that accepts a fuzzy string and returns a list of matching agents from the registry.

#### Scenario: Single exact match
- **WHEN** the user runs `acp-agent search cyclopts`
- **THEN** the system displays a list containing the `cyclopts` agent

#### Scenario: Multiple fuzzy matches
- **WHEN** the user runs `acp-agent search agent`
- **THEN** the system displays a list of all agents whose names contain "agent"

#### Scenario: No matches
- **WHEN** the user runs `acp-agent search non-existent-agent`
- **THEN** the system displays a message indicating no agents were found

### Requirement: Display Agent List in Search Results
The search results SHALL display matching agents in a list format (ID, Name, Description), identical or similar to the `list` command output.

#### Scenario: Display details for a match
- **WHEN** a search returns matches
- **THEN** each result shows at least the agent's name and its short description
