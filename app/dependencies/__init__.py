"""Dependencies package - shared dependency injection."""

from __future__ import annotations

from .auth import (
    CurrentUser,
    RequiredUser,
    get_current_user,
    require_user,
)

__all__ = [
    "CurrentUser",
    "RequiredUser",
    "get_current_user",
    "require_user",
]
