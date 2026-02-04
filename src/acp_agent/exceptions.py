from __future__ import annotations


class RegistryError(Exception):
    """Base exception for the registry module."""


class AgentNotFoundError(RegistryError):
    """Raised when an agent is not found in the registry."""


class DistributionError(RegistryError):
    """Raised when no valid distribution is found for the current platform."""


class RunnerNotFoundError(RegistryError):
    """Raised when no suitable system tools are found for the distribution."""


class ExecutionError(RegistryError):
    """Raised when the subprocess execution fails."""


class DownloadError(RegistryError):
    """Raised when downloading a binary distribution fails."""
