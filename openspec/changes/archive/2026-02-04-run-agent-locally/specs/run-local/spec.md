## ADDED Requirements

### Requirement: Local Agent Execution
The system SHALL provide a way to run a registry agent locally by its ID. It SHALL support passing extra arguments, custom environment variables, and a specific working directory.

#### Scenario: Run npx distribution with extra args
- **WHEN** user calls `run_local` with `extra_args=["--foo"]`
- **THEN** system SHALL combine the agent's default args with `["--foo"]` and execute using `bunx` or `npx`

#### Scenario: Run with environment overrides
- **WHEN** user calls `run_local` with `env={"API_KEY": "secret"}`
- **THEN** system SHALL merge the agent's default environment with `{"API_KEY": "secret"}` and execute

#### Scenario: Run in specific working directory
- **WHEN** user calls `run_local` with `cwd="/tmp/workspace"`
- **THEN** the subprocess SHALL be executed with `/tmp/workspace` as its working directory

### Requirement: System Tool Validation
The system MUST verify that at least one compatible runner exists for the agent's distribution type.

#### Scenario: No runners available
- **WHEN** an agent requires `uvx` but neither `uvx` nor `pip` is installed
- **THEN** system SHALL raise a descriptive error indicating the missing tools

### Requirement: Binary Caching
The system SHALL support caching downloaded binaries to avoid redundant downloads.

#### Scenario: Use default cache path
- **WHEN** no `cache_path` is provided for a binary distribution
- **THEN** system SHALL use `~/.local/bin` as the default directory

#### Scenario: Skip download if exists
- **WHEN** a binary for the agent ID and version already exists in the `cache_path`
- **THEN** system SHALL skip the download and execute the existing file

### Requirement: Logging and Observability
The system SHALL log execution steps and errors to assist with debugging.

#### Scenario: Log tool detection
- **WHEN** the system searches for a runner (e.g., `bunx`)
- **THEN** it SHALL log whether the tool was found and its path

#### Scenario: Log execution command
- **WHEN** an agent is about to be executed
- **THEN** it SHALL log the full command and environment variables at DEBUG level

### Requirement: Structured Error Handling
The system SHALL use specific exceptions to distinguish between different failure modes.

#### Scenario: Raise specific error for missing agent
- **WHEN** `run_local` is called with an invalid ID
- **THEN** it SHALL raise `AgentNotFoundError`

#### Scenario: Raise specific error for failed download
- **WHEN** `curl` or `wget` fails during binary fetching
- **THEN** it SHALL raise `DownloadError` with the underlying reason
