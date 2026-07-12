"""Canonical JSON tests."""

from __future__ import annotations

from tests.utils.canonical_json import canonical_json


def test_canonical_json_stable_keys():
    a = canonical_json({"b": 1, "a": 2})
    b = canonical_json({"a": 2, "b": 1})
    assert a == b
