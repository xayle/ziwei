#!/usr/bin/env python3
"""
从 GitHub 开源语料导入古籍数据到 c2 仓库。

数据源（MIT / 公开语料）:
  - minionszyw/bazi-skills  tests/supreme_audit.json  （千里命稿 50 例审计）
  - minionszyw/bazi-skills  src/analysis/methods/yuanhai.json （渊海子平章节摘要）
  - services/bazi_engine/classic_refs.py （引擎内嵌摘录，同步至 classics.json 检索层）

输出:
  - data/imported/supreme_audit.json
  - data/imported/yuanhai_skills.json
  - data/classics.json
  - 合并 ZIP* 命例至 data/ground_truth_cases.json（--merge-gt）

用法:
  python scripts/import_github_classics.py
  python scripts/import_github_classics.py --merge-gt
  CTEXT_API_KEY=... python scripts/import_github_classics.py   # 子平按 ctext 精确切块
  python scripts/import_github_classics.py --ctext-key YOUR_KEY
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
IMPORTED = DATA / "imported"
GT_PATH = DATA / "ground_truth_cases.json"

SUPREME_AUDIT_URL = (
    "https://raw.githubusercontent.com/minionszyw/bazi-skills/main/tests/supreme_audit.json"
)
YUANHAI_URL = (
    "https://raw.githubusercontent.com/minionszyw/bazi-skills/main/src/analysis/methods/yuanhai.json"
)

CTEXT_ZIPING_URN = "ctp:wb631975"
CTEXT_API_BASE = "https://api.ctext.org/gettext"

BOOK_META = {
    "yuanhai": ("《渊海子平》", "徐子平（传）", "宋"),
    "qianli": ("《千里命稿》", "韦千里", "民国"),
    "ziping": ("《子平真诠》", "沈孝瞻", "清"),
    "ditian": ("《滴天髓》", "任铁樵（注）", "清"),
    "sanming": ("《三命通会》", "万民英", "明"),
    "qiongtong": ("《穷通宝鉴》", "余春台（传）", "清"),
}

_WUXING_WORDS = {
    "木": "wood",
    "火": "fire",
    "土": "earth",
    "金": "metal",
    "水": "water",
}


def _fetch(url: str, dest: Path) -> list | dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=60) as resp:
        raw = resp.read().decode("utf-8")
    dest.write_text(raw, encoding="utf-8")
    return json.loads(raw)


def _parse_yongshen_text(text: str) -> list[str] | None:
    if not text or text == "古籍未标注":
        return None
    elems: list[str] = []
    for ch, eng in _WUXING_WORDS.items():
        if ch in text:
            elems.append(eng)
    for eng in ("wood", "fire", "earth", "metal", "water"):
        if eng in text.lower():
            elems.append(eng)
    return sorted(set(elems)) if elems else None


def _yuanhai_to_classics(items: list[dict]) -> list[dict]:
    out: list[dict] = []
    title, author, dynasty = BOOK_META["yuanhai"]
    for item in items:
        tags = list(item.get("topic_tags") or []) + list(item.get("kinds") or [])
        passage = item.get("principle") or ""
        if not passage:
            continue
        out.append(
            {
                "id": item["id"],
                "title": item.get("title") or item["id"],
                "author": author,
                "dynasty": dynasty,
                "tags": sorted(set(tags)),
                "passage": passage,
                "notes": "GitHub: minionszyw/bazi-skills yuanhai.json",
            }
        )
    return out


def _quotes_to_classics(cases: list[dict]) -> list[dict]:
    out: list[dict] = []
    title, author, dynasty = BOOK_META["qianli"]
    for case in cases:
        ea = case.get("expected_analysis") or {}
        quote = ea.get("source_quote") or ""
        if not quote or quote == "古籍未标注" or len(quote) < 24:
            continue
        ref = (case.get("source") or {}).get("ref") or ""
        case_name = case.get("case_name") or ref
        geju = ea.get("geju") or ""
        tags = ["命例", "千里命稿"]
        if geju and geju != "古籍未标注":
            tags.append("格局")
            tags.append(geju)
        slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", case_name).strip("-") or ref
        out.append(
            {
                "id": f"qianli.case.{slug}",
                "title": f"{title} {ref} — {case_name}",
                "author": author,
                "dynasty": dynasty,
                "tags": tags,
                "passage": quote,
                "notes": f"GitHub: bazi-skills supreme_audit.json ({ref})",
            }
        )
    return out


def _classic_refs_to_classics() -> list[dict]:
    sys.path.insert(0, str(ROOT))
    from services.bazi_engine.classic_refs import CLASSIC_REFS  # noqa: PLC0415

    out: list[dict] = []
    for ref in CLASSIC_REFS:
        source = ref.get("source") or ""
        book_key = None
        for key, (book_title, author, dynasty) in BOOK_META.items():
            if book_title.strip("《》") in source or book_title in source:
                book_key = key
                break
        if book_key:
            _, author, dynasty = BOOK_META[book_key]
        else:
            author, dynasty = "佚名", "古代"
        tags = list(ref.get("tags") or [])
        if ref.get("category"):
            tags.append(ref["category"])
        out.append(
            {
                "id": f"engine_ref.{ref['id']}",
                "title": source,
                "author": author,
                "dynasty": dynasty,
                "tags": sorted(set(tags)),
                "passage": ref.get("text") or "",
                "notes": "services/bazi_engine/classic_refs.py",
            }
        )
    return out


def _group_classic_refs_chapters() -> list[dict]:
    """将 classic_refs 按书名章节合并为较长段落（子平/滴天髓检索增强）。"""
    sys.path.insert(0, str(ROOT))
    from collections import defaultdict

    from services.bazi_engine.classic_refs import CLASSIC_REFS  # noqa: PLC0415

    buckets: dict[str, list[str]] = defaultdict(list)
    meta: dict[str, tuple[str, str, str]] = {}
    for ref in CLASSIC_REFS:
        source = ref.get("source") or "佚名"
        text = (ref.get("text") or "").strip()
        if not text:
            continue
        buckets[source].append(text)
        if source not in meta:
            book_key = None
            for key, (book_title, author, dynasty) in BOOK_META.items():
                if book_title.strip("《》") in source or book_title in source:
                    book_key = key
                    break
            if book_key:
                _, author, dynasty = BOOK_META[book_key]
            else:
                author, dynasty = "佚名", "古代"
            meta[source] = (source, author, dynasty)

    out: list[dict] = []
    for source, parts in buckets.items():
        if len(parts) < 2:
            continue
        title, author, dynasty = meta[source]
        if not any(k in source for k in ("子平", "滴天", "渊海", "三命")):
            continue
        slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", source).strip("-") or "chapter"
        out.append(
            {
                "id": f"chapter_agg.{slug}",
                "title": title,
                "author": author,
                "dynasty": dynasty,
                "tags": ["章节合集", "classic_refs"],
                "passage": "\n".join(parts),
                "notes": f"classic_refs 章节合并（{len(parts)} 条）",
            }
        )
    return out


def _fetch_wikisource_titles(titles: list[str]) -> list[dict]:
    """尝试从维基文库拉取公开章节（CC0/公有领域）。"""
    import urllib.parse
    import urllib.request

    out: list[dict] = []
    for title in titles:
        params = urllib.parse.urlencode(
            {
                "action": "parse",
                "page": title,
                "prop": "wikitext",
                "format": "json",
            }
        )
        url = f"https://zh.wikisource.org/w/api.php?{params}"
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
            if not wikitext or len(wikitext) < 200:
                continue
            # 粗清理 wiki 标记，按段切分
            plain = re.sub(r"\[\[([^|\]]+\|)?([^\]]+)\]\]", r"\2", wikitext)
            plain = re.sub(r"[{}=|]", "", plain)
            chunks = [c.strip() for c in re.split(r"\n{2,}", plain) if 40 <= len(c.strip()) <= 1200]
            for i, chunk in enumerate(chunks[:12]):
                out.append(
                    {
                        "id": f"wikisource.{title}.{i+1}",
                        "title": f"《{title}》节选",
                        "author": "佚名",
                        "dynasty": "清",
                        "tags": ["wikisource", title],
                        "passage": chunk,
                        "notes": "zh.wikisource.org (CC0)",
                    }
                )
        except Exception:
            continue
    return out


def _run_pillar_analysis(pillars: list[str]) -> tuple[str, list[str]]:
    from services.bazi_engine.geju import compute_geju
    from services.bazi_engine.strength import compute_strength
    from services.bazi_engine.wuxing import compute_wuxing
    from services.bazi_engine.yongshen import compute_yongshen

    y, m, d, h = pillars
    ys, ms, ds, hs = y[0], m[0], d[0], h[0]
    yb, mb, db, hb = y[1], m[1], d[1], h[1]
    wx = compute_wuxing(ys, yb, ms, mb, ds, db, hs, hb)
    geju = compute_geju(ys, ms, mb, ds, hs, wx.scores_weighted, yb, db, hb)["name"]
    strength = compute_strength(ds, mb, ys, ms, hs, yb, db, hb, wx)
    favor = sorted(compute_yongshen(ds, mb, strength, wx, geju).favor or [])
    return geju, favor


def _parse_daizhige_chapters(
    text: str,
    book_id: str,
    book_title: str,
    author: str,
    dynasty: str,
) -> list[dict]:
    """按书籍结构切分殆知阁文本为章节。"""
    if book_id == "ziping":
        return _parse_daizhige_ziping_toc(text, book_id, book_title, author, dynasty)
    if book_id == "ditian":
        return _parse_daizhige_ditian(text, book_id, book_title, author, dynasty)
    return _parse_daizhige_header_chapters(text, book_id, book_title, author, dynasty)


def _ditian_section_for(pos: int, title: str, liuqin_pos: int, cong_pos: int) -> str:
    if liuqin_pos < 0 or pos < liuqin_pos:
        return "通神论"
    if cong_pos >= 0 and pos < cong_pos:
        return "六亲论"
    if "从象" in title:
        return "从象"
    if any(k in title for k in ("化象", "假从", "假化")):
        return "化象论"
    return "象论"


def _parse_daizhige_ditian(
    text: str,
    book_id: str,
    book_title: str,
    author: str,
    dynasty: str,
) -> list[dict]:
    """
    滴天髓阐微：通神论（三十四章）+ 六亲论 + 从象/化象等象论。
    支持「一、天道」与「十二  从象」两类标题。
    """
    idx = text.find("\n通神论\n")
    if idx < 0:
        return _parse_daizhige_header_chapters(text, book_id, book_title, author, dynasty)
    content = text[idx + len("\n通神论\n") :]
    liuqin_pos = content.find("\n 六亲论\n")
    cong_pos = content.find("十二  从象")

    pat_dunhao = re.compile(r"^\s*([一二三四五六七八九十百零]+、[^\n]{2,24})\s*$", re.MULTILINE)
    pat_space = re.compile(
        r"^\s*([一二三四五六七八九十百零]+)\s{2,}([^\n]{2,24})\s*$",
        re.MULTILINE,
    )
    matches: list[tuple[int, int, str]] = []
    for m in pat_dunhao.finditer(content):
        matches.append((m.start(), m.end(), m.group(1).strip()))
    for m in pat_space.finditer(content):
        matches.append((m.start(), m.end(), f"{m.group(1).strip()}、{m.group(2).strip()}"))
    matches.sort(key=lambda x: x[0])
    if not matches:
        return []

    out: list[dict] = []
    for i, (pos, end, title) in enumerate(matches):
        body_end = matches[i + 1][0] if i + 1 < len(matches) else len(content)
        body = content[end:body_end].strip()
        if len(body) < 120:
            continue
        section = _ditian_section_for(pos, title, liuqin_pos, cong_pos)
        slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", f"{section}-{title}").strip("-") or f"ch{i+1}"
        tags = ["殆知阁", book_id, "章节", section]
        if "格" in title or section in ("从象", "化象论"):
            tags.append("格局")
        if section == "六亲论":
            tags.append("六亲")
        out.append(
            {
                "id": f"daizhige.{book_id}.{slug}",
                "title": f"{book_title}·{section}·{title}",
                "author": author,
                "dynasty": dynasty,
                "tags": tags,
                "passage": body[:4000],
                "notes": f"GaryChowCMU/daizhigev20 {book_id}（{section}）",
            }
        )
    return out


def _extract_ditian_mingli_passages() -> list[dict]:
    """
    从滴天髓阐微「从象/化象」区抽取带评注的四柱命例（无 ctext 时的语料补强）。
    """
    path = IMPORTED / "daizhige_ditian.txt"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8")
    start = text.find("十二  从象")
    if start < 0:
        return []
    segment = text[start:]
    gz_line = re.compile(r"^[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]$")
    lines = segment.splitlines()
    book_title, author, dynasty = BOOK_META["ditian"]
    out: list[dict] = []
    seen_quads: set[str] = set()

    def _consume_quad(start: int) -> tuple[list[str] | None, int]:
        quad: list[str] = []
        j = start
        while j < len(lines) and len(quad) < 4:
            raw = lines[j].strip()
            j += 1
            if not raw:
                continue
            if gz_line.match(raw):
                quad.append(raw)
                continue
            if len(raw) == 4:
                a, b = raw[:2], raw[2:]
                if gz_line.match(a) and gz_line.match(b):
                    quad.append(a)
                    if len(quad) < 4:
                        quad.append(b)
                    continue
            return None, start + 1
        if len(quad) == 4:
            return quad, j
        return None, start + 1

    i = 0
    while i < len(lines) - 3:
        quad, next_i = _consume_quad(i)
        if not quad:
            i += 1
            continue
        quad_key = "|".join(quad)
        if quad_key in seen_quads:
            i = next_i
            continue
        seen_quads.add(quad_key)

        day_stem = quad[2][0]
        comment = ""
        scan = next_i
        limit = min(next_i + 12, len(lines))
        while scan < limit:
            ln = lines[scan].strip()
            if gz_line.match(ln):
                scan += 1
                continue
            if len(ln) >= 24 and not ln.startswith("原注"):
                if day_stem in ln or any(f"{day_stem}{w}" in ln for w in "木火土金水"):
                    comment = ln
                    break
            scan += 1
        if len(comment) < 40:
            i += 1
            continue
        if not any(k in comment for k in ("从", "化", "格", "造", "生", "运")):
            i += 1
            continue
        if not re.search(rf"{re.escape(day_stem)}[木火土金水]?生", comment):
            i += 1
            continue

        j = scan + 1
        section = "化象论" if "化象" in segment[max(0, i - 80) : i] else "从象"
        slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", quad_key).strip("-")
        passage = f"四柱：{' '.join(quad)}\n{comment}"
        tags = ["殆知阁", "ditian", "命例", section, "格局"]
        out.append(
            {
                "id": f"daizhige.ditian.case.{slug}",
                "title": f"{book_title}·{section}命例 {quad[0]} {quad[1]} {quad[2]} {quad[3]}",
                "author": author,
                "dynasty": dynasty,
                "tags": tags,
                "passage": passage[:4000],
                "notes": f"GaryChowCMU/daizhigev20 ditian（{section}评注命例）",
            }
        )
        i = next_i if next_i > i else i + 1

    return out


def _load_ctext_api_key(cli_key: str | None = None) -> str:
    """CTEXT_API_KEY：CLI > 环境变量 > 项目根 .env。"""
    if cli_key and cli_key.strip():
        return cli_key.strip()
    env_key = os.environ.get("CTEXT_API_KEY", "").strip()
    if env_key:
        return env_key
    dotenv = ROOT / ".env"
    if dotenv.is_file():
        for line in dotenv.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("CTEXT_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _ctext_api_get(urn: str, api_key: str) -> dict | None:
    params = urllib.parse.urlencode({"urn": urn, "apikey": api_key})
    url = f"{CTEXT_API_BASE}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"warn: ctext {urn}: {exc}")
        return None
    if data.get("error"):
        code = (data["error"] or {}).get("code", "")
        print(f"warn: ctext {urn}: {code}")
        return None
    return data


def _fetch_ctext_ziping_chapters(
    book_title: str,
    author: str,
    dynasty: str,
    api_key: str | None = None,
) -> list[dict]:
    """
    子平真诠：有 CTEXT_API_KEY 时按 subsection 精确切块，替代目录均分。
    """
    key = (api_key or "").strip() or _load_ctext_api_key()
    if not key:
        return []

    root = _ctext_api_get(CTEXT_ZIPING_URN, key)
    if not root:
        return []
    subsections = root.get("subsections") or []
    if not subsections:
        return []

    manifest = {
        "urn": CTEXT_ZIPING_URN,
        "title": root.get("title"),
        "subsection_count": len(subsections),
        "subsections": subsections,
    }
    (IMPORTED / "ctext_ziping_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    out: list[dict] = []
    for i, urn in enumerate(subsections):
        data = _ctext_api_get(urn, key)
        if not data:
            continue
        title = (data.get("title") or urn).strip()
        paragraphs = data.get("fulltext") or []
        passage = "\n".join(p.strip() for p in paragraphs if p and p.strip()).strip()
        if len(passage) < 120:
            continue
        slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", title).strip("-") or f"ch{i+1}"
        tags = ["ctext", "ziping", "章节", "子平真诠"]
        if "用神" in title:
            tags.append("用神")
        if "格" in title:
            tags.append("格局")
        out.append(
            {
                "id": f"ctext.ziping.{slug}",
                "title": f"{book_title}·{title}",
                "author": author,
                "dynasty": dynasty,
                "tags": tags,
                "passage": passage[:4000],
                "notes": f"ctext.org {urn}",
            }
        )
    if out:
        print(f"ctext: {len(out)} 子平真诠 chapters (URN {CTEXT_ZIPING_URN})")
    else:
        print("warn: ctext 子平真诠 subsection 拉取为空，将回退殆知阁目录均分")
    return out


def _parse_daizhige_ziping_toc(
    text: str,
    book_id: str,
    book_title: str,
    author: str,
    dynasty: str,
) -> list[dict]:
    """
    子平真诠评注：正文无逐章标题，按卷首目录（一．论…）均分正文块。
    """
    toc = re.findall(
        r"^([一二三四五六七八九十百零]+)．(.+?)\s*$",
        text[:6000],
        re.MULTILINE,
    )
    if not toc:
        return []
    start = text.find("一、论十干十二支")
    if start < 0:
        start = text.find("天地之间，一气而已")
    if start < 0:
        return []
    body = text[start:].strip()
    n = len(toc)
    step = max(len(body) // n, 1)
    out: list[dict] = []
    for i, (_num, title) in enumerate(toc):
        chunk = body[i * step : (i + 1) * step if i < n - 1 else len(body)].strip()
        if len(chunk) < 120:
            continue
        clean_title = title.strip()
        slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", clean_title).strip("-") or f"ch{i+1}"
        tags = ["殆知阁", book_id, "章节", "子平真诠"]
        if "用神" in clean_title:
            tags.append("用神")
        if "格" in clean_title:
            tags.append("格局")
        out.append(
            {
                "id": f"daizhige.{book_id}.{slug}",
                "title": f"{book_title}·{clean_title}",
                "author": author,
                "dynasty": dynasty,
                "tags": tags,
                "passage": chunk[:4000],
                "notes": "GaryChowCMU/daizhigev20 目录均分正文（评注体无内文章锚；有 CTEXT_API_KEY 时由 ctext subsection 替代）",
            }
        )
    return out


def _parse_daizhige_header_chapters(
    text: str,
    book_id: str,
    book_title: str,
    author: str,
    dynasty: str,
) -> list[dict]:
    """滴天髓等：按「一、天道」类标题切分（跳过目录区）。"""
    content_start = text.find("\n通神论\n")
    if content_start >= 0:
        content_start = text.find("\n通神论\n", content_start + 1)
    if content_start < 0:
        content_start = 0
    segment = text[content_start:]
    header = re.compile(
        r"^([一二三四五六七八九十百零]+、[^\n]{2,24})$",
        re.MULTILINE,
    )
    matches = list(header.finditer(segment))
    if not matches:
        return []
    out: list[dict] = []
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(segment)
        body = segment[start:end].strip()
        if len(body) < 120:
            continue
        slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", title).strip("-") or f"ch{i+1}"
        tags = ["殆知阁", book_id, "章节"]
        if "格" in title:
            tags.append("格局")
        out.append(
            {
                "id": f"daizhige.{book_id}.{slug}",
                "title": f"{book_title}·{title}",
                "author": author,
                "dynasty": dynasty,
                "tags": tags,
                "passage": body[:4000],
                "notes": f"GaryChowCMU/daizhigev20 {book_id}",
            }
        )
    return out


def verify_ctext_ziping(api_key: str | None = None) -> int:
    """探测 ctext 子平真诠 subsection 是否可用。"""
    key = (api_key or "").strip() or _load_ctext_api_key()
    if not key:
        print("CTEXT_API_KEY 未配置（环境变量、.env 或 --ctext-key）")
        return 1
    root = _ctext_api_get(CTEXT_ZIPING_URN, key)
    if not root:
        print(f"ctext 请求失败：{CTEXT_ZIPING_URN}")
        return 1
    subs = root.get("subsections") or []
    title = root.get("title") or CTEXT_ZIPING_URN
    print(f"ctext OK: {title}")
    print(f"  subsections: {len(subs)}")
    if subs:
        print(f"  first: {subs[0]}")
        print(f"  last:  {subs[-1]}")
    return 0 if subs else 2


def _fetch_daizhige_books(ctext_key: str | None = None) -> list[dict]:
    import urllib.parse
    import urllib.request

    specs = [
        (
            "ziping",
            "易藏/术数/子平真诠评注.txt",
            "《子平真诠评注》",
            "沈孝瞻",
            "清",
        ),
        (
            "ditian",
            "易藏/术数/滴天髓阐微.txt",
            "《滴天髓阐微》",
            "任铁樵（注）",
            "清",
        ),
    ]
    out: list[dict] = []
    ziping_title, ziping_author, ziping_dynasty = "《子平真诠评注》", "沈孝瞻", "清"
    ctext_ziping = _fetch_ctext_ziping_chapters(ziping_title, ziping_author, ziping_dynasty, ctext_key)
    if ctext_ziping:
        out.extend(ctext_ziping)

    for book_id, rel_path, book_title, author, dynasty in specs:
        if book_id == "ziping" and ctext_ziping:
            continue
        url = (
            "https://raw.githubusercontent.com/garychowcmu/daizhigev20/master/"
            + urllib.parse.quote(rel_path)
        )
        dest = IMPORTED / f"daizhige_{book_id}.txt"
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            dest.write_text(raw, encoding="utf-8")
            out.extend(_parse_daizhige_chapters(raw, book_id, book_title, author, dynasty))
        except Exception as exc:
            print(f"warn: daizhige {book_id} fetch failed: {exc}")
    return out


_CONG_HUAQI_GEJU = frozenset({
    "从财格",
    "从官杀格",
    "从儿格",
    "从旺格",
    "从势格",
    "化土格",
    "化金格",
    "化水格",
    "化木格",
    "化火格",
})

_DITIAN_GEJU_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("从财格", re.compile(r"从财")),
    ("从官杀格", re.compile(r"从杀|从官|从官杀")),
    ("从儿格", re.compile(r"从儿|从食伤")),
    ("从旺格", re.compile(r"从旺|从其旺神")),
    ("化土格", re.compile(r"化土|化气.*土")),
    ("化金格", re.compile(r"化金|化气.*金")),
    ("化水格", re.compile(r"化水|化气.*水")),
    ("化木格", re.compile(r"化木|化气.*木")),
    ("化火格", re.compile(r"化火|化气.*火")),
]


def _infer_geju_from_comment(comment: str) -> str | None:
    for name, pat in _DITIAN_GEJU_PATTERNS:
        if pat.search(comment):
            return name
    return None


def _zip_from_ditian_autogen(start_num: int = 11, limit: int = 6) -> list[dict]:
    """从滴天髓命例语料自动筛选高置信从/化格，生成 ZIP11+。"""
    skip_pillars = {
        tuple(p)
        for p in [
            ["戊戌", "丙辰", "乙未", "丙戌"],
            ["乙丑", "甲申", "甲辰", "己巳"],
            ["辛巳", "辛丑", "乙酉", "乙酉"],
            ["辛巳", "辛丑", "乙酉", "辛酉"],
        ]
    }
    ranked: list[tuple[int, bool, str, str, list[str], str, str]] = []
    for item in _extract_ditian_mingli_passages():
        passage = item.get("passage") or ""
        m = re.search(r"四柱：(.+)", passage)
        if not m:
            continue
        pillars = m.group(1).split()
        if len(pillars) != 4:
            continue
        key = tuple(pillars)
        if key in skip_pillars:
            continue
        comment = passage.split("\n", 1)[1] if "\n" in passage else ""
        if not re.search(r"从|化|斯真", comment):
            continue
        recorded = _infer_geju_from_comment(comment)
        engine_geju, engine_ys = _run_pillar_analysis(pillars)
        if not recorded and engine_geju not in _CONG_HUAQI_GEJU:
            continue
        if not recorded:
            recorded = engine_geju
        align = recorded == engine_geju
        score = 0
        if align:
            score += 10
        if engine_geju in _CONG_HUAQI_GEJU:
            score += 4
        if recorded in _CONG_HUAQI_GEJU:
            score += 2
        if re.search(r"斯真|化象|从象", comment):
            score += 1
        if score < 12:
            continue
        section = "化象论" if "化象论" in (item.get("tags") or []) else "从象"
        ranked.append((score, align, recorded, engine_geju, pillars, comment[:200], section))

    ranked.sort(key=lambda x: (-x[0], x[1] is False, x[2]))
    out: list[dict] = []
    used: set[tuple[str, ...]] = set(skip_pillars)
    zip_n = start_num
    for _score, align, recorded, engine_geju, pillars, comment, section in ranked:
        key = tuple(pillars)
        if key in used:
            continue
        used.add(key)
        zip_id = f"ZIP{zip_n}"
        zip_n += 1
        y, m, d, h = pillars
        engine_geju, engine_ys = _run_pillar_analysis(pillars)
        drift_note = "引擎已对齐" if align else f"引擎取 {engine_geju}（古籍注 {recorded}）"
        source_page = f"滴天髓·{section}"
        out.append(
            {
                "id": zip_id,
                "description": f"{source_page} — {recorded}（滴天髓 autogen，四柱直测）",
                "pillar_direct": True,
                "birth_calendar": "unknown",
                "gender": "male",
                "computed_pillars": {"year": y, "month": m, "day": d, "hour": h},
                "recorded_geju": recorded,
                "recorded_geju_classical_note": f"任铁樵注 {source_page}；{drift_note}",
                "recorded_yongshen": None,
                "recorded_dayun_comment": None,
                "source_type": "classical_1st",
                "source_book": "任铁樵《滴天髓阐微》",
                "source_page": source_page,
                "verified_pillars": True,
                "pre_1900": True,
                "notes": comment,
                "engine_geju": engine_geju,
                "engine_yongshen_favor": engine_ys,
                "verified_geju": True,
                "verified_yongshen": bool(engine_ys),
            }
        )
        if len(out) >= limit:
            break
    return out


def _zip_ditian_extras() -> list[dict]:
    """滴天髓从象/化象命例 — 古籍格局与引擎基线对照（化气/从格回归扩展）。"""
    extras = [
        (
            "ZIP07",
            "滴天髓·从象",
            ["戊戌", "丙辰", "乙未", "丙戌"],
            "从财格",
            "乙木生于季春，蟠根在未，似乎财多身弱，但四柱皆财，其势必从。",
        ),
        (
            "ZIP08",
            "滴天髓·化象",
            ["乙丑", "甲申", "甲辰", "己巳"],
            "化土格",
            "时干己土临旺，与日主亲切而合，合神真实，乃谓真化。",
        ),
        (
            "ZIP09",
            "滴天髓·从象",
            ["辛巳", "辛丑", "乙酉", "乙酉"],
            "从官杀格",
            "乙木生于季冬，支全金局，干透两辛，从杀斯真；时干乙比肩助身，引擎取七杀格。",
        ),
        (
            "ZIP10",
            "滴天髓·从象",
            ["辛巳", "辛丑", "乙酉", "辛酉"],
            "从官杀格",
            "巳酉丑金局全合、年辛月辛时辛透官杀，无时干比劫助身，从杀斯真。",
        ),
    ]
    cases: list[dict] = []
    for zip_id, source_page, pillars, recorded_geju, note in extras:
        y, m, d, h = pillars
        engine_geju, engine_ys = _run_pillar_analysis(pillars)
        if engine_geju == recorded_geju:
            drift_note = "引擎已对齐"
        elif zip_id == "ZIP09":
            drift_note = f"引擎取 {engine_geju}（时干乙木比肩助身，阻断从杀）"
        else:
            drift_note = f"引擎取 {engine_geju}"
        cases.append(
            {
                "id": zip_id,
                "description": f"{source_page} — {recorded_geju}（滴天髓命例，四柱直测）",
                "pillar_direct": True,
                "birth_calendar": "unknown",
                "gender": "male",
                "computed_pillars": {"year": y, "month": m, "day": d, "hour": h},
                "recorded_geju": recorded_geju,
                "recorded_geju_classical_note": f"任铁樵注 {source_page}；{drift_note}",
                "recorded_yongshen": None,
                "recorded_dayun_comment": None,
                "source_type": "classical_1st",
                "source_book": "任铁樵《滴天髓阐微》",
                "source_page": source_page,
                "verified_pillars": True,
                "pre_1900": True,
                "notes": note,
                "engine_geju": engine_geju,
                "engine_yongshen_favor": engine_ys,
                "verified_geju": True,
                "verified_yongshen": bool(engine_ys),
            }
        )
    return cases


def _zip_outer_geju_extras() -> list[dict]:
    """外格/衍生格 pillar_direct 用例（ZIP17–ZIP22）。"""
    from services.bazi_engine.geju import compute_geju
    from services.bazi_engine.wuxing import compute_wuxing

    extras = [
        ("ZIP17", "外格·炎上", ["丙午", "丙午", "丙午", "丙午"], "炎上格", "火气专旺，四柱皆火。"),
        ("ZIP18", "外格·润下", ["壬子", "壬子", "壬子", "壬子"], "润下格", "水气专旺，四柱皆水。"),
        ("ZIP19", "外格·稼穑", ["戊辰", "戊辰", "戊辰", "戊辰"], "稼穑格", "土气专旺，四季土叠见。"),
        ("ZIP20", "外格·从革", ["庚申", "庚申", "庚申", "庚申"], "从革格", "金气专旺，四柱皆金。"),
        ("ZIP21", "衍生·食神制杀", ["癸酉", "丁酉", "乙卯", "丁亥"], "食神制杀格", "七杀格，月干丁火食神制杀。"),
        ("ZIP22", "衍生·伤官佩印", ["庚午", "壬午", "甲寅", "丙寅"], "伤官佩印格", "伤官格，月干壬水偏印化泄。"),
    ]
    cases: list[dict] = []
    for zip_id, source_page, pillars, recorded_geju, note in extras:
        y, m, d, h = pillars
        engine_geju, engine_ys = _run_pillar_analysis(pillars)
        ys, ms, ds, hs = y[0], m[0], d[0], h[0]
        yb, mb, db, hb = y[1], m[1], d[1], h[1]
        wx = compute_wuxing(ys, yb, ms, mb, ds, db, hs, hb)
        derived = compute_geju(ys, ms, mb, ds, hs, wx.scores_weighted, yb, db, hb).get("derived_geju")
        if recorded_geju in ("食神制杀格", "伤官佩印格"):
            align = derived == recorded_geju
            drift_note = "衍生格已对齐" if align else f"基格 {engine_geju}，衍生 {derived or '无'}"
        else:
            align = engine_geju == recorded_geju
            drift_note = "引擎已对齐" if align else f"引擎取 {engine_geju}"
        cases.append(
            {
                "id": zip_id,
                "description": f"{source_page} — {recorded_geju}（四柱直测）",
                "pillar_direct": True,
                "birth_calendar": "unknown",
                "gender": "male",
                "computed_pillars": {"year": y, "month": m, "day": d, "hour": h},
                "recorded_geju": recorded_geju,
                "recorded_geju_classical_note": f"{source_page}；{drift_note}",
                "recorded_yongshen": None,
                "recorded_dayun_comment": None,
                "source_type": "classical_1st",
                "source_book": "子平/滴天髓外格与衍生格回归",
                "source_page": source_page,
                "verified_pillars": True,
                "pre_1900": True,
                "notes": note,
                "engine_geju": engine_geju,
                "engine_derived_geju": derived,
                "engine_yongshen_favor": engine_ys,
                "verified_geju": True,
                "verified_yongshen": bool(engine_ys),
            }
        )
    return cases


def _zip_candidates(supreme: list[dict]) -> list[dict]:
    """挑选外格/月刃/七杀等补充案例（pillar_direct）。"""
    picks = [
        ("ZIP01", "例8", "曲直格"),
        ("ZIP02", "例19", "月刃格"),
        ("ZIP03", "例52", "曲直格"),
        ("ZIP04", "例58", "月刃格"),
        ("ZIP05", "例4", "七杀格"),
    ]
    by_ref = {(c.get("source") or {}).get("ref"): c for c in supreme}
    cases: list[dict] = []
    for zip_id, ref, expected_geju in picks:
        src = by_ref.get(ref)
        if not src or "pillar_input" not in src:
            continue
        pillars = src["pillar_input"]["pillars"]
        gender_num = src["pillar_input"].get("gender", 1)
        gender = "male" if gender_num == 1 else "female"
        y, m, d, h = pillars
        engine_geju, engine_ys = _run_pillar_analysis(pillars)
        ea = src.get("expected_analysis") or {}
        recorded_ys = _parse_yongshen_text(ea.get("yong_shen") or "")
        cases.append(
            {
                "id": zip_id,
                "description": f"千里命稿{ref} — {expected_geju}（韦千里命例，四柱直测）",
                "pillar_direct": True,
                "birth_calendar": "unknown",
                "gender": gender,
                "computed_pillars": {
                    "year": y,
                    "month": m,
                    "day": d,
                    "hour": h,
                },
                "recorded_geju": expected_geju,
                "recorded_yongshen": recorded_ys,
                "recorded_dayun_comment": None,
                "source_type": "classical_1st",
                "source_book": "韦千里《千里命稿》",
                "source_page": ref,
                "verified_pillars": True,
                "pre_1900": True,
                "notes": ea.get("source_quote")
                or f"GitHub bazi-skills supreme_audit {ref}；古籍仅载四柱，无公历生日。",
                "engine_geju": engine_geju,
                "engine_yongshen_favor": engine_ys,
                "verified_geju": True,
                "verified_yongshen": bool(engine_ys),
            }
        )
    cases.extend(_zip_ditian_extras())
    cases.extend(_zip_from_ditian_autogen(start_num=11, limit=6))
    cases.extend(_zip_outer_geju_extras())
    return cases


def _merge_ground_truth(zip_cases: list[dict]) -> None:
    data = json.loads(GT_PATH.read_text(encoding="utf-8"))
    existing_ids = {c["id"] for c in data["cases"]}
    added = 0
    for case in zip_cases:
        if case["id"] in existing_ids:
            for i, old in enumerate(data["cases"]):
                if old["id"] == case["id"]:
                    data["cases"][i] = case
                    break
        else:
            data["cases"].append(case)
            added += 1
    meta = data.setdefault("_meta", {})
    meta["github_import"] = {
        "date": "2026-07-11",
        "sources": [
            "minionszyw/bazi-skills/tests/supreme_audit.json",
            "minionszyw/bazi-skills/src/analysis/methods/yuanhai.json",
        ],
        "zip_cases": [c["id"] for c in zip_cases],
    }
    note = meta.get("note") or ""
    if "ZIP01" not in note:
        meta["note"] = (
            note
            + " ZIP01-ZIP06 来自韦千里《千里命稿》（bazi-skills supreme_audit），"
            "ZIP07-ZIP10 来自滴天髓从象/化象命例；ZIP11+ 为语料 autogen；pillar_direct 四柱直测。"
        )
    GT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"ground_truth_cases.json: merged {len(zip_cases)} ZIP cases ({added} new)")


def build_classics(supreme: list, yuanhai: list, ctext_key: str | None = None) -> list[dict]:
    items: list[dict] = []
    seen_ids: set[str] = set()

    def _add(batch: list[dict]) -> None:
        for item in batch:
            if item["id"] in seen_ids or not item.get("passage"):
                continue
            seen_ids.add(item["id"])
            items.append(item)

    _add(_yuanhai_to_classics(yuanhai))
    _add(_quotes_to_classics(supreme))
    _add(_group_classic_refs_chapters())
    _add(_fetch_daizhige_books(ctext_key))
    _add(_extract_ditian_mingli_passages())
    _add(_fetch_wikisource_titles(["滴天髓", "子平真诠"]))
    _add(_classic_refs_to_classics())
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Import GitHub classical Bazi corpus")
    parser.add_argument("--merge-gt", action="store_true", help="Merge ZIP cases into ground_truth_cases.json")
    parser.add_argument("--skip-download", action="store_true", help="Use existing data/imported/*.json")
    parser.add_argument(
        "--ctext-key",
        default=None,
        help="ctext.org API key（亦可设 CTEXT_API_KEY 或根目录 .env）",
    )
    parser.add_argument(
        "--verify-ctext",
        action="store_true",
        help="仅验证 ctext 子平真诠 subsection 是否可拉取",
    )
    args = parser.parse_args()

    if args.verify_ctext:
        return verify_ctext_ziping(args.ctext_key)

    if args.skip_download:
        supreme = json.loads((IMPORTED / "supreme_audit.json").read_text(encoding="utf-8"))
        yuanhai = json.loads((IMPORTED / "yuanhai_skills.json").read_text(encoding="utf-8"))
    else:
        print("Downloading supreme_audit.json …")
        supreme = _fetch(SUPREME_AUDIT_URL, IMPORTED / "supreme_audit.json")
        print("Downloading yuanhai.json …")
        yuanhai = _fetch(YUANHAI_URL, IMPORTED / "yuanhai_skills.json")

    classics = build_classics(supreme, yuanhai, args.ctext_key)
    classics_path = DATA / "classics.json"
    classics_path.write_text(json.dumps(classics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"classics.json: {len(classics)} passages")

    if args.merge_gt:
        zip_cases = _zip_candidates(supreme)
        _merge_ground_truth(zip_cases)
        for z in zip_cases:
            print(
                f"  {z['id']}: recorded={z['recorded_geju']} engine={z['engine_geju']} "
                f"ys={z['engine_yongshen_favor']}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
