"""GTM entitlement models (BE-GTM-05 / T086)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.life_volume import LifeVolumeId

EntitlementTier = Literal["free", "volume_pass", "full_book"]

# Q2 / T087：卷 0–1 免费，2–4 需 pass，5–6 需 full_book；跋默认可见（信任层）
VOLUME_MIN_ENTITLEMENT: dict[LifeVolumeId, EntitlementTier] = {
    "preface": "free",
    "vol1": "free",
    "vol2": "volume_pass",
    "vol3": "volume_pass",
    "vol4": "volume_pass",
    "vol5": "full_book",
    "vol6": "full_book",
    "colophon": "free",
}


class EntitlementInfo(BaseModel):
    """当前用户卷目权益（auth/me 与中间件共用）。"""

    tier: EntitlementTier = "free"
    unlocked_volume_ids: list[LifeVolumeId] = Field(default_factory=list)
    schema_version: Literal["entitlement@1.0"] = "entitlement@1.0"
