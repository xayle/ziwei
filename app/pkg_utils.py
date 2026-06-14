"""Lightweight package-availability utilities.

Kept in a standalone module so both ``app.bootstrap`` and ``routers.verify``
can import it without creating a circular dependency.
"""

from __future__ import annotations

import importlib.metadata
import importlib.util


def backend_status(name: str) -> tuple[bool, str]:
    """Return (available, version) for an installed Python package *name*."""
    spec = importlib.util.find_spec(name)
    available = spec is not None
    version = "unavailable"
    if available:
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"
    return available, version
