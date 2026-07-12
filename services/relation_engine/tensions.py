"""Detect cross-module tensions for Trust layer."""

from __future__ import annotations

from typing import Any


def detect_tensions(
    bazi_a: dict[str, Any] | None,
    bazi_b: dict[str, Any] | None,
) -> list[dict[str, str]]:
    tensions: list[dict[str, str]] = []
    for side, payload in (("a", bazi_a), ("b", bazi_b)):
        if not payload:
            continue
        raw = payload if isinstance(payload, dict) else {}
        wealth_hint = (raw.get("dayun") or {}).get("wealth_hint") or raw.get("wealth_hint")
        wealth_analysis = raw.get("wealth_analysis") or {}
        trend = wealth_analysis.get("trend") if isinstance(wealth_analysis, dict) else None
        if wealth_hint and trend and _opposite_trend(str(wealth_hint), str(trend)):
            tensions.append(
                {
                    "code": f"wealth_hint_vs_analysis_{side}",
                    "message": f"甲方大运财提示与财业分析趋势不一致（{side}）"
                    if side == "a"
                    else f"乙方大运财提示与财业分析趋势不一致（{side}）",
                }
            )
        strength = raw.get("strength_tier") or (raw.get("day_master_strength") or {}).get("tier")
        geju = raw.get("geju") or raw.get("pattern") or ""
        if strength and geju and _strength_geju_conflict(str(strength), str(geju)):
            tensions.append(
                {
                    "code": f"strength_geju_{side}",
                    "message": f"日主强弱标注与格局文案存在张力（{side}）",
                }
            )
    return tensions


def _opposite_trend(hint: str, trend: str) -> bool:
    up_words = ("升", "旺", "增", "好", "顺")
    down_words = ("降", "弱", "减", "差", "阻")
    hint_up = any(w in hint for w in up_words)
    hint_down = any(w in hint for w in down_words)
    trend_up = any(w in trend for w in up_words)
    trend_down = any(w in trend for w in down_words)
    return (hint_up and trend_down) or (hint_down and trend_up)


def _strength_geju_conflict(strength: str, geju: str) -> bool:
    if "极弱" in strength and "身强" in geju:
        return True
    if "极强" in strength and "身弱" in geju:
        return True
    return False
