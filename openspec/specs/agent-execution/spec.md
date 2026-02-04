# agent-execution

## Purpose
Defines the requirements for finding, downloading, and executing an agent locally with user-defined environment and arguments.

## Requirements

### Requirement: Run Command Execution
The `acp-agent` SHALL provide a `run` command that takes an `agent-id` and executes the agent locally.

#### Scenario: Basic execution
- **WHEN** user runs `acp-agent run some-agent`
- **THEN** the system fetches `some-agent` from the registry and executes it with default settings.

### Requirement: Agent Arguments Passing
The `run` command SHALL allow passing additional arguments to the agent being executed.

#### Scenario: Passing extra arguments
- **WHEN** user runs `acp-agent run some-agent --arg1 value1`
- **THEN** the system executes `some-agent` and passes `--arg1` and `value1` as extra arguments to the agent's command.

### Requirement: Environment Variable Support
The `run` command SHALL support setting environment variables for the agent's execution environment via `--env` or `-e` flags.

#### Scenario: Setting environment variables
- **WHEN** user runs `acp-agent run some-agent -e KEY=VAL -e DEBUG=true`
- **THEN** the agent is executed with `KEY=VAL` and `DEBUG=true` added to its environment.

### Requirement: Custom Working Directory
The `run` command SHALL support specifying the current working directory (CWD) for the agent's execution via a `--cwd` flag.

#### Scenario: Specifying CWD
- **WHEN** user runs `acp-agent run some-agent --cwd /tmp/test-run`
- **THEN** the agent is executed with `/tmp/test-run` as its working directory.

### Requirement: Custom Cache Path
The `run` command SHALL support overriding the default cache path for agent distributions via a `--cache-path` flag.

#### Scenario: Specifying cache path
- **WHEN** user runs `acp-agent run some-agent --cache-path ./custom-cache`
- **THEN** the system uses `./custom-cache` to store/find the agent's distribution binaries or packages.
