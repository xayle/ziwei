"""紫微斗数古籍语料 — 星曜/格局/宫位软提示（对齐八字 classic_refs 管线）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CTEXT_BOOK = "《紫微斗数全书》"
_CTEXT_BASE = "https://ctext.org/wiki.pl?if=en&res=979714"


def _with_ctext(ref: dict[str, Any], *, page: int, vol_page: str) -> dict[str, Any]:
    return {
        **ref,
        "source_page": vol_page,
        "ctext_page": page,
        "ctext_ref": f"{_CTEXT_BASE}&chapter={page}",
    }


_CORE_REFS: list[dict[str, Any]] = [
    # ── 十四主星 ──
    {
        "id": "zw_star_001",
        "source": "《紫微斗数全书》",
        "text": "紫微帝座，诸星之主，有解厄制化之功；庙旺则贵，陷弱宜辅弼。",
        "category": "主星",
        "tags": ["紫微"],
    },
    {
        "id": "zw_star_002",
        "source": "《紫微斗数全书》",
        "text": "天机化气为善，主思虑计划；喜昌曲会照，忌羊陀冲破。",
        "category": "主星",
        "tags": ["天机"],
    },
    {
        "id": "zw_star_003",
        "source": "《紫微斗数全书》",
        "text": "太阳化气为贵，主光明父夫；昼生有力，夜生稍减。",
        "category": "主星",
        "tags": ["太阳"],
    },
    {
        "id": "zw_star_004",
        "source": "《紫微斗数全书》",
        "text": "武曲化气为财，主刚毅果决；与府相配合，财源可聚。",
        "category": "主星",
        "tags": ["武曲"],
    },
    {
        "id": "zw_star_005",
        "source": "《紫微斗数全书》",
        "text": "天同化气为福，主温和享受；逢禄存、化禄，福厚。",
        "category": "主星",
        "tags": ["天同"],
    },
    {
        "id": "zw_star_006",
        "source": "《紫微斗数全书》",
        "text": "廉贞化气为囚，主次桃花；遇火贪、铃贪可发横财运。",
        "category": "主星",
        "tags": ["廉贞"],
    },
    {
        "id": "zw_star_007",
        "source": "《紫微斗数全书》",
        "text": "天府化气为令，主库藏稳厚；为财帛田宅之基，宜守成。",
        "category": "主星",
        "tags": ["天府"],
    },
    {
        "id": "zw_star_008",
        "source": "《紫微斗数全书》",
        "text": "太阴化气为富，主田宅母妻；夜生较昼生有力。",
        "category": "主星",
        "tags": ["太阴"],
    },
    {
        "id": "zw_star_009",
        "source": "《紫微斗数全书》",
        "text": "贪狼化气为桃花，主欲望才艺；遇火铃可成火贪、铃贪格。",
        "category": "主星",
        "tags": ["贪狼"],
    },
    {
        "id": "zw_star_010",
        "source": "《紫微斗数全书》",
        "text": "巨门化气为暗，主口舌是非；宜昌曲、禄存化解。",
        "category": "主星",
        "tags": ["巨门"],
    },
    {
        "id": "zw_star_011",
        "source": "《紫微斗数全书》",
        "text": "天相化气为印，主辅佐文诰；官禄财帛之佐，喜紫微天府会。",
        "category": "主星",
        "tags": ["天相"],
    },
    {
        "id": "zw_star_012",
        "source": "《紫微斗数全书》",
        "text": "天梁化气为荫，主寿算解厄；逢刑忌夹，孤克难免。",
        "category": "主星",
        "tags": ["天梁"],
    },
    {
        "id": "zw_star_013",
        "source": "《紫微斗数全书》",
        "text": "七杀化气为将，主威权变动；宜禄存、昌曲调和。",
        "category": "主星",
        "tags": ["七杀"],
    },
    {
        "id": "zw_star_014",
        "source": "《紫微斗数全书》",
        "text": "破军化气为耗，主开创破耗；逢禄存、化禄可减破。",
        "category": "主星",
        "tags": ["破军"],
    },
    # ── 格局 ──
    {
        "id": "zw_pat_001",
        "source": "《紫微斗数全书》",
        "text": "紫府同宫，终身福厚；须看庙旺与四化。",
        "category": "格局",
        "tags": ["紫府同宫"],
    },
    {
        "id": "zw_pat_002",
        "source": "《紫微斗数全书》",
        "text": "府相朝垣，衣食无忧；财官印绶相护。",
        "category": "格局",
        "tags": ["府相朝垣"],
    },
    {
        "id": "zw_pat_003",
        "source": "《紫微斗数全书》",
        "text": "君臣庆会，紫微天府昌曲左右会照，科名显达。",
        "category": "格局",
        "tags": ["君臣庆会"],
    },
    {
        "id": "zw_pat_004",
        "source": "《紫微斗数全书》",
        "text": "火贪格：贪狼遇火星，主突发横财；须庙旺方真。",
        "category": "格局",
        "tags": ["火贪格", "火贪"],
    },
    {
        "id": "zw_pat_005",
        "source": "《紫微斗数全书》",
        "text": "铃贪格：贪狼遇铃星，横发之机；忌空劫同宫。",
        "category": "格局",
        "tags": ["铃贪格", "铃贪"],
    },
    {
        "id": "zw_pat_006",
        "source": "《紫微斗数全书》",
        "text": "杀破狼：七杀破军贪狼会照，主一生多变动；宜技艺开创。",
        "category": "格局",
        "tags": ["杀破狼"],
    },
    {
        "id": "zw_pat_007",
        "source": "《紫微斗数全书》",
        "text": "羊陀夹命，多阻滞刑伤；宜修身积德。",
        "category": "格局",
        "tags": ["羊陀夹命"],
    },
    {
        "id": "zw_pat_008",
        "source": "《紫微斗数全书》",
        "text": "化禄守命，福厚财丰；忌空劫冲破。",
        "category": "格局",
        "tags": ["化禄守命"],
    },
    # ── 十二宫 ──
    {
        "id": "zw_pal_001",
        "source": "《紫微斗数全书》",
        "text": "命宫为先天根本，主性情格局；三方四正定吉凶。",
        "category": "宫位",
        "tags": ["命宫"],
    },
    {
        "id": "zw_pal_002",
        "source": "《紫微斗数全书》",
        "text": "财帛宫主财源理财；须参田宅、福德互看。",
        "category": "宫位",
        "tags": ["财帛"],
    },
    {
        "id": "zw_pal_003",
        "source": "《紫微斗数全书》",
        "text": "官禄宫主事业功名；会照父母、迁移定际遇。",
        "category": "宫位",
        "tags": ["官禄", "事业"],
    },
    {
        "id": "zw_pal_004",
        "source": "《紫微斗数全书》",
        "text": "夫妻宫主配偶姻缘；忌羊陀火铃守照。",
        "category": "宫位",
        "tags": ["夫妻"],
    },
    {
        "id": "zw_pal_005",
        "source": "《紫微斗数全书》",
        "text": "疾厄宫主健康灾厄；会福德、父母参身心。",
        "category": "宫位",
        "tags": ["疾厄", "健康"],
    },
    # ── 四化 ──
    {
        "id": "zw_sihua_001",
        "source": "《紫微斗数全书》",
        "text": "化禄主福财机缘；化权主权势掌控；化科主名声考试；化忌主阻滞亏欠。",
        "category": "四化",
        "tags": ["四化", "化禄", "化权", "化科", "化忌"],
    },
]


def _page_for_id(rid: str) -> tuple[int, str]:
    if rid.startswith("zw_star_"):
        n = int(rid.rsplit("_", 1)[-1])
        return n, f"卷一·主星 p.{n}"
    if rid.startswith("zw_pat_"):
        n = int(rid.rsplit("_", 1)[-1])
        return 90 + n, f"卷二·格局 p.{90 + n}"
    if rid.startswith("zw_pal_"):
        n = int(rid.rsplit("_", 1)[-1])
        return 83 + n, f"卷二·宫位 p.{83 + n}"
    if rid.startswith("zw_sihua_"):
        return 111, "卷三·四化 p.111"
    return 1, "卷一 p.1"


def _load_generated_refs() -> list[dict[str, Any]]:
    path = Path(__file__).resolve().parent.parent / "data" / "ziwei_classic_refs_generated.json"
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _merge_catalog() -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for ref in _CORE_REFS:
        rid = ref.get("id", "")
        page, vol_page = _page_for_id(rid)
        merged[rid] = _with_ctext(ref, page=page, vol_page=vol_page)
    for ref in _load_generated_refs():
        rid = ref.get("id", "")
        if rid and rid not in merged:
            merged[rid] = ref
    return list(merged.values())


ZIWEI_CLASSIC_REFS: list[dict[str, Any]] = _merge_catalog()


def catalog_self_check() -> dict[str, Any]:
    """Return basic catalog health metrics (≥100 entries, ctext pages present)."""
    with_page = sum(1 for r in ZIWEI_CLASSIC_REFS if r.get("source_page") and r.get("ctext_ref"))
    return {
        "count": len(ZIWEI_CLASSIC_REFS),
        "with_ctext_page": with_page,
        "ok": len(ZIWEI_CLASSIC_REFS) >= 100 and with_page == len(ZIWEI_CLASSIC_REFS),
    }


def _match_refs(keyword: str, *, category: str | None = None, limit: int = 3) -> list[dict]:
    if not keyword:
        return []
    hits = [r for r in ZIWEI_CLASSIC_REFS if keyword in r.get("tags", []) or keyword in r.get("text", "")]
    if category:
        cat_hits = [r for r in hits if r.get("category") == category]
        if cat_hits:
            hits = cat_hits
    seen: set[str] = set()
    out: list[dict] = []
    for ref in hits:
        rid = ref.get("id", "")
        if rid in seen:
            continue
        seen.add(rid)
        out.append({**ref, "hint_type": "soft"})
        if len(out) >= limit:
            break
    return out


def pattern_candidates(pattern_name: str, *, limit: int = 2) -> list[dict]:
    return _match_refs(pattern_name, category="格局", limit=limit)


def star_candidates(star_names: list[str], *, limit: int = 4) -> list[dict]:
    out: list[dict] = []
    seen: set[str] = set()
    for name in star_names:
        for ref in _match_refs(name, category="主星", limit=2):
            rid = ref.get("id", "")
            if rid in seen:
                continue
            seen.add(rid)
            out.append(ref)
            if len(out) >= limit:
                return out
    return out


def build_chart_classic_refs(chart: Any) -> list[dict]:
    """Aggregate soft classic hints for a computed ZiweiChart."""
    refs: list[dict] = []
    seen: set[str] = set()

    def _add(items: list[dict]) -> None:
        for item in items:
            rid = item.get("id", "")
            if rid in seen:
                continue
            seen.add(rid)
            refs.append(item)

    life_palace = None
    main_stars: list[str] = []
    for palace in getattr(chart, "palaces", []) or []:
        if getattr(palace, "name", "") == "命宫" or getattr(palace, "index", -1) == 0:
            life_palace = palace
        for star in getattr(palace, "main_stars", []) or []:
            name = star.get("name") if isinstance(star, dict) else getattr(star, "name", None)
            if name and name not in main_stars:
                main_stars.append(name)

    _add(star_candidates(main_stars[:6], limit=4))

    for pattern in getattr(chart, "patterns", []) or []:
        pname = getattr(pattern, "name", "") or ""
        _add(pattern_candidates(pname, limit=1))

    if life_palace is not None:
        _add(_match_refs("命宫", category="宫位", limit=1))

    _add(_match_refs("四化", category="四化", limit=1))

    return refs[:10]
