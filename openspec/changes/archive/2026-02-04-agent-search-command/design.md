## Context

The `acp-agent` CLI currently allows users to list all available agents, but lacks a search capability. As the registry grows, finding specific agents becomes more difficult.

## Goals / Non-Goals

**Goals:**
- Add a `search` command to the `acp-agent` CLI.
- Support fuzzy (substring) matching on agent `name` and `id`.
- Display results in a formatted table.

**Non-Goals:**
- Complex relevance ranking or weighted fuzzy matching.
- Searching within agent descriptions or other metadata (initially).

## Decisions

- **Filtering Logic**: We will use case-insensitive substring matching on both the agent `id` and `name`. This provides a good balance between simplicity and utility without adding new dependencies.
- **CLI Implementation**: The `search` command will be added to `src/acp_agent/cli/app.py` using `cyclopts`.
- **Registry Integration**: We will reuse `list_agents` from `src/acp_agent/registry.py` to fetch the current state of the registry and then filter locally.

## Risks / Trade-offs

- [Risk] Performance issues if the registry becomes extremely large. → [Mitigation] The current registry size is small and fetched as a single JSON; local filtering is efficient. If it grows to thousands, we may need a backend search API.
- [Risk] Poor search quality without proper fuzzy matching (e.g., Levenshtein distance). → [Mitigation] Substring matching is usually sufficient for agent names. We can add a specialized fuzzy matching library later if needed.
