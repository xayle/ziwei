"""Load relation-type-registry.json — single source for dimension weights."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = ROOT / "docs" / "contracts" / "relation-type-registry.json"

RELATION_TYPES = (
    "couple",
    "friend",
    "parent_child",
    "colleague",
    "business_partner",
    "supervisor_subordinate",
)


@lru_cache(maxsize=1)
def load_registry() -> dict[str, Any]:
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return raw


def get_type_config(relation_type: str) -> dict[str, Any]:
    reg = load_registry()
    types = reg.get("types") or {}
    if relation_type not in types:
        raise ValueError(f"Unknown relation_type: {relation_type}")
    return types[relation_type]


def get_day_branch_rules() -> dict[str, Any]:
    return load_registry().get("day_branch_rules") or {}


def get_year_branch_same_score() -> int:
    correction = load_registry().get("year_branch_same_correction") or {}
    return int(correction.get("score", 18))
