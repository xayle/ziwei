"""Canonical JSON helper for deterministic chart/explain snapshots."""

from __future__ import annotations

import json
from typing import Any


def canonical_json(data: Any) -> str:
    """Serialize with stable key order for hashing and fixture diff."""
    return json.dumps(data, sort_keys=True, ensure_ascii=False, default=str, separators=(",", ":"))
