"""Dependencies package - shared dependency injection."""
from __future__ import annotations

from .auth import (
    get_current_user,
    require_user,
    CurrentUser,
    RequiredUser,
)

__all__ = [
    "get_current_user",
    "require_user",
    "CurrentUser",
    "RequiredUser",
]
