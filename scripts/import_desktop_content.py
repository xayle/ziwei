#!/usr/bin/env python3
"""
Import useful content from Desktop source folders into c2 data layer.

Sources (default paths on Windows):
  - 资料/学习文件/ziwei-main     → design docs (already synced); star_profiles JSON
  - 资料/文墨天机                → wenmo reference cases + narrative style samples
  - Desktop/紫薇                 → skipped (older c2 snapshot; c2 is canonical)

Outputs:
  - data/imported/wenmo_reference_cases.json
  - data/imported/narrative_style_samples.json
  - data/imported/source_manifest.json
  - data/ziwei/star_profiles.json
  - data/glossary.json (merged ziwei terms)

Usage:
  python scripts/import_desktop_content.py
  python scripts/import_desktop_content.py --desktop "D:/Users/Administrator/Desktop"
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
IMPORTED = DATA / "imported"
ZIWEI_DOCS = ROOT / "docs" / "design" / "ziwei"

WENMO_META: dict[str, dict[str, Any]] = {
    "华": {
        "id": "WM01",
        "name": "华倩",
        "gender": "female",
        "birth_year": 1993,
        "birth_month": 6,
        "birth_day": 29,
        "birth_hour": 15,
        "birth_minute": 15,
        "solar_corrected_hour": 15,
        "solar_corrected_minute": 20,
        "longitude": 122.117,
        "pillars": "癸酉 戊午 辛巳 丙申",
        "wuxing_ju": "水二局",
        "ming_zhu": "禄存",
        "shen_zhu": "天同",
        "life_palace_gz": "壬戌",
    },
    "黄": {
        "id": "WM02",
        "name": "黄振",
        "gender": "male",
        "birth_year": 1988,
        "birth_month": 6,
        "birth_day": 25,
        "birth_hour": 6,
        "birth_minute": 10,
        "solar_corrected_hour": 5,
        "solar_corrected_minute": 56,
        "longitude": 117.183,
        "pillars": "戊辰 戊午 辛亥 辛卯",
        "wuxing_ju": "水二局",
        "ming_zhu": "文曲",
        "shen_zhu": "文昌",
        "life_palace_gz": "乙卯",
        "body_palace_branch": "酉",
    },
    "路": {
        "id": "WM03",
        "name": "路琳清",
        "gender": "female",
        "birth_year": 1993,
        "birth_month": 3,
        "birth_day": 6,
        "birth_hour": 8,
        "birth_minute": 35,
        "solar_corrected_hour": 8,
        "solar_corrected_minute": 12,
        "longitude": 117.183,
        "pillars": "癸酉 乙卯 丙戌 壬辰",
        "wuxing_ju": "水二局",
        "ming_zhu": "巨门",
        "shen_zhu": "天同",
        "life_palace_gz": "癸亥",
    },
}

ZIWEI_GLOSSARY: list[dict[str, Any]] = [
    {
        "term": "紫微斗数",
        "pinyin": "zǐ wēi dòu shù",
        "definition": "以紫微星为首的星曜体系，依出生时辰安十二宫，论命运吉凶的命理学派。",
        "category": "紫微",
        "classic_source": "《紫微斗数全书》",
    },
    {
        "term": "命宫",
        "pinyin": "mìng gōng",
        "definition": "紫微命盘核心宫位，代表先天性格、人生方向与整体格局。",
        "category": "紫微",
        "classic_source": "《紫微斗数全书》",
    },
    {
        "term": "身宫",
        "pinyin": "shēn gōng",
        "definition": "与后天行为、实际际遇相关的宫位，与命宫并看以辨先天后天。",
        "category": "紫微",
        "classic_source": "《紫微斗数全书》",
    },
    {
        "term": "三方四正",
        "pinyin": "sān fāng sì zhèng",
        "definition": "以命宫（或任一宫位）为本宫，加对宫、三合宫共四个宫位，为紫微论命的基本观察框架。",
        "category": "紫微",
        "classic_source": "《紫微斗数全书》",
    },
    {
        "term": "四化",
        "pinyin": "sì huà",
        "definition": "化禄、化权、化科、化忌四种变化，由生年天干引发，影响星曜吉凶与事件倾向。",
        "category": "紫微",
        "classic_source": "《紫微斗数全书》",
    },
    {
        "term": "庙旺利陷",
        "pinyin": "miào wàng lì xiàn",
        "definition": "星曜在不同地支宫位的亮度等级：庙、旺、得、利、平、不、陷，影响星情发挥程度。",
        "category": "紫微",
        "classic_source": "《紫微斗数全书》",
    },
    {
        "term": "五行局",
        "pinyin": "wǔ xíng jú",
        "definition": "由命宫干支纳音确定的局数（水二、木三、金四、土五、火六），决定紫微星起局与大运节奏。",
        "category": "紫微",
        "classic_source": "《紫微斗数全书》",
    },
    {
        "term": "大限",
        "pinyin": "dà xiàn",
        "definition": "紫微十年一换的运势周期，依五行局与阴阳男女顺逆而定起运年龄与宫位。",
        "category": "紫微",
        "classic_source": "《紫微斗数全书》",
    },
    {
        "term": "命主",
        "pinyin": "mìng zhǔ",
        "definition": "依出生年支确定的星曜，代表先天灵魂主题。",
        "category": "紫微",
        "classic_source": "《紫微斗数全书》",
    },
    {
        "term": "身主",
        "pinyin": "shēn zhǔ",
        "definition": "依出生年支确定的星曜，代表后天行为趋向。",
        "category": "紫微",
        "classic_source": "《紫微斗数全书》",
    },
    {
        "term": "空宫",
        "pinyin": "kōng gōng",
        "definition": "宫位内无十四主星坐守，须借对宫与三方星曜会照来论该宫事项。",
        "category": "紫微",
        "classic_source": "《紫微斗数全书》",
    },
    {
        "term": "飞星",
        "pinyin": "fēi xīng",
        "definition": "四化星飞入他宫的变化关系，用于分析宫位之间的因果联动。",
        "category": "紫微",
        "classic_source": "《骨髓赋》",
    },
]


def _parse_star_cell(cell: Any) -> list[dict[str, Any]]:
    if not cell or str(cell).strip() in {"", "无"}:
        return []
    out: list[dict[str, Any]] = []
    for part in str(cell).split(","):
        part = part.strip()
        if not part or part == "无":
            continue
        m = re.match(r"^(.+?)\[(.+?)\](.*)$", part)
        if m:
            transforms = [t for t in re.findall(r"[↑↓]?[生年]?[禄权科忌]", m.group(3)) if t]
            out.append(
                {
                    "name": m.group(1),
                    "brightness": m.group(2),
                    "transforms": transforms or None,
                }
            )
        else:
            out.append({"name": part, "brightness": None, "transforms": None})
    return out


def _load_wenmo_xlsx(path: Path) -> list[dict[str, Any]]:
    try:
        import openpyxl
    except ImportError as e:
        raise SystemExit("openpyxl required: pip install openpyxl") from e

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    palaces: list[dict[str, Any]] = []
    for row in rows[2:14]:
        if not row or not row[0]:
            continue
        palaces.append(
            {
                "palace": row[0],
                "branch": row[1],
                "major": _parse_star_cell(row[2]),
                "minor": _parse_star_cell(row[3]),
                "misc": _parse_star_cell(row[4]) if len(row) > 4 else [],
                "dayun_range": row[9] if len(row) > 9 else None,
            }
        )
    return palaces


def build_wenmo_cases(wenmo_dir: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for key, meta in WENMO_META.items():
        xlsx = wenmo_dir / f"{key}.xlsx"
        if not xlsx.exists():
            print(f"  skip {meta['id']}: missing {xlsx}", file=sys.stderr)
            continue
        palaces = _load_wenmo_xlsx(xlsx)
        ming = next((p for p in palaces if p["palace"] == "命宫"), None)
        cases.append(
            {
                **meta,
                "source": "文墨天机",
                "source_file": str(xlsx),
                "trust_level": "advisory",
                "purpose": "wenmo_crosscheck",
                "palaces": palaces,
                "ming_palace_verified": ming is not None,
                "notes": "第三方排盘对照轨；不覆盖引擎 canonical 输出",
            }
        )
    return cases


def _extract_trait_line(block: str, label: str) -> list[str]:
    for line in block.splitlines():
        m = re.match(rf"^- \*\*{re.escape(label)}\*\*[：:](.+)$", line.strip())
        if m:
            return [x.strip() for x in re.split(r"[、,]", m.group(1)) if x.strip()]
    return []


def _extract_bullets(block: str, label: str) -> list[str]:
    items: list[str] = []
    in_section = False
    for line in block.splitlines():
        if f"**{label}**" in line and line.strip().startswith("-"):
            continue
        if label in line and "**" in line:
            in_section = True
            continue
        if in_section:
            if line.startswith("**") and label not in line:
                break
            if line.strip().startswith("- "):
                items.append(line.strip()[2:])
    return items


def _parse_star_profiles(md_path: Path, *, star_type: str) -> list[dict[str, Any]]:
    text = md_path.read_text(encoding="utf-8")
    profiles: list[dict[str, Any]] = []
    chunks = re.split(r"\n### \d+\. ", text)
    for chunk in chunks[1:]:
        header = chunk.split("\n", 1)[0]
        m = re.match(r"(.+?)星[（(](.+?)[）)]", header)
        if not m:
            continue
        name, alias = m.group(1), m.group(2)
        block = chunk

        def _table_field(field: str) -> str | None:
            pat = rf"\| {re.escape(field)} \| (.+?) \|"
            hit = re.search(pat, block)
            return hit.group(1).strip() if hit else None

        brightness_affected = "受影响" in block and "❌" not in block.split("受亮度影响")[1][:20] if "受亮度影响" in block else None

        profiles.append(
            {
                "key": name,
                "name": f"{name}星",
                "alias": alias,
                "type": star_type,
                "five_elements": _table_field("五行"),
                "dou_series": _table_field("斗系"),
                "huaqi": _table_field("化气"),
                "representative": _table_field("代表人物"),
                "pros": _extract_trait_line(block, "优点"),
                "cons": _extract_trait_line(block, "缺点"),
                "key_points": _extract_bullets(block, "关键特点"),
                "brightness_sensitive": brightness_affected,
                "source": str(md_path.relative_to(ROOT)),
                "trust_level": "reference",
            }
        )
    return profiles


def build_star_profiles() -> dict[str, Any]:
    files = [
        (ZIWEI_DOCS / "02-星曜体系" / "01-十四主星.md", "major"),
        (ZIWEI_DOCS / "02-星曜体系" / "02-六吉星.md", "lucky"),
        (ZIWEI_DOCS / "02-星曜体系" / "03-六煞星.md", "bad"),
    ]
    stars: list[dict[str, Any]] = []
    for path, star_type in files:
        if path.exists():
            stars.extend(_parse_star_profiles(path, star_type=star_type))
    return {
        "_meta": {
            "version": "1.0",
            "generated": datetime.now(timezone.utc).isoformat(),
            "generator": "scripts/import_desktop_content.py",
            "trust_level": "reference",
            "note": "Explain-layer star profiles; not verified classic citations",
        },
        "stars": stars,
    }


def build_narrative_samples(wenmo_dir: Path) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []

    hepan = wenmo_dir / "合盘.docx"
    if hepan.exists() and hepan.stat().st_size > 0:
        try:
            from markitdown import MarkItDown

            md = MarkItDown().convert(str(hepan)).text_content
            if md:
                excerpt = md[:1200].strip()
                samples.append(
                    {
                        "id": "NARR-HEPAN-001",
                        "title": "合盘分析结构样例（黄×路）",
                        "source": "文墨天机/合盘.docx",
                        "domain": "ziwei_compat",
                        "trust_level": "experience_inference",
                        "ui_label": "经验推断",
                        "excerpt": excerpt,
                        "tags": ["合盘", "夫妻", "子女", "大限"],
                    }
                )
        except Exception as exc:
            print(f"  warn: hepan convert failed: {exc}", file=sys.stderr)

    ziwei_section = (
        "此盘最大的特点，是**命宫府相朝垣，福德贪狼化忌**的巨大反差。"
        "你有一个高贵的「壳」，但里面住着一个「骚动不安的灵魂」。"
        "官禄宫武曲天相，是典型的「财荫夹印」格，在大型金融机构或公家单位做财务管理，是正途。"
    )
    samples.append(
        {
            "id": "NARR-ZW-001",
            "title": "紫微段落叙事样例（华倩盘）",
            "source": "文墨天机/华.docx",
            "domain": "ziwei_palace",
            "trust_level": "experience_inference",
            "ui_label": "经验推断",
            "excerpt": ziwei_section,
            "tags": ["命宫", "福德", "官禄", "财帛"],
        }
    )
    return samples


def merge_glossary() -> list[dict[str, Any]]:
    path = DATA / "glossary.json"
    existing = json.loads(path.read_text(encoding="utf-8"))
    by_term = {item["term"]: item for item in existing}
    added = 0
    for item in ZIWEI_GLOSSARY:
        if item["term"] not in by_term:
            by_term[item["term"]] = item
            added += 1
    merged = list(by_term.values())
    path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  glossary: +{added} ziwei terms (total {len(merged)})")
    return merged


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  wrote {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")


def build_manifest(desktop: Path, outputs: dict[str, str]) -> dict[str, Any]:
    return {
        "version": "1.0",
        "generated": datetime.now(timezone.utc).isoformat(),
        "desktop_root": str(desktop),
        "sources": {
            "资料": {
                "path": str(desktop / "资料"),
                "integrated": [
                    "学习文件/ziwei-main → docs/design/ziwei (pre-synced, MD5 verified)",
                    "学习文件/1 (iztro) → brightness cross-check via scripts/iztro",
                    "iztro-main, ziwei-main repos → algorithm reference only (not copied)",
                ],
                "skipped": [
                    "DAO_DE_JING-main — general classics; use import_github_classics.py instead",
                    "FortuneTelling/xuanxue* — out of MVP scope",
                    "奇门遁甲 — out of MVP scope",
                ],
            },
            "文墨天机": {
                "path": str(desktop / "文墨天机"),
                "integrated": [
                    "华/黄/路.xlsx → data/imported/wenmo_reference_cases.json",
                    "合盘.docx + 华.docx excerpts → narrative_style_samples.json",
                ],
                "skipped": [
                    "App.swf / .exe / assets — runtime binaries, not content",
                    "刘.docx — empty file",
                ],
            },
            "紫薇": {
                "path": str(desktop / "紫薇"),
                "integrated": [],
                "skipped": ["Older c2 snapshot; c2 repo is canonical"],
            },
        },
        "outputs": outputs,
        "policy": {
            "verified_classics": "classics.json + ziwei_classic_refs",
            "reference_profiles": "data/ziwei/star_profiles.json",
            "advisory_crosscheck": "wenmo_reference_cases.json (trust_level=advisory)",
            "experience_narrative": "narrative_style_samples.json (ui_label=经验推断)",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Desktop source content into c2")
    parser.add_argument(
        "--desktop",
        default=str(Path.home() / "Desktop"),
        help="Desktop root containing 资料/文墨天机/紫薇",
    )
    args = parser.parse_args()
    desktop = Path(args.desktop)

    wenmo_dir = desktop / "文墨天机"
    if not wenmo_dir.exists():
        # fallback: 资料 may be sibling
        alt = desktop / "资料" / "文墨天机"
        wenmo_dir = alt if alt.exists() else wenmo_dir

    print("Importing Desktop content...")
    outputs: dict[str, str] = {}

    cases = build_wenmo_cases(wenmo_dir)
    wenmo_path = IMPORTED / "wenmo_reference_cases.json"
    write_json(wenmo_path, {"_meta": {"count": len(cases)}, "cases": cases})
    outputs["wenmo_reference_cases"] = str(wenmo_path.relative_to(ROOT))

    profiles = build_star_profiles()
    profiles_path = DATA / "ziwei" / "star_profiles.json"
    write_json(profiles_path, profiles)
    outputs["star_profiles"] = str(profiles_path.relative_to(ROOT))

    narratives = build_narrative_samples(wenmo_dir)
    narr_path = IMPORTED / "narrative_style_samples.json"
    write_json(narr_path, {"_meta": {"count": len(narratives)}, "samples": narratives})
    outputs["narrative_style_samples"] = str(narr_path.relative_to(ROOT))

    merge_glossary()
    outputs["glossary"] = "data/glossary.json"

    manifest_path = IMPORTED / "source_manifest.json"
    write_json(manifest_path, build_manifest(desktop, outputs))

    print(f"Done: {len(cases)} wenmo cases, {len(profiles['stars'])} star profiles, {len(narratives)} narrative samples")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
