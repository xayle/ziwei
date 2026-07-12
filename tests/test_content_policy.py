"""Tests for content_policy."""

from __future__ import annotations

import pytest

from services.content_policy import (
    ContentPolicyError,
    assert_cite_allowed,
    is_verified_classic,
    sanitize_explain_block,
)


def test_assert_cite_rejects_unverified():
    with pytest.raises(ContentPolicyError):
        assert_cite_allowed(layer="cite", classic_id="yuanhai.kanming.foundation")


def test_sanitize_downgrades_unverified_cite():
    block = sanitize_explain_block(
        {"text": "x", "layer": "cite", "classic_id": "yuanhai.kanming.foundation"},
    )
    assert block["layer"] == "inference"
    assert block.get("classic_id") is None


def test_verified_classic_exists():
    assert is_verified_classic("verified") is False
    # At least one verified id should exist in corpus
    from pathlib import Path
    import json

    raw = json.loads((Path(__file__).resolve().parents[1] / "data" / "classics.json").read_text(encoding="utf-8"))
    verified = [x["id"] for x in raw if x.get("verification_status") == "verified"]
    assert len(verified) >= 20
    assert is_verified_classic(verified[0])
