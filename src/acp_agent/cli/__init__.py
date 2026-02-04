from __future__ import annotations

from .app import app
from . import run as _  # noqa: F401


def main() -> None:
    app()
