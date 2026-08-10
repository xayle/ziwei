#!/usr/bin/env python3
"""刘博样例 PDF/HTML 质量门禁：禁词、未知默认、神煞句、总结去复读。"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.schemas.fusheng_report import FushengReportPdfRequest
from services.fusheng_report_service import build_fusheng_report_payload, render_fusheng_report_html

OUT_JSON = ROOT / "docs" / "reports" / "fusheng-report-pdf-sample-check-latest.json"
OUT_HTML = ROOT / "output" / "pdf" / "regression-liubo.html"
FORBIDDEN = re.compile(r"main_match|\bL0\b|solar_next|\biztro\b", re.IGNORECASE)


def _lcs_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    # 简化：用最长公共子串长度 / min(len)
    n, m = len(a), len(b)
    if n > 4000:
        a = a[:4000]
        n = 4000
    if m > 4000:
        b = b[:4000]
        m = 4000
    prev = [0] * (m + 1)
    best = 0
    for i in range(1, n + 1):
        cur = [0] * (m + 1)
        ca = a[i - 1]
        for j in range(1, m + 1):
            if ca == b[j - 1]:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best = cur[j]
            else:
                cur[j] = 0
        prev = cur
    return best / max(1, min(n, m))


async def main() -> int:
    req = FushengReportPdfRequest(
        birth_dt="1990-07-17T12:25:00",
        lon=117.28,
        tz="Asia/Shanghai",
        gender="male",
        label="刘博 · 1990/07/17",
        surname="刘",
        given_name="博",
        city_name="徐州",
        calendar_mode="gregorian",
        birth_time_precision="exact",
        unknown_time_fallback="midday",
        year_divide="lichun",
        day_divide="solar_next",
    )
    payload = await build_fusheng_report_payload(req)
    html = render_fusheng_report_html(payload)
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")

    summary = str((payload.get("bazi") or {}).get("bazi_summary") or "")
    # 总结页正文（去掉基础档案中的摘要）
    closing_m = re.search(r"<h2>综合总结</h2>(.*?)(?:<section|</body>)", html, re.S)
    closing = re.sub(r"<[^>]+>", "", closing_m.group(1) if closing_m else "")
    trust_m = re.search(
        r"<h2>校勘与可信度</h2>(.*?)(?:<section|</body>)", html, re.S
    ) or re.search(r"<h2>引擎可信度</h2>(.*?)(?:<section|</body>)", html, re.S)
    trust_html = trust_m.group(1) if trust_m else ""
    summary_zone = re.search(r"trust-summary(.*?)(?:trust-appendix|$)", trust_html, re.S)
    summary_zone_html = summary_zone.group(1) if summary_zone else trust_html
    pct_in_summary = len(re.findall(r"=%|\d{1,3}%", summary_zone_html))
    chart_section = ""
    cm = re.search(r"<h2>八字满盘</h2>(.*?)(?:<section|</body>)", html, re.S)
    if cm:
        chart_section = re.sub(r"<[^>]+>", "", cm.group(1))
    # 空白率代理：封面外各 sheet 纯文本长度（防空壳页）
    sheets = re.findall(r'class="page sheet"[^>]*>(.*?)</section>', html, re.S)
    sheet_lens = [len(re.sub(r"<[^>]+>", "", s).strip()) for s in sheets]
    min_sheet = min(sheet_lens) if sheet_lens else 0

    checks = {
        "no_unknown_default": "未知默认" not in html,
        "human_birth_time": "1990年7月17日 12:25" in html and "1990-07-17T12:25" not in html,
        "no_forbidden_tokens": not FORBIDDEN.search(html),
        "no_empty_notes_page": "人工批注区" not in html,
        "dual_track_no_orphan_page": (
            ("本命暂无古籍双轨样例" in html and "双轨对照附录" not in html)
            or ("双轨对照附录" in html and "<table>" in html.split("双轨对照附录")[-1][:800])
        ),
        "pillars_full_chart": (
            "八字满盘" in html
            and "流年" in html
            and "大运" in html
            and "主星" in html
            and "藏干" in html
            and "空亡" in html
            and "星运" in html
        ),
        "cover_has_frame": "FUSHENG ARCHIVE" in html and "本册目录" in html,
        "archive_no_zonghe_shoushu": "综合收束" not in html.split("综合总结")[0],
        "no_xiongsha_tianyi": "凶煞有天乙" not in html and "凶煞有天乙" not in summary,
        "closing_not_copy": _lcs_ratio(summary, closing) < 0.40,
        # I01–I04 / 付费收据
        "chart_legend": "读盘图例" in html,
        "geju_or_tension": ("定格" in chart_section) or ("张力" in chart_section) or ("定格说明" in html),
        "liunian_bridge": "本年对我" in html,
        "dayun_bridge": "当前大运" in html,
        "ziwei_topics": "桃花" in html and "田宅" in html,
        "flying_plain": "飞星三分钟读法" in html,
        "closing_focus_index": ("本年焦点" in closing) or ("回看" in closing),
        "how_to_read": "本册怎么读" in html,
        "trust_no_pct_wall": pct_in_summary <= 3,
        # 主册充实；十二宫/姓名等专页可短，但禁止残页级空白
        "sheet_min_content": (
            sum(1 for n in sheet_lens if n >= 400) >= 3 and min_sheet >= 120
        ),
        "no_half_sentence_ellipsis_wall": html.count("…") < 12,
        "palace_table_complete": html.count("宫</td>") >= 12 or "紫微十二宫" in html,
        "song_sheet_frame": 'class="page sheet"' in html and "v2.7" in html,
    }
    forbidden_hits = FORBIDDEN.findall(html)
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sample": "刘博 · 1990-07-17 12:25 徐州",
        "html_path": str(OUT_HTML.relative_to(ROOT)).replace("\\", "/"),
        "checks": checks,
        "forbidden_hits": forbidden_hits[:20],
        "lcs_ratio_summary_vs_closing": round(_lcs_ratio(summary, closing), 4),
        "pct_in_trust_summary": pct_in_summary,
        "sheet_text_lens": sheet_lens,
        "min_sheet_text_len": min_sheet,
        "pass": all(checks.values()),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
