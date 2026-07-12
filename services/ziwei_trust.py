"""Ziwei trust_level computation (Q10: degraded returns 200, not 403)."""

from __future__ import annotations

from typing import Literal

from app.schemas.ziwei import IztroCrosscheckResponse, ZiweiResponse

TrustLevel = Literal["full", "degraded", "reference", "advisory", "verified"]


def compute_ziwei_trust_level(
    *,
    missing_fields: list[str] | None,
    engine_warnings: list[str] | None,
    iztro_crosscheck: IztroCrosscheckResponse | None,
) -> TrustLevel:
    missing = list(missing_fields or [])
    warnings = list(engine_warnings or [])
    if iztro_crosscheck is not None and not iztro_crosscheck.life_palace_match:
        return "degraded"
    if any("右弼" in w for w in warnings):
        return "advisory"
    if any(f in ("palace_ten_gods", "youbi_month_vs_iztro_hour") or "宫干" in f or "十神" in f for f in missing):
        return "advisory"
    if missing:
        return "degraded"
    return "full"


def apply_trust_level(response: ZiweiResponse) -> ZiweiResponse:
    level = compute_ziwei_trust_level(
        missing_fields=response.missing_fields,
        engine_warnings=response.engine_warnings,
        iztro_crosscheck=response.iztro_crosscheck,
    )
    return response.model_copy(update={"trust_level": level})
