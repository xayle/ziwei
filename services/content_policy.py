"""Content policy: only verified classics may appear as cite-layer citations."""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLASSICS_PATH = ROOT / "data" / "classics.json"

DEFAULT_DISCLAIMER_TEXT = "本辑录仅供文化研究与自我认知参考，不构成医疗、法律或投资建议。"
DEFAULT_DISCLAIMER_VERSION = "2026-07-12"


class ContentPolicyError(ValueError):
    """Raised when a block violates citation policy."""


@lru_cache(maxsize=1)
def _verified_ids() -> frozenset[str]:
    if not CLASSICS_PATH.exists():
        return frozenset()
    raw = json.loads(CLASSICS_PATH.read_text(encoding="utf-8"))
    return frozenset(
        item["id"] for item in raw if isinstance(item, dict) and item.get("verification_status") == "verified"
    )


def is_verified_classic(classic_id: str | None) -> bool:
    if not classic_id or not classic_id.strip():
        return False
    return classic_id.strip() in _verified_ids()


def assert_cite_allowed(*, layer: str, classic_id: str | None) -> None:
    if layer != "cite":
        return
    if not classic_id:
        raise ContentPolicyError("cite layer requires classic_id")
    if not is_verified_classic(classic_id):
        raise ContentPolicyError(f"classic_id not verified: {classic_id}")


def sanitize_explain_block(block: dict) -> dict:
    """Drop or downgrade blocks that violate cite policy."""
    layer = block.get("layer", "fact")
    classic_id = block.get("classic_id")
    if layer == "cite" and classic_id and not is_verified_classic(classic_id):
        return {**block, "layer": "inference", "classic_id": None}
    if layer == "cite" and not classic_id:
        return {**block, "layer": "inference"}
    return block


def default_disclaimer_block() -> dict:
    return {
        "text": DEFAULT_DISCLAIMER_TEXT,
        "version": DEFAULT_DISCLAIMER_VERSION,
        "jurisdiction": "CN",
    }


def content_versions_meta() -> dict:
    versions: dict[str, str] = {}
    if CLASSICS_PATH.exists():
        versions["classics"] = "classics.json"
    glossary = ROOT / "data" / "glossary.json"
    if glossary.exists():
        versions["glossary"] = "glossary.json"
    star_profiles = ROOT / "data" / "ziwei" / "star_profiles.json"
    if star_profiles.exists():
        versions["star_profiles"] = "star_profiles.json"
    wenmo_cases = ROOT / "data" / "imported" / "wenmo_reference_cases.json"
    if wenmo_cases.exists():
        versions["wenmo_reference_cases"] = "wenmo_reference_cases.json"
    narratives = ROOT / "data" / "imported" / "narrative_samples.json"
    if narratives.exists():
        versions["narrative_samples"] = "narrative_samples.json"
    versions["disclaimer"] = DEFAULT_DISCLAIMER_VERSION
    return versions


WENMO_ADVISORY_TEXT = "文墨天机为对照轨，仅用于交叉核对；不参与主盘排盘与典籍引用层。"


def default_wenmo_advisory() -> str:
    return WENMO_ADVISORY_TEXT
