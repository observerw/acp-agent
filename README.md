# ACP Agent CLI & SDK 🚀

[![PyPI version](https://img.shields.io/pypi/v/acp-agent.svg)](https://pypi.org/project/acp-agent/)
[![Python versions](https://img.shields.io/pypi/pyversions/acp-agent.svg)](https://pypi.org/project/acp-agent/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This project provides a friendly and intuitive CLI and SDK for the [ACP Registry](https://github.com/agentclientprotocol/registry), enabling developers to quickly browse, search, run, and containerize [ACP (Agent Client Protocol)](https://agentclientprotocol.com) agents.

## Motivation 💡

The official ACP Registry provides an extensive list of agents. This project simplifies discovery and integration through three core pillars:

- **Interactive Discovery**: Browse and fuzzy-search the entire registry directly from your terminal.
- **Seamless Execution**: Run any agent locally with automatic environment setup, or integrate them into Python apps via the async SDK.
- **Production Deployment**: Automatically generate optimized Containerfiles to run agents in isolated environments or CI/CD pipelines.

## Usage 🚀

There are three ways to use `acp-agent`:

### 1. CLI Usage

We recommend using [uv](https://github.com/astral-sh/uv) to manage and run this project.

```bash
# List all agents
uvx acp-agent list

# Search for agents
uvx acp-agent search opencode

# Run an agent locally
uvx acp-agent run opencode

# Run with a specific working directory, environment variables, and extra arguments
# Any arguments after the options are passed directly to the agent
uvx acp-agent run opencode --cwd ./my-project -e DEBUG=true -- --help
```

#### Example Search Output

```
Search Results for 'opencode'
┏━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ID       ┃ Name     ┃ Description                  ┃
┡━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ opencode │ OpenCode │ The open source coding agent │
└──────────┴──────────┴──────────────────────────────┘
```

### 2. SDK Usage

You can integrate `acp-agent` into your Python projects.

```python
import asyncio
from acp_agent import run_local

async def main():
    # Run an agent and attach to its output (stdout/stderr)
    # This will automatically handle downloading and environment setup
    # returns the exit code of the agent
    exit_code = await run_local("opencode", attach=True)
    print(f"Agent exited with code: {exit_code}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Container Usage

Generate a `Containerfile` to run an agent inside ANY container you defined.

```python
import asyncio
from pathlib import Path
from acp_agent import format_containerfile

async def main():
    # Generate Containerfile content for 'opencode'
    # This will inject the agent installation and CMD into your base image
    content = await format_containerfile(
        agent_id="opencode",
        containerfile="FROM python:3.12-slim"
    )
    Path("Dockerfile").write_text(content)

if __name__ == "__main__":
    asyncio.run(main())
```

## License 📄

[MIT License](LICENSE)
