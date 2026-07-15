#!/usr/bin/env python3
"""五书无人值守 Autopilot（方案 A · 子串校验升 verified）。

设计：docs/superpowers/specs/2026-07-16-five-classics-autopilot-design.md

用法:
  python scripts/five_classics_autopilot.py
  python scripts/five_classics_autopilot.py --max-rounds 3 --books 穷通宝鉴
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLASSICS = ROOT / "data" / "classics.json"
IMPORTED = ROOT / "data" / "imported"
SPOTCHECK = ROOT / "docs" / "reports" / "spotcheck-ctext.md"
BASES_DIR = IMPORTED / "five_classics_bases"
REPORT_JSON = ROOT / "docs" / "reports" / "five-classics-autopilot-latest.json"

CANON = ("滴天髓", "子平真诠", "穷通宝鉴", "三命通会", "渊海子平")

BOOK_META = {
    "穷通宝鉴": ("余春台（传）", "清"),
    "子平真诠": ("沈孝瞻", "清"),
    "滴天髓": ("任铁樵（注）", "清"),
    "三命通会": ("万民英", "明"),
    "渊海子平": ("徐子平（传）", "宋"),
}

# 优先级 P1→P8（设计 §2）
PRIORITY_TARGETS: list[tuple[str, str | None, str]] = [
    ("穷通宝鉴", "C-调候", "matrix"),
    ("三命通会", "C-日主", "matrix"),
    ("穷通宝鉴", None, "count"),
    ("三命通会", None, "count"),
    ("渊海子平", None, "count"),
    ("子平真诠", None, "count"),
    ("滴天髓", None, "count"),
]

GATES = {
    "滴天髓": 80,
    "子平真诠": 45,
    "穷通宝鉴": 40,
    "三命通会": 30,
    "渊海子平": 20,
}

CATEGORY_TAG_HINTS: dict[str, tuple[str, ...]] = {
    "C-格局": ("格局", "从象", "专旺", "正格"),
    "C-用神": ("用神", "取用"),
    "C-调候": ("调候", "寒", "暖", "燥", "湿", "春", "夏", "秋", "冬", "月令", "余寒"),
    "C-十神": ("十神", "正官", "七杀", "正印", "偏印", "财", "食神", "伤官"),
    "C-岁运": ("大运", "流年", "岁运", "行运"),
    "C-神煞": ("神煞", "空亡", "桃花", "驿马"),
    "C-日主": ("日主", "日干", "甲木", "乙木", "丙火", "丁火", "戊土", "己土", "庚金", "辛金", "壬水", "癸水"),
}

MONTH_BRANCHES = "寅卯辰巳午未申酉戌亥子丑"


def normalize(text: str) -> str:
    s = unicodedata.normalize("NFKC", text or "")
    s = re.sub(r"\s+", "", s)
    s = s.replace("\u3000", "")
    return s


def book_of(title: str | None) -> str | None:
    t = title or ""
    for b in CANON:
        if b in t:
            return b
    return None


def item_hits_category(item: dict, cat: str) -> bool:
    hints = CATEGORY_TAG_HINTS[cat]
    blob = " ".join(
        [
            str(item.get("title") or ""),
            str(item.get("passage") or "")[:240],
            " ".join(item.get("tags") or []),
        ]
    )
    return any(h in blob for h in hints)


def load_classics() -> list[dict]:
    return json.loads(CLASSICS.read_text(encoding="utf-8"))


def save_classics(items: list[dict]) -> None:
    CLASSICS.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def fetch_url(url: str, timeout: int = 60) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "fusheng-five-classics-autopilot/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_wikisource_plain(page: str) -> str:
    params = urllib.parse.urlencode(
        {"action": "parse", "page": page, "prop": "wikitext", "format": "json"}
    )
    url = f"https://zh.wikisource.org/w/api.php?{params}"
    data = json.loads(fetch_url(url, timeout=90))
    wt = data.get("parse", {}).get("wikitext", {}).get("*", "")
    if not wt:
        return ""
    plain = re.sub(r"\[\[[^|\]]*\|([^\]]+)\]\]", r"\1", wt)
    plain = re.sub(r"\[\[([^\]]+)\]\]", r"\1", plain)
    plain = re.sub(r"\{\{[^}]*\}\}", "", plain)
    plain = re.sub(r"<[^>]+>", "", plain)
    plain = re.sub(r"'{2,}", "", plain)
    plain = re.sub(r"=+", "\n", plain)
    plain = re.sub(r"[{}|]", "", plain)
    return plain


def load_or_fetch_base(book: str) -> tuple[str, str]:
    """返回 (fulltext, source_note)。优先本地缓存，避免外网超时。"""
    BASES_DIR.mkdir(parents=True, exist_ok=True)
    cache = BASES_DIR / f"{book}.txt"
    meta = BASES_DIR / f"{book}.source.json"

    if cache.exists() and cache.stat().st_size > 500:
        note = "cache"
        if meta.exists():
            note = json.loads(meta.read_text(encoding="utf-8")).get("source", "cache")
        return cache.read_text(encoding="utf-8", errors="replace"), str(note)

    # 已有 daizhige / imported 优先（滴天/子平）
    local_candidates = {
        "滴天髓": [
            IMPORTED / "daizhige_ditian.txt",
            IMPORTED / "daizhige_ditian.raw.txt",
        ],
        "子平真诠": [
            IMPORTED / "daizhige_ziping.txt",
        ],
        "渊海子平": [IMPORTED / "yuanhai_skills.json"],
    }
    for path in local_candidates.get(book, []):
        if path.exists() and path.suffix == ".txt" and path.stat().st_size > 500:
            text = path.read_text(encoding="utf-8", errors="replace")
            note = f"local:{path.relative_to(ROOT)}"
            cache.write_text(text, encoding="utf-8")
            meta.write_text(json.dumps({"source": note}, ensure_ascii=False, indent=2), encoding="utf-8")
            return text, note

    # 维基文库（可选；失败则 missing）
    wiki_pages = {
        "穷通宝鉴": "穷通宝鉴",
        "三命通会": "三命通会",
        "渊海子平": "渊海子平",
        "子平真诠": "子平真诠",
        "滴天髓": "滴天髓",
    }
    page = wiki_pages.get(book)
    if page:
        try:
            text = fetch_wikisource_plain(page)
            if len(normalize(text)) >= 800:
                note = f"wikisource:{page}"
                cache.write_text(text, encoding="utf-8")
                meta.write_text(
                    json.dumps(
                        {"source": note, "fetched_at": datetime.now(UTC).isoformat()},
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                return text, note
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            print(f"warn: wikisource {book}: {exc}")

    return "", f"missing:{book}"


def yuanhai_to_base() -> str:
    path = IMPORTED / "yuanhai_skills.json"
    if not path.exists():
        return ""
    data = json.loads(path.read_text(encoding="utf-8"))
    parts = []
    for item in data if isinstance(data, list) else []:
        p = item.get("principle") or item.get("text") or ""
        if p:
            parts.append(str(p))
    return "\n".join(parts)


def ensure_bases(books: list[str]) -> dict[str, tuple[str, str]]:
    out: dict[str, tuple[str, str]] = {}
    for b in books:
        text, note = load_or_fetch_base(b)
        if b == "渊海子平" and len(normalize(text)) < 400:
            yh = yuanhai_to_base()
            if yh:
                text, note = yh, "local:yuanhai_skills.json"
                BASES_DIR.mkdir(parents=True, exist_ok=True)
                (BASES_DIR / f"{b}.txt").write_text(text, encoding="utf-8")
        out[b] = (text, note)
        print(f"base {b}: chars={len(text)} norm={len(normalize(text))} src={note}")
    return out


def infer_tags(title: str, passage: str, prefer_cat: str | None) -> list[str]:
    tags: list[str] = []
    blob = title + passage[:200]
    if prefer_cat == "C-调候" or any(x in blob for x in ("春", "夏", "秋", "冬", "余寒", "调候", "月")):
        tags.append("调候")
    if prefer_cat == "C-日主" or any(x in blob for x in ("甲木", "乙木", "丙火", "日主", "论甲", "论乙")):
        tags.extend(["日主", "日干"])
    if "用神" in blob or "取用" in blob:
        tags.append("用神")
    if "大运" in blob or "流年" in blob or "行运" in blob:
        tags.append("岁运")
    if any(x in blob for x in ("正官", "七杀", "食神", "伤官", "正印", "偏财")):
        tags.append("十神")
    if prefer_cat:
        tags.append(prefer_cat)
    tags.append("autopilot")
    return sorted(set(tags))


def split_sections(text: str) -> list[tuple[str, str]]:
    """粗按标题切 (heading, body)。"""
    lines = text.splitlines()
    sections: list[tuple[str, list[str]]] = []
    cur_h = "正文"
    buf: list[str] = []
    heading_re = re.compile(r"^(#{1,6}\s*)?([三四五六七八九十百千〇零\d]+[、.\s]+)?.{1,40}$")
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if buf:
                buf.append("")
            continue
        is_heading = (
            stripped.startswith("#")
            or (len(stripped) <= 20 and any(k in stripped for k in ("论", "总论", "正月", "二月", "三月", "卷")))
            or (len(stripped) <= 12 and stripped.endswith(("论", "章", "节")))
        )
        if is_heading and sum(len(x) for x in buf) >= 40:
            sections.append((cur_h, buf))
            cur_h = stripped.lstrip("#").strip()
            buf = []
        else:
            if is_heading and not buf:
                cur_h = stripped.lstrip("#").strip()
            else:
                buf.append(stripped)
    if buf:
        sections.append((cur_h, buf))
    out: list[tuple[str, str]] = []
    for h, b in sections:
        body = "".join(b)
        body = re.sub(r"\s+", "", body)
        if len(body) >= 40:
            out.append((h, body))
    return out


def chunk_body(body: str, min_len: int = 80, max_len: int = 600) -> list[str]:
    if len(body) <= max_len:
        return [body] if len(body) >= min_len else []
    parts = re.split(r"(?<=[。！？；])", body)
    chunks: list[str] = []
    buf = ""
    for p in parts:
        if not p:
            continue
        if len(buf) + len(p) <= max_len:
            buf += p
        else:
            if len(buf) >= min_len:
                chunks.append(buf)
            buf = p
    if len(buf) >= min_len:
        chunks.append(buf)
    return chunks


def stable_id(book: str, heading: str, passage: str) -> str:
    h = hashlib.sha1(normalize(passage).encode("utf-8")).hexdigest()[:10]
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", heading)[:24] or "sec"
    return f"auto.{book}.{slug}.{h}"


def in_base(passage: str, base_norm: str) -> bool:
    pn = normalize(passage)
    return len(pn) >= 40 and pn in base_norm


def append_spotcheck_rows(rows: list[tuple[str, str, str]]) -> None:
    if not rows:
        return
    if not SPOTCHECK.exists():
        SPOTCHECK.write_text("# spotcheck\n\n| id | loc | batch | source | status |\n|----|-----|-------|--------|--------|\n", encoding="utf-8")
    existing = SPOTCHECK.read_text(encoding="utf-8")
    lines = []
    for cid, source, status in rows:
        if cid in existing:
            continue
        lines.append(f"| {cid} | — | autopilot-substr | {source} | {status} |")
    if lines:
        with SPOTCHECK.open("a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")


def upgrade_existing(items: list[dict], bases: dict[str, tuple[str, str]]) -> int:
    n = 0
    spot: list[tuple[str, str, str]] = []
    norms = {b: normalize(t) for b, (t, _) in bases.items()}
    for it in items:
        b = book_of(it.get("title"))
        if not b or b not in norms:
            continue
        if it.get("verification_status") == "verified":
            continue
        passage = it.get("passage") or ""
        if in_base(passage, norms[b]):
            it["verification_status"] = "verified"
            note = it.get("notes") or ""
            flag = "[autopilot-substr]"
            if flag not in note:
                it["notes"] = (note + " " + flag).strip()
            it["source_ref"] = bases[b][1]
            n += 1
            spot.append((it["id"], bases[b][1], "verified"))
    append_spotcheck_rows(spot)
    return n


def coverage_snapshot(items: list[dict]) -> dict:
    by_book: dict[str, list[dict]] = defaultdict(list)
    for it in items:
        b = book_of(it.get("title"))
        if b:
            by_book[b].append(it)
    books = {}
    for b in CANON:
        xs = by_book.get(b, [])
        v = sum(1 for x in xs if x.get("verification_status") == "verified")
        books[b] = {"total": len(xs), "verified": v, "gate": GATES[b], "deficit": max(0, GATES[b] - v)}
    matrix = {}
    for cat, owners in {
        "C-调候": ("穷通宝鉴", "三命通会"),
        "C-日主": ("渊海子平", "三命通会", "滴天髓"),
    }.items():
        cells = {}
        for b in owners:
            cells[b] = any(
                item_hits_category(x, cat) and x.get("verification_status") == "verified"
                for x in by_book.get(b, [])
            )
        matrix[cat] = cells
    return {"books": books, "matrix": matrix}


def gap_needed(items: list[dict], book: str, cat: str | None, kind: str) -> int:
    snap = coverage_snapshot(items)
    if kind == "matrix" and cat:
        # 至少 1
        owners = snap["matrix"].get(cat, {})
        if owners.get(book):
            return 0
        return 1
    return snap["books"][book]["deficit"]


def fill_from_base(
    items: list[dict],
    book: str,
    base_text: str,
    source_note: str,
    prefer_cat: str | None,
    need: int,
) -> int:
    if need <= 0 or not base_text:
        return 0
    author, dynasty = BOOK_META[book]
    base_norm = normalize(base_text)
    seen_ids = {it["id"] for it in items}
    seen_pass = {normalize(it.get("passage") or "") for it in items}
    added = 0
    sections = split_sections(base_text)
    # 调候优先：含季节/月令的节
    if prefer_cat == "C-调候":
        sections = sorted(
            sections,
            key=lambda x: (
                0
                if any(k in x[0] + x[1][:80] for k in ("春", "夏", "秋", "冬", "正月", "月", "余寒", "调候", "总论"))
                else 1
            ),
        )
    if prefer_cat == "C-日主":
        sections = sorted(
            sections,
            key=lambda x: (0 if any(k in x[0] for k in ("日主", "论甲", "论乙", "甲木", "十干")) else 1),
        )

    for heading, body in sections:
        for chunk in chunk_body(body):
            if added >= need:
                return added
            if not in_base(chunk, base_norm):
                # chunk 已取自 base，规范化后应可命中；若因标点差异失败则跳过极碎片
                if normalize(chunk) not in base_norm:
                    continue
            cid = stable_id(book, heading, chunk)
            pn = normalize(chunk)
            if cid in seen_ids or pn in seen_pass:
                continue
            tags = infer_tags(heading, chunk, prefer_cat)
            items.append(
                {
                    "id": cid,
                    "title": f"《{book}》·{heading}",
                    "author": author,
                    "dynasty": dynasty,
                    "tags": tags,
                    "passage": chunk,
                    "notes": f"autopilot chunk from {source_note}",
                    "verification_status": "verified",
                    "source_ref": source_note,
                }
            )
            seen_ids.add(cid)
            seen_pass.add(pn)
            append_spotcheck_rows([(cid, source_note, "verified")])
            added += 1
    return added


def _load_coverage_mod():
    import importlib.util

    path = ROOT / "scripts" / "report_five_classics_coverage.py"
    spec = importlib.util.spec_from_file_location("report_five_classics_coverage", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load coverage script")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def run_round(items: list[dict], bases: dict[str, tuple[str, str]], book_filter: set[str] | None) -> dict:
    upgraded = upgrade_existing(items, bases)
    filled = 0
    actions = []
    for book, cat, kind in PRIORITY_TARGETS:
        if book_filter and book not in book_filter:
            continue
        text, note = bases.get(book, ("", "missing"))
        if len(normalize(text)) < 200:
            actions.append({"book": book, "blocker": note})
            continue
        need = gap_needed(items, book, cat, kind)
        if need <= 0:
            continue
        # 每轮每目标配额：矩阵小步、冲数量可大步
        quota = min(need, 8 if kind == "matrix" else 30)
        n = fill_from_base(items, book, text, note, cat, quota)
        filled += n
        actions.append({"book": book, "cat": cat, "kind": kind, "need": need, "added": n})
        if n and kind == "matrix":
            break
    return {"upgraded": upgraded, "filled": filled, "actions": actions}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-rounds", type=int, default=8)
    ap.add_argument("--books", default="", help="逗号分隔书名过滤")
    args = ap.parse_args()
    book_filter = {b.strip() for b in args.books.split(",") if b.strip()} or None

    want_books = list(book_filter) if book_filter else list(CANON)
    bases = ensure_bases(want_books)
    items = load_classics()
    history = []
    for r in range(1, args.max_rounds + 1):
        stats = run_round(items, bases, book_filter)
        save_classics(items)
        cov = _load_coverage_mod()
        report = cov.build_report(items)
        cov.DEFAULT_JSON.parent.mkdir(parents=True, exist_ok=True)
        cov.DEFAULT_JSON.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        after = coverage_snapshot(items)
        history.append({"round": r, "stats": stats, "after": after})
        print(f"\n=== round {r} upgraded={stats['upgraded']} filled={stats['filled']} ===")
        for b, row in after["books"].items():
            print(f"  {b}: verified={row['verified']}/{row['gate']} (deficit {row['deficit']})")
        if stats["upgraded"] == 0 and stats["filled"] == 0:
            print("no progress — stop")
            break
        if report["milestones"]["M3_all_gates"]:
            print("M3 all gates met")
            break

    cov = _load_coverage_mod()
    final_report = cov.build_report(items)
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "history": history,
        "final": coverage_snapshot(items),
        "m3": bool(final_report["milestones"]["M3_all_gates"]),
        "milestones": final_report["milestones"],
    }
    REPORT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nWrote {REPORT_JSON}")
    print(cov.render_text(final_report))
    if payload["m3"]:
        return 0
    if history and history[-1]["stats"]["upgraded"] == 0 and history[-1]["stats"]["filled"] == 0:
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
