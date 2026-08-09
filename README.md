# ACP Agent CLI & SDK

> # ⚠️ DEPRECATED / 已废弃
>
> **This project is deprecated and is no longer maintained.**
>
> **Use [`OpenInsightDev/acp-agent`](https://github.com/OpenInsightDev/acp-agent) instead** — it is the actively maintained successor and provides significantly better feature support, including agent discovery, installation, cache management, running, and HTTP/WebSocket serving of [ACP](https://agentclientprotocol.com/) agents as both a CLI and a Rust library.
>
> **请改用 [`OpenInsightDev/acp-agent`](https://github.com/OpenInsightDev/acp-agent)：**
> `https://github.com/OpenInsightDev/acp-agent`

[![PyPI version](https://img.shields.io/pypi/v/acp-agent.svg)](https://pypi.org/project/acp-agent/)
[![Python versions](https://img.shields.io/pypi/pyversions/acp-agent.svg)](https://pypi.org/project/acp-agent/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`acp-agent` is a Python CLI and SDK for the [ACP Registry](https://github.com/agentclientprotocol/registry). It helps you discover agents, prepare runtime dependencies, run them locally, and generate container-ready startup commands.

## Features

- List and search agents from the public ACP registry.
- Run an agent by ID with optional environment variables and working directory.
- Pre-install runtime requirements with `setup`.
- Include a built-in `dummy` ACP agent for protocol testing.
- Use the async `ACPAgent` SDK in Python applications.
- Generate a `Containerfile` that embeds agent setup and command.

## Installation

Requires Python 3.12+.

```bash
pip install acp-agent
```

You can also run cli directly with `uvx` without installing globally:

```bash
uvx acp-agent --help
```

## CLI Usage

```bash
# Show all commands
acp-agent --help

# List all agents
acp-agent list

# Search by id or name
acp-agent search opencode

# Pre-setup an agent (install/download runtime dependencies)
acp-agent setup opencode

# Run an agent
acp-agent run opencode

# Run with environment variables and working directory
acp-agent run opencode -e DEBUG=true --cwd ./my-project

# Run the built-in dummy agent
acp-agent dummy --seed 42
```

When using `uvx`, replace `acp-agent` with `uvx acp-agent` in the examples above.

Example output (`acp-agent search opencode`):

```text
            Search Results for 'opencode'
┏━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ID       ┃ Name     ┃ Description                  ┃
┡━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ opencode │ OpenCode │ The open source coding agent │
└──────────┴──────────┴──────────────────────────────┘
```

Example output (`acp-agent list`, excerpt):

```text
                          Available Agents
┏━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ID             ┃ Name           ┃ Description                                ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ claude-acp     │ Claude Agent   │ ACP wrapper for Anthropic's Claude         │
│ codex-acp      │ Codex CLI      │ ACP adapter for OpenAI's coding assistant  │
│ opencode       │ OpenCode       │ The open source coding agent               │
│ ...            │ ...            │ ...                                        │
└────────────────┴────────────────┴────────────────────────────────────────────┘
```

## SDK Usage

```python
import asyncio

from acp_agent import ACPAgent


async def main() -> None:
    agent = await ACPAgent.create(
        "opencode",
        env={"DEBUG": "true"},
        workdir="./my-project",
    )

    process = await agent.run()
    returncode = await process.wait()
    print(f"agent exited: {returncode}")


if __name__ == "__main__":
    asyncio.run(main())
```

You can also render a containerfile snippet with the same agent instance:

```python
import asyncio
from pathlib import Path

from acp_agent import ACPAgent


async def main() -> None:
    agent = await ACPAgent.create("opencode")
    content = await agent.format_containerfile("FROM python:3.12-slim")
    Path("Containerfile").write_text(content)


if __name__ == "__main__":
    asyncio.run(main())
```

Example rendered output:

```dockerfile
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ENV DEBUG=true

# note: this command will install any runtime dependencies and cache them in a layer
RUN uvx acp-agent setup opencode

WORKDIR /workspace

CMD ["opencode", "acp"]
```

## Runtime Settings

`acp-agent` reads settings from environment variables with the `ACP_AGENT_` prefix:

- `ACP_AGENT_PYTHON_VERSION` (default: `3.12`)
- `ACP_AGENT_ALLOW_PIP` (default: `false`)
- `ACP_AGENT_CACHE_PATH` (default: platform cache dir)
- `ACP_AGENT_BIN_DIR_PATH` (default: `~/.local/bin`)

## License

[MIT License](LICENSE)
