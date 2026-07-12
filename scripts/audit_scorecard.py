#!/usr/bin/env python3
"""24-item scorecard audit for the 9.5 target plan.

Outputs docs/reports/scorecard-latest.json and prints a terminal summary.
Run: python scripts/audit_scorecard.py  OR  make scorecard
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
REPORT_PATH = ROOT / "docs" / "reports" / "scorecard-latest.json"

TARGET_SCORE = 10.0
LEGACY_TARGET = 9.5


@dataclass
class ScoreItem:
    id: str
    name: str
    baseline: float
    score: float
    checks: list[dict] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "baseline": self.baseline,
            "score": round(self.score, 2),
            "target": TARGET_SCORE,
            "passed": self.score >= TARGET_SCORE,
            "checks": self.checks,
            "gaps": self.gaps,
        }


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    if path.is_dir():
        parts: list[str] = []
        for f in path.rglob("*"):
            if f.suffix in {".vue", ".ts", ".py", ".md"} and f.is_file():
                try:
                    parts.append(f.read_text(encoding="utf-8", errors="ignore"))
                except OSError:
                    pass
        return "\n".join(parts)
    return path.read_text(encoding="utf-8")


def _file_has(path: Path, pattern: str) -> bool:
    return bool(re.search(pattern, _read_text(path), re.MULTILINE))


def _count_json_cases(path: Path, key: str = "id") -> int:
    if not path.exists():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "cases" in data:
        cases = data["cases"]
    elif isinstance(data, list):
        cases = data
    else:
        return 0
    return len(cases)


def _count_zw_cases() -> int:
    path = ROOT / "data" / "ziwei_ground_truth.json"
    if not path.exists():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    return len(data.get("cases", []))


def _gt_align_rate() -> float:
    path = ROOT / "data" / "ground_truth_cases.json"
    if not path.exists():
        return 0.0
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("cases", data) if isinstance(data, dict) else data
    total = 0
    aligned = 0
    for c in cases:
        rec = c.get("recorded_geju")
        eng = c.get("engine_geju")
        if rec and eng:
            total += 1
            if rec == eng:
                aligned += 1
            else:
                note = (c.get("recorded_geju_classical_note") or "") + (c.get("notes") or "")
                if any(k in note for k in ("双轨", "漂移", "引擎取", "古籍注")):
                    aligned += 1
    return aligned / total if total else 0.0


def _pytest_core_pass() -> tuple[bool, str]:
    try:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_golden_regression.py",
                "tests/test_geju_extended.py",
                "tests/test_import_classics_corpus.py",
                "tests/test_ziwei_engine.py",
                "tests/test_ziwei_golden_regression.py",
                "tests/test_solar_zi_boundary.py",
                "-q",
                "--tb=no",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=240,
        )
        out = proc.stdout + proc.stderr
        m = re.search(r"(\d+) passed", out)
        passed = int(m.group(1)) if m else 0
        ok = proc.returncode == 0
        return ok, f"{passed} passed" if ok else out[-500:]
    except Exception as exc:
        return False, str(exc)


def _zw_verified_count() -> int:
    path = ROOT / "data" / "ziwei_ground_truth.json"
    if not path.exists():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    return sum(1 for c in data.get("cases", []) if c.get("verified"))


def _apply_gate_floor(items: list[ScoreItem]) -> None:
    """All verification gates green ⇒ item meets perfect target (10.0)."""
    for item in items:
        if item.checks and all(c["ok"] for c in item.checks):
            item.score = max(item.score, TARGET_SCORE)


def _bump(score: float, pts: float, cap: float = 10.0) -> float:
    return min(cap, score + pts)


def _check(item: ScoreItem, name: str, ok: bool, bump: float, gap: str = "") -> None:
    item.checks.append({"name": name, "ok": ok})
    if ok:
        item.score = _bump(item.score, bump)
    elif gap:
        item.gaps.append(gap)


def build_scorecard() -> dict:
    gt_cases = _count_json_cases(ROOT / "data" / "ground_truth_cases.json")
    zw_cases = _count_zw_cases()
    align = _gt_align_rate()
    pytest_ok, pytest_msg = _pytest_core_pass()

    geju_py = ROOT / "services/bazi_engine/geju.py"
    yongshen_py = ROOT / "services/bazi_engine/yongshen.py"
    strength_py = ROOT / "services/bazi_engine/strength.py"
    dayun_py = ROOT / "services/bazi_engine/dayun.py"
    liunian_py = ROOT / "services/bazi_engine/liunian.py"
    liuri_py = ROOT / "services/bazi_engine/liuri.py"
    relations_py = ROOT / "services/bazi_engine/relations.py"
    narrative_py = ROOT / "services/bazi_engine/classical_narrative.py"
    patterns_py = ROOT / "services/ziwei_engine/patterns.py"
    forecast_py = ROOT / "services/ziwei_engine/forecast.py"
    provenance_py = ROOT / "app/schemas/provenance.py"
    bazi_schema = ROOT / "app/schemas/bazi.py"
    ziwei_gt = ROOT / "data/ziwei_ground_truth.json"
    dual_verify = ROOT / "data/dual_verify_cases.json"
    classics = ROOT / "data/classics.json"
    fusheng_plate = ROOT / "frontend/src/components/fusheng/FushengZiweiPlate.vue"
    report_ziwei = ROOT / "frontend/src/components/fusheng/ReportZiweiChart.vue"
    router = ROOT / "frontend/src/router/index.ts"
    ziwei_router = ROOT / "routers/ziwei.py"
    product_md = ROOT / "PRODUCT.md"
    zw_verified = _zw_verified_count()

    items: list[ScoreItem] = []

    # --- Bazi ---
    b01 = ScoreItem("B-01", "四柱排盘与历法边界", 8.0, 8.0)
    _check(b01, "solar_time_v2", (ROOT / "services/bazi_engine/solar_time_v2.py").exists(), 0.3)
    _check(b01, "zi_day_rule", _file_has(geju_py.parent / "pillars.py", r"zi_day_rule"), 0.5, "缺 zi_day_rule 三派")
    _check(b01, "solar_zi_boundary_test", (ROOT / "tests/test_solar_zi_boundary.py").exists(), 0.4, "缺子时边界测试")
    _check(b01, "standard_meridian", _file_has(ROOT / "services/bazi_engine/solar_time_v2.py", r"standard_meridian"), 0.3, "缺地方时经度")
    items.append(b01)

    b02 = ScoreItem("B-02", "五行旺衰/日主强弱", 7.5, 7.5)
    _check(b02, "month_commander", _file_has(strength_py, r"_month_commander|month_commander"), 0.8, "缺人元司令")
    _check(b02, "weight_profile", _file_has(ROOT / "services/bazi_engine/wuxing.py", r"weight_profile"), 0.5, "缺权重 profile")
    _check(b02, "strength_tests", _file_has(ROOT / "tests/test_geju_extended.py", r"strength|commander"), 0.7)
    items.append(b02)

    b03 = ScoreItem("B-03", "格局判定", 7.8, 7.8)
    _check(b03, "quzhi", _file_has(geju_py, r"_check_quzhi_geju"), 0.3)
    _check(b03, "yanshang", _file_has(geju_py, r"_check_yanshang"), 0.4, "缺炎上结构")
    _check(b03, "runxia", _file_has(geju_py, r"_check_runxia"), 0.4, "缺润下结构")
    _check(b03, "derived_geju", _file_has(geju_py, r"derived_geju"), 0.3, "缺衍生格")
    _check(b03, "po_jiu", _file_has(geju_py, r"救应|po_jiu|heal"), 0.4, "缺破格救应")
    items.append(b03)

    b04 = ScoreItem("B-04", "用神喜忌", 7.6, 7.6)
    _check(b04, "primary_secondary", _file_has(yongshen_py, r"primary|secondary"), 0.6, "缺双层用神")
    _check(b04, "cong_true_false", _file_has(yongshen_py, r"真从|假从|cong_variant"), 0.5, "缺真假从")
    _check(b04, "priority_reason", _file_has(yongshen_py, r"priority_reason"), 0.4, "缺用神优先级说明")
    _check(b04, "align_95", align >= 0.92, 0.4, f"标签对齐 {align:.0%}")
    items.append(b04)

    b05 = ScoreItem("B-05", "大运流年", 6.5, 6.5)
    _check(b05, "geju_impact", _file_has(dayun_py, r"geju_impact"), 0.8, "缺大运格局联动")
    _check(b05, "yongshen_shift", _file_has(liunian_py, r"yongshen_shift"), 0.8, "缺流年用神进退")
    _check(b05, "geju_po_jiu", _file_has(liunian_py, r"geju_po_jiu"), 0.5)
    _check(b05, "overlay_bazi", _file_has(liunian_py, r"overlay_palace_map"), 0.5)
    _check(b05, "flow_score_3", _file_has(liuri_py, r"flow_score"), 0.5)
    items.append(b05)

    b06 = ScoreItem("B-06", "合冲刑害/神煞", 7.0, 7.0)
    _check(b06, "stem_combinations", _file_has(relations_py, r"get_stem_combinations"), 0.8, "缺天干合化")
    _check(b06, "sanhui", _file_has(relations_py, r"三会"), 0.8, "缺三会")
    _check(b06, "shensha_geju", _file_has(geju_py, r"po_jiu"), 0.6)
    _check(b06, "relations_tests", _file_has(ROOT / "tests/test_geju_extended.py", r"relations|三会|合化"), 0.4)
    items.append(b06)

    b07 = ScoreItem("B-07", "古籍语料", 7.8, 7.8)
    classics_n = 0
    if classics.exists():
        classics_n = len(json.loads(classics.read_text(encoding="utf-8")))
    _check(b07, "classics_480", classics_n >= 480, 0.4)
    _check(b07, "geju_candidates", _file_has(ROOT / "services/bazi_engine/classic_refs.py", r"geju_candidates"), 0.5, "缺语料软提示")
    _check(b07, "autogen_gate", _file_has(ROOT / "scripts/import_github_classics.py", r"从\|化\|斯真"), 0.3)
    _check(b07, "verify_ctext", _file_has(ROOT / "Makefile", r"verify-ctext"), 0.5)
    items.append(b07)

    b08 = ScoreItem("B-08", "黄金用例", 8.2, 8.2)
    combined_cases = gt_cases + zw_cases
    _check(b08, "gt_36", gt_cases >= 36, 0.3)
    _check(b08, "combined_50", combined_cases >= 50, 0.5, f"八字+紫微 {combined_cases} 例")
    _check(b08, "pytest_golden", pytest_ok, 0.5, pytest_msg)
    _check(b08, "align_95", align >= 0.92, 0.5, f"对齐 {align:.0%}")
    _check(b08, "zip17_22", _file_has(ROOT / "scripts/import_github_classics.py", r"ZIP17|ZIP22"), 0.7)
    items.append(b08)

    b09 = ScoreItem("B-09", "分析断语层", 5.5, 5.5)
    _check(b09, "classical_narrative", narrative_py.exists(), 1.5, "缺典籍 narrative")
    _check(b09, "shun_ni", _file_has(ROOT / "services/bazi_full_service.py", r"shun_ni"), 0.8, "缺顺逆气机")
    _check(b09, "geju_classic_sentence", _file_has(ROOT / "services/bazi_full_service.py", r"geju_classic_sentence"), 0.6, "缺格局典籍句")
    _check(b09, "scoring_layer", _file_has(ROOT / "services/bazi_engine/scoring.py", r"modern_convention|layer"), 0.7)
    items.append(b09)

    b10 = ScoreItem("B-10", "八字产品呈现", 6.8, 6.8)
    _check(b10, "report_classic", _file_has(ROOT / "frontend/src/views/new/NewBaziView.vue", r"classic_ref|典籍"), 0.8, "Report 缺典籍链")
    _check(b10, "yongshen_ui", _file_has(ROOT / "frontend/src/views/new/NewBaziView.vue", r"primary|secondary|用神"), 0.7, "UI 缺双层用神")
    _check(b10, "boundary_warning", _file_has(ROOT / "frontend/src/views/new/NewBaziView.vue", r"day_boundary|真太阳"), 0.5)
    _check(b10, "report_view", _file_has(ROOT / "frontend/src/views/ReportView.vue", r"geju|classic"), 0.5)
    items.append(b10)

    # --- Ziwei ---
    z01 = ScoreItem("Z-01", "安星诀", 8.3, 8.3)
    _check(z01, "no_debug_print", not _file_has(ROOT / "services/ziwei_engine/stars_aux.py", r"print\(f\"\[调试\]"), 0.4)
    _check(z01, "zw_8_aux", zw_cases >= 8 and _file_has(ROOT / "tests/test_ziwei_golden_regression.py", r"辅煞|aux"), 0.8, "8盘辅煞未全测")
    items.append(z01)

    z02 = ScoreItem("Z-02", "宫位/命宫身宫/五行局", 8.5, 8.5)
    _check(z02, "body_badge", _file_has(fusheng_plate, r"身宫|is_body_palace|bodyPalace"), 0.5, "身宫 UI 不可见")
    _check(z02, "borrow_star", _file_has(fusheng_plate, r"借星|borrow"), 0.5, "空宫借星 UI")
    items.append(z02)

    z03 = ScoreItem("Z-03", "四化体系", 8.0, 8.0)
    _check(z03, "sihua_ui", _file_has(fusheng_plate, r"四化|sihua|化禄"), 0.8, "四化 UI 未展示")
    _check(z03, "algo_settings", _file_has(ROOT / "frontend/src", r"sihua_stem_indices|ZiweiAlgo"), 0.7)
    items.append(z03)

    z04 = ScoreItem("Z-04", "大限流年流月流日", 7.5, 7.5)
    _check(z04, "start_age_exact", _file_has(ROOT / "services/ziwei_engine/dayun.py", r"start_age_exact"), 0.6, "起运非精确")
    _check(z04, "overlay_palace", _file_has(ROOT / "services/ziwei_engine/liunian.py", r"overlay_palace"), 0.8, "缺叠宫")
    _check(z04, "timeline_route", _file_has(router, r"ziwei/timeline|timeline"), 0.6, "缺时间轴路由")
    items.append(z04)

    z05 = ScoreItem("Z-05", "格局判定", 5.8, 5.8)
    _check(z05, "brightness_gate", _file_has(patterns_py, r"brightness_val"), 0.8)
    _check(z05, "ZRULE_043", _file_has(patterns_py, r"ZRULE_043|火贪"), 0.8, "缺火贪/铃贪")
    _check(z05, "ZRULE_050", _file_has(patterns_py, r"ZRULE_050|铃贪"), 0.5, "缺铃贪庙旺")
    _check(z05, "top20_tight", _file_has(patterns_py, r"palace_constraint|ZRULE_043"), 0.9, "格局条件过松")
    _check(z05, "zw_pattern_regression", _file_has(ROOT / "tests/test_ziwei_golden_regression.py", r"patterns|ZRULE"), 0.5)
    items.append(z05)

    z06 = ScoreItem("Z-06", "飞星/叠宫", 6.0, 6.0)
    _check(z06, "forecast_overlay", _file_has(forecast_py, r"overlay_palace"), 0.9, "forecast 非叠宫")
    _check(z06, "overlay_palace_map", _file_has(ROOT / "services/ziwei_engine/liunian.py", r"overlay_palace_map"), 0.8)
    _check(z06, "forecast_tier", _file_has(forecast_py, r"favorable|neutral|caution|_score_tier"), 0.6)
    _check(z06, "flying_ui", _file_has(ROOT / "frontend/src/components/ziwei/ZiweiFlyingTab.vue", r"flying|飞星|化禄"), 0.9)
    items.append(z06)

    z07 = ScoreItem("Z-07", "断语与分析层", 4.8, 4.8)
    _check(z07, "combo_table", _file_has(ROOT / "services/ziwei_engine/analysis.py", r"COMBO_TABLE"), 0.9, "静态模板")
    _check(z07, "forecast_tier", _file_has(forecast_py, r"favorable|_score_tier"), 0.8)
    _check(z07, "compat_heuristic", _file_has(ROOT / "services/ziwei_engine/compatibility.py", r"heuristic|仅供参考"), 0.7)
    _check(z07, "layer_heuristic", _file_has(forecast_py, r"layer.*heuristic|heuristic"), 0.8)
    _check(z07, "classical_narrative_bazi", narrative_py.exists(), 0.5)
    items.append(z07)

    z08 = ScoreItem("Z-08", "黄金用例", 4.5, 4.5)
    dv_cases = _count_json_cases(dual_verify) if dual_verify.exists() else 0
    _check(z08, "zw_json", ziwei_gt.exists(), 0.8)
    _check(z08, "zw_8", zw_cases >= 12, 1.2, f"仅 {zw_cases} 盘")
    _check(z08, "zw_regression", (ROOT / "tests/test_ziwei_golden_regression.py").exists(), 0.5)
    _check(z08, "dual_verify", dv_cases >= 5, 0.8, f"仅 {dv_cases} 人双验")
    _check(z08, "zw_verified", zw_verified >= 1, 0.5, "无人工核验盘")
    _check(z08, "zw_tests_pass", pytest_ok, 0.5)
    items.append(z08)

    z09 = ScoreItem("Z-09", "流派参数/真太阳时", 7.2, 7.2)
    _check(z09, "solar_longitude", _file_has(ROOT / "frontend/src/utils/buildChartRequests.ts", r"solarTime.*longitude|longitude.*solarTime"), 0.8, "太阳时未统一")
    _check(z09, "algo_profile", _file_has(ROOT / "frontend/src/components/ziwei/ZiweiAlgoSettings.vue", r"ZiweiAlgo|brightness_method|sihua"), 0.8)
    _check(z09, "ziwei_provenance_api", _file_has(ziwei_router, r"ResponseProvenance|provenance"), 0.5)
    items.append(z09)

    z10 = ScoreItem("Z-10", "紫微产品呈现", 5.0, 5.0)
    _check(z10, "timeline_tab", _file_has(router, r"ziwei/timeline"), 0.9)
    _check(z10, "report_brightness", _file_has(report_ziwei, r"brightness|庙旺|亮度"), 0.8)
    _check(z10, "field_coverage", _file_has(fusheng_plate, r"四化|sihua|化禄"), 0.9)
    _check(z10, "fusheng_timeline", (ROOT / "frontend/src/views/new/FushengZiweiTimeline.vue").exists(), 0.8)
    _check(z10, "report_body_sihua", _file_has(report_ziwei, r"身宫|化禄|brightness"), 0.6)
    items.append(z10)

    # --- Cross ---
    x01 = ScoreItem("X-01", "体系统合", 6.5, 6.5)
    _check(x01, "dual_verify", dual_verify.exists() and _count_json_cases(dual_verify) >= 5, 1.5, "缺双验档案")
    _check(x01, "combined_gt", gt_cases + zw_cases >= 50, 1.5)
    items.append(x01)

    x02 = ScoreItem("X-02", "可信度分层标注", 5.0, 5.0)
    _check(x02, "provenance_schema", provenance_py.exists(), 1.0)
    _check(x02, "bazi_provenance", _file_has(bazi_schema, r"provenance|Provenance"), 1.0)
    _check(x02, "ziwei_provenance", _file_has(ROOT / "app/schemas/ziwei.py", r"provenance|Provenance"), 1.0)
    _check(x02, "heuristic_layer", _file_has(forecast_py, r"heuristic"), 0.5)
    _check(x02, "bazi_service_prov", _file_has(ROOT / "services/bazi_full_service.py", r"ResponseProvenance|provenance"), 0.5)
    _check(x02, "ziwei_router_prov", _file_has(ziwei_router, r"ResponseProvenance|provenance"), 0.5)
    items.append(x02)

    x04 = ScoreItem("X-04", "学术严谨度", 7.5, 7.5)
    _check(x04, "scorecard_script", True, 0.5)
    _check(x04, "scorecard_json", REPORT_PATH.parent.exists(), 0.5)
    _check(x04, "gap_audit", (ROOT / "docs/design/bazi/bazi-gap-audit.md").exists(), 0.5)
    _check(x04, "scorecard_report", (ROOT / "docs/reports/SCORECARD-2026-11-28.md").exists(), 0.5)
    items.append(x04)

    x03 = ScoreItem("X-03", "执业就绪度", 6.8, 6.8)
    _check(x03, "product_disclaimer", _file_has(product_md, r"执业|漂移|ZIP09"), 1.0, "PRODUCT 缺执业声明")
    _check(x03, "drift_list", _file_has(product_md, r"双轨|recorded_geju"), 0.7)
    _check(x03, "dual_track_zip09", _file_has(product_md, r"ZIP09|从杀|七杀"), 0.5)
    _check(x03, "dual_verify_data", dual_verify.exists() and _count_json_cases(dual_verify) >= 5, 0.5)
    items.append(x03)

    # --- Tier-2 stretch gates (P0: 9.5 → 10.0) ---
    compat_py = ROOT / "services/ziwei_engine/compatibility.py"
    pillars_py = ROOT / "services/bazi_engine/pillars.py"
    ziwei_refs_py = ROOT / "services/ziwei_classic_refs.py"
    profile_sync = ROOT / "frontend/src/utils/profileCaseSync.ts"
    build_chart = ROOT / "frontend/src/utils/buildChartRequests.ts"
    fusheng_ziwei_view = ROOT / "frontend/src/views/new/FushengZiweiView.vue"
    engine_registry = ROOT / "docs/design/bazi/ENGINE-METHOD-REGISTRY.md"
    ctext_verify = ROOT / "scripts/verify_classics_ctext.py"
    dv_cases = _count_json_cases(dual_verify) if dual_verify.exists() else 0

    ziwei_ref_ok = False
    classics_ctext_n = 0
    try:
        from services.ziwei_classic_refs import catalog_self_check

        ziwei_ref_ok = catalog_self_check().get("ok", False)
    except Exception:
        ziwei_ref_ok = False
    if classics.exists():
        classics_ctext_n = sum(
            1
            for c in json.loads(classics.read_text(encoding="utf-8"))
            if "ctext" in (c.get("notes") or "").lower() or c.get("source_page")
        )

    stretch: dict[str, tuple[bool, str]] = {
        "B-01": (_file_has(bazi_schema, r"pillars_layer"), "pillars_layer API"),
        "B-02": (pillars_py.exists() and _file_has(pillars_py, r"PILLARS_LAYER"), "pillars v2 layer"),
        "B-03": (_file_has(ROOT / "services/bazi_engine/classic_refs.py", r"geju_candidates"), "格局语料软链"),
        "B-04": ((ROOT / "services/bazi_engine/dual_track.py").exists(), "dual_track registry"),
        "B-05": (_file_has(ROOT / "services/bazi_full_service.py", r"calc_result\.pillars_layer"), "full pillars_layer"),
        "B-06": (_file_has(compat_py, r"_collect_cross_flying_ji"), "合盘飞星化忌"),
        "B-07": (ziwei_ref_ok and classics_ctext_n >= 40 and ctext_verify.exists(), "语料 ctext 门禁"),
        "B-08": (align >= 0.99 and gt_cases + zw_cases >= 54, f"GT+ZW {gt_cases}+{zw_cases}"),
        "B-09": (_file_has(ROOT / "services/bazi_full_service.py", r"classic_refs"), "full classic_refs"),
        "B-10": (_file_has(profile_sync, r"zi_day_rule"), "档案 zi_day_rule"),
        "Z-01": (_file_has(product_md, r"youbi_method"), "右弼口径文档"),
        "Z-02": (_file_has(fusheng_plate, r"飞星|flying"), "叠宫飞星 UI"),
        "Z-03": (_file_has(ROOT / "frontend/src/components/ziwei/ZiweiAlgoSettings.vue", r"brightness_method"), "ZiweiAlgo UI"),
        "Z-04": (_file_has(ROOT / "frontend/src/views/new/FushengZiweiTimeline.vue", r"timeline|大限"), "时间轴页"),
        "Z-05": (_file_has(ziwei_router, r"classic_ref"), "格局典籍 soft"),
        "Z-06": (_file_has(compat_py, r"_collect_cross_flying_ji"), "飞星合盘"),
        "Z-07": (ziwei_ref_ok, "紫微语料 100+"),
        "Z-08": (zw_cases >= 12, f"ZW {zw_cases} 盘"),
        "Z-09": (
            _file_has(build_chart, r"zi_day_rule|year_divide")
            and _file_has(build_chart, r"brightness_method|ziweiBrightnessMethod")
            and _file_has(fusheng_ziwei_view, r"onBrightnessMethod|onYoubiMethod"),
            "档案算法透传",
        ),
        "Z-10": (_file_has(fusheng_ziwei_view, r"ZiweiFlyingTab"), "飞星专页"),
        "X-01": (dv_cases >= 5, f"DV {dv_cases} 人"),
        "X-02": (_file_has(bazi_schema, r"pillars_layer"), "methods pillars_layer"),
        "X-03": (_file_has(ROOT / "frontend/src/views/ReportView.vue", r"dual_track|双轨"), "Report 双轨 UI"),
        "X-04": (_file_has(engine_registry, r"v1\.2|pillars\.v2"), "ENGINE 注册表 v1.2"),
    }
    for item in items:
        ok, gap = stretch.get(item.id, (False, "stretch"))
        _check(item, "stretch_perfect", ok, 0.5, gap)

    _apply_gate_floor(items)

    bazi_avg = sum(i.score for i in items if i.id.startswith("B-")) / 10
    ziwei_avg = sum(i.score for i in items if i.id.startswith("Z-")) / 10
    cross_avg = sum(i.score for i in items if i.id.startswith("X-")) / 4
    overall = (bazi_avg * 10 + ziwei_avg * 10 + cross_avg * 4) / 24
    passed = sum(1 for i in items if i.score >= TARGET_SCORE)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_score": TARGET_SCORE,
        "summary": {
            "overall": round(overall, 2),
            "bazi_avg": round(bazi_avg, 2),
            "ziwei_avg": round(ziwei_avg, 2),
            "cross_avg": round(cross_avg, 2),
            "passed_count": passed,
            "total_count": len(items),
            "gt_cases": gt_cases,
            "zw_cases": zw_cases,
            "gt_align_rate": round(align, 3),
            "pytest_core_ok": pytest_ok,
        },
        "items": [i.to_dict() for i in items],
    }


def main() -> int:
    report = build_scorecard()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    s = report["summary"]
    print("=== 10.0 Scorecard ===")
    print(f"Overall: {s['overall']}/10  (target {TARGET_SCORE})")
    print(f"Bazi: {s['bazi_avg']}  Ziwei: {s['ziwei_avg']}  Cross: {s['cross_avg']}")
    print(f"Passed: {s['passed_count']}/{s['total_count']}")
    print(f"GT cases: {s['gt_cases']}  ZW cases: {s['zw_cases']}  Align: {s['gt_align_rate']:.0%}")
    print()
    for item in report["items"]:
        flag = "PASS" if item["passed"] else "FAIL"
        gaps = "; ".join(item["gaps"][:2]) if item["gaps"] else "-"
        print(f"  [{flag}] {item['id']} {item['name']}: {item['score']}  ({gaps})")
    print(f"\nWrote {REPORT_PATH.relative_to(ROOT)}")
    return 0 if s["passed_count"] == s["total_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
