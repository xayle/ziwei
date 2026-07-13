"""Build life-snippets@0.1 hooks for Douyin / GTM (T076 · BOOK-GTM §5.3).

P3-02：优先 fact/engine 句；典籍句可选一条。不返回长 inference。
"""

from __future__ import annotations

from typing import Any

from app.models import Case
from app.schemas import BaziFullRequest
from app.schemas.life_snippets import LifeSnippetHookModel, LifeSnippetsResponseModel
from app.schemas.life_volume import LIFE_VOLUME_LABELS
from services.chart_snapshot_service import build_bazi_snapshot
from services.content_policy import default_disclaimer_block

_HOOK_TEXT_LIMIT = 80
_DEFAULT_DISCLAIMER = "传统文化与自我认知参考，非命运断言。"


def _clip(text: str, limit: int = _HOOK_TEXT_LIMIT) -> str:
    t = " ".join((text or "").strip().split())
    if len(t) <= limit:
        return t
    return f"{t[: limit - 1]}…"


def _pillar_day(bazi: dict[str, Any]) -> tuple[str, str]:
    day = (bazi.get("pillars_primary") or {}).get("day") or {}
    if isinstance(day, dict):
        return str(day.get("stem") or ""), str(day.get("branch") or "")
    return "", ""


def _wx(elements: list[str] | None) -> str:
    mapping = {"wood": "木", "fire": "火", "earth": "土", "metal": "金", "water": "水"}
    return "、".join(mapping.get(e, e) for e in (elements or [])[:3]) or "—"


def build_hooks_from_bazi(bazi: dict[str, Any], *, limit: int = 5) -> list[LifeSnippetHookModel]:
    """Extract 3–5 short hooks; prefer engine facts + at most one classical."""
    limit = max(3, min(5, int(limit)))
    hooks: list[LifeSnippetHookModel] = []

    stem, branch = _pillar_day(bazi)
    geju = bazi.get("geju") or {}
    geju_name = geju.get("engine_geju") or geju.get("geju_name") or "待分析"
    if stem or branch or geju_name:
        hooks.append(
            LifeSnippetHookModel(
                tag="事实",
                text=_clip(f"日主{stem}{branch}，{geju_name}。"),
                layer="engine",
            )
        )

    classic = (geju.get("classic_ref") or "").strip()
    if classic:
        hooks.append(
            LifeSnippetHookModel(
                tag="典籍",
                text=_clip(classic),
                layer="classical",
            )
        )

    yong = bazi.get("yongshen") or {}
    favor = _wx(yong.get("favor") if isinstance(yong, dict) else None)
    if favor != "—":
        hooks.append(
            LifeSnippetHookModel(
                tag="事实",
                text=_clip(f"用神倾向：{favor}。"),
                layer="engine",
            )
        )

    liunian = bazi.get("liunian") or {}
    items = liunian.get("items") if isinstance(liunian, dict) else None
    if items:
        item = items[0] if isinstance(items[0], dict) else {}
        year = item.get("year")
        stem_y = item.get("stem") or ""
        branch_y = item.get("branch") or ""
        ten_god = item.get("ten_god") or ""
        if year and (stem_y or branch_y):
            suffix = f"，十神{ten_god}" if ten_god else ""
            hooks.append(
                LifeSnippetHookModel(
                    tag="推算",
                    text=_clip(f"{year} {stem_y}{branch_y}流年{suffix}。"),
                    layer="engine",
                )
            )

    strength = (bazi.get("day_master_strength") or {}).get("tier")
    if strength and len(hooks) < limit:
        hooks.append(
            LifeSnippetHookModel(
                tag="事实",
                text=_clip(f"日主强弱：{strength}。"),
                layer="engine",
            )
        )

    # Deduplicate by text; pad with relation highlight if short
    seen: set[str] = set()
    unique: list[LifeSnippetHookModel] = []
    for h in hooks:
        if h.text in seen:
            continue
        seen.add(h.text)
        unique.append(h)
        if len(unique) >= limit:
            break

    if len(unique) < 3:
        rs = bazi.get("relations_summary") or {}
        items_r = rs.get("items") or []
        for item in items_r:
            if len(unique) >= 3:
                break
            label = ""
            if isinstance(item, dict):
                label = str(item.get("label") or item.get("type") or "")
            if not label or label in seen:
                continue
            seen.add(label)
            unique.append(LifeSnippetHookModel(tag="事实", text=_clip(label), layer="engine"))

    while len(unique) < 3:
        unique.append(
            LifeSnippetHookModel(
                tag="事实",
                text="命盘事实已就绪，展开六卷可读细节。",
                layer="engine",
            )
        )
        if len(unique) >= 3:
            break

    return unique[:limit]


def build_life_snippets_for_case(
    case: Case,
    *,
    limit: int = 5,
    request_id: str | None = None,
) -> LifeSnippetsResponseModel:
    from routers.bazi import _normalize_birth_dt_text

    dt = _normalize_birth_dt_text(case.birth_dt_local, case.tz or "Asia/Shanghai")
    bazi_req = BaziFullRequest(
        dt=dt,
        lon=float(case.lon),
        tz=case.tz or "Asia/Shanghai",
        gender=case.gender or "male",
        solar_time_enabled=bool(case.solar_time_enabled),
    )
    snapshot = build_bazi_snapshot(bazi_req, request_id=request_id or f"life-snippets-{case.id}")
    bazi = snapshot.response.model_dump(mode="json")
    hooks = build_hooks_from_bazi(bazi, limit=limit)

    disclaimer_block = default_disclaimer_block()
    disclaimer = _clip(str(disclaimer_block.get("text") or _DEFAULT_DISCLAIMER), 60)
    if "命运断言" not in disclaimer and "参考" not in disclaimer:
        disclaimer = _DEFAULT_DISCLAIMER

    # 有流年钩子 → 运之波；有典籍 → 命之根；默认运之波（竖版试投常用）
    has_liunian = any(h.tag == "推算" for h in hooks)
    has_classic = any(h.layer == "classical" for h in hooks)
    if has_liunian:
        vertical_title = LIFE_VOLUME_LABELS["vol3"]
    elif has_classic:
        vertical_title = LIFE_VOLUME_LABELS["vol1"]
    else:
        vertical_title = LIFE_VOLUME_LABELS["vol3"]

    return LifeSnippetsResponseModel(
        case_id=case.id,
        hooks=hooks,
        vertical_title=vertical_title,
        disclaimer=disclaimer or _DEFAULT_DISCLAIMER,
    )
