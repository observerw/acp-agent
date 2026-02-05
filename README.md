# ACP Agent CLI 🚀

[![PyPI version](https://img.shields.io/pypi/v/acp-agent.svg)](https://pypi.org/project/acp-agent/)
[![Python versions](https://img.shields.io/pypi/pyversions/acp-agent.svg)](https://pypi.org/project/acp-agent/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

This project provides a friendly and intuitive Command Line Interface (CLI) for the [ACP Registry](https://github.com/agentclientprotocol/registry), enabling developers to quickly browse, search, and run ACP (Agent Client Protocol) agents locally.

## Motivation 💡

The official ACP Registry provides an extensive list of agents. This project aims to:

- **Instant Viewing**: Display all available agents in a beautiful terminal-based table.
- **Quick Discovery**: Support keyword-based fuzzy searching to find the right agent in seconds.
- **Local Execution**: Provide one-click run capabilities, automatically handling environment and parameter configurations to accelerate development and testing.

## Getting Started 🛠️

We recommend using [uv](https://github.com/astral-sh/uv) to manage and run this project.

### Basic Usage

```bash
uvx acp-agent --help
```

### Core Features

#### 1. List All Agents

Fetch and display the complete list of agents from the Registry:

```bash
uv run acp-agent list
```

#### 2. Search for Agents

Search by name or ID using keywords:

```bash
uv run acp-agent search opencode
```

```
Search Results for 'opencode'
┏━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ID       ┃ Name     ┃ Description                  ┃
┡━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ opencode │ OpenCode │ The open source coding agent │
└──────────┴──────────┴──────────────────────────────┘
```

#### 3. Run an Agent Locally

Run an agent by its ID with support for argument passthrough and environment variables:

```bash
# Basic execution
uv run acp-agent run <agent-id>

# Run with a specific working directory and environment variables
uv run acp-agent run opencode --cwd ./my-project -e DEBUG=true
```

## License 📄

[MIT License](LICENSE)
