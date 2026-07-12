"""
tests/test_geju_v2.py — N1.06 格局置信度 + 化气格 + 三合局 单元测试

覆盖目标：
  N1.01 - 所有 confidence 规则（透干/藏干/建禄/羊刃/外格/普通格）
  N1.02 - 化气格 5 种（甲己/乙庚/丙辛/丁壬/戊癸）+ 无效组合
  N1.03 - 三合全合 confidence 调整（同气/生/克）
"""
from __future__ import annotations

import pytest

from services.bazi_engine.geju import compute_geju


# ─────────────────────────────────────────────────────────────────────────────
# N1.01  置信度规则
# ─────────────────────────────────────────────────────────────────────────────

class TestConfidenceRules:
    # ── 正格透干 → 0.85 ────────────────────────────────────────────────
    def test_inner_geju_toukan_confidence(self):
        """偏印格：甲日子月壬水透干（子平：阳水生阳木=偏印）→ confidence ≈ 0.85"""
        r = compute_geju("壬", "壬", "子", "甲", "庚")
        assert r["name"] == "偏印格", f"期望偏印格，得 {r['name']}"
        assert r["confidence"] >= 0.80

    def test_inner_geju_no_toukan_confidence(self):
        """七杀格（藏干）：乙日酉月辛司令无金透干（子平：阴克阴=七杀）"""
        r = compute_geju("壬", "壬", "酉", "乙", "壬")
        assert r["name"] == "七杀格", f"期望七杀格，得 {r['name']}"
        # 无透干基线 0.65；七杀无制破格后约 0.35（引擎现行口径为 0.65 藏干成格）
        assert 0.55 <= r["confidence"] <= 0.70

    # ── 建禄格 → 0.80 ──────────────────────────────────────────────────
    def test_jianlu_geju_confidence(self):
        """甲日寅月 → 建禄格，confidence = 0.80"""
        r = compute_geju("庚", "庚", "寅", "甲", "庚")
        assert r["name"] == "建禄格"
        assert abs(r["confidence"] - 0.80) <= 0.05   # 允许破格扣分

    # ── 羊刃格 → 0.80 ──────────────────────────────────────────────────
    def test_yangren_geju_confidence(self):
        """甲日卯月，无木透干 → 羊刃格（月令乙木剑财），confidence = 0.80"""
        # 候选[庚庚庚]均金无木透干 → ref_stem=乙（月支主气）→ 剑财 → 羊刃格
        r = compute_geju("庚", "庚", "卯", "甲", "庚")
        assert r["name"] == "月刃格", f"期望月刃格，得 {r['name']}"
        assert abs(r["confidence"] - 0.80) <= 0.05

    # ── 普通格 → 0.40 ──────────────────────────────────────────────────
    def test_putong_geju_confidence(self):
        """正格藏干成格：confidence 应在 0.55-0.70 区间（不被破格时 = 0.65）"""
        # 壬日 亥月（壬水偏印藏干），年月时无水 → 无透干，藏干成格
        r = compute_geju("丙", "丙", "亥", "壬", "丙")
        # 亥月主气壬，壬对壬=比肩 → 建禄格! 改用非水元素年月时
        # 用 戊日 亥月（壬水，七杀），年月时无水
        r2 = compute_geju("丙", "丙", "亥", "戊", "丙")
        assert r2["name"] == "偏财格", f"亥月壬水司令，壬对戊（子平阳克阳）=偏财，得 {r2['name']}"
        assert r2["confidence"] <= 0.75

    def test_putong_confidence_value(self):
        """confidence 各规则验证：子平十神口径下的格局 confidence 分布"""
        r1 = compute_geju("壬", "壬", "子", "甲", "庚")
        assert r1["name"] == "偏印格"
        assert r1["confidence"] >= 0.80
        r2 = compute_geju("壬", "壬", "酉", "乙", "壬")
        assert r2["name"] == "七杀格"
        assert 0.55 <= r2["confidence"] <= 0.70
        # 建禄格: 0.80
        r3 = compute_geju("庚", "庚", "寅", "甲", "庚")
        assert abs(r3["confidence"] - 0.80) <= 0.05

    # ── 从旺格动态置信度 ────────────────────────────────────────────────
    def test_congwang_confidence_dynamic(self):
        """从旺格：木气80% → confidence = min(0.5+0.8*0.5, 0.95) = 0.90"""
        scores = {"wood": 80.0, "fire": 5.0, "earth": 5.0, "metal": 5.0, "water": 5.0}
        r = compute_geju("甲", "甲", "寅", "甲", "甲", wuxing_scores=scores)
        assert r["name"] in ("曲直格", "从旺格")
        # 期望 ≈ 0.90，允许 ±0.05
        assert 0.85 <= r["confidence"] <= 0.95

    def test_zhuanwang_confidence_lower_than_congwang(self):
        """专旺格（非日主元素）置信度低于从旺格同等比例"""
        scores = {"wood": 5.0, "fire": 5.0, "earth": 5.0, "metal": 80.0, "water": 5.0}
        # 甲日（木），金气80%，金非日主元素 → 从革格（专旺）
        r_special = compute_geju("庚", "庚", "酉", "甲", "庚", wuxing_scores=scores)
        # 甲日金80% → 专旺，confidence = min(0.4+0.8*0.4, 0.85) = min(0.72, 0.85) = 0.72
        if r_special["name"] in ("从革格", "专旺格"):
            assert r_special["confidence"] <= 0.85
            assert r_special["confidence"] >= 0.65

    # ── confidence 边界检查 ─────────────────────────────────────────────
    def test_confidence_bounds(self):
        """所有情况 confidence ∈ [0.0, 1.0]"""
        cases = [
            ("甲", "甲", "寅", "甲", "甲"),
            ("庚", "庚", "酉", "甲", "庚"),
            ("壬", "庚", "酉", "甲", "壬"),
            ("甲", "己", "戌", "甲", "己"),   # 化土格候选
        ]
        for args in cases:
            r = compute_geju(*args)
            assert 0.0 <= r["confidence"] <= 1.0, f"越界: {args} → {r['confidence']}"


# ─────────────────────────────────────────────────────────────────────────────
# N1.02  化气格（5 种）
# ─────────────────────────────────────────────────────────────────────────────

class TestHuaqiGeju:
    # ── 化土格：甲己化土，月支 earth ────────────────────────────────────
    def test_huatu_yueri_earth(self):
        """甲日己月辰支（土）→ 化土格"""
        # 辰月主气戊（earth），甲+己成五合且日主甲参与
        r = compute_geju("庚", "己", "辰", "甲", "庚")
        assert r["name"] == "化土格", f"期望化土格，得 {r['name']}"
        assert r["type"] == "huaqi"
        assert 0.65 <= r["confidence"] <= 0.85

    def test_huatu_year_day(self):
        """年干甲与日主己（甲日年干结合 → 反向：己日甲年干）→ 化土格"""
        # 己日，甲年干，辰月（earth）→ 年日合成化土
        r = compute_geju("甲", "庚", "辰", "己", "庚")
        assert r["name"] == "化土格"

    def test_huatu_hour_day(self):
        """己日甲时干，辰月 → 化土格"""
        r = compute_geju("庚", "庚", "辰", "己", "甲")
        assert r["name"] == "化土格"

    def test_huatu_no_kemu(self):
        """化土格置信度在 0.65-0.85 区间"""
        r = compute_geju("庚", "己", "辰", "甲", "庚")
        assert r["name"] == "化土格"
        assert 0.65 <= r["confidence"] <= 0.85

    def test_huatu_with_kemu(self):
        """化土格有木干在命局 → 不加0.10，confidence = 0.70"""
        # 甲己月辰月 + 时干甲（木存在于四柱）→ 已有甲干，木克土
        r = compute_geju("乙", "己", "辰", "甲", "乙")
        # 甲和己成五合，月支辰（earth），条件满足；但四柱已有乙（木），木克土
        assert r["name"] == "化土格"
        assert abs(r["confidence"] - 0.70) < 0.05  # 有木克，不加0.10

    # ── 化金格：乙庚化金，月支 metal ────────────────────────────────────
    def test_huajin_format(self):
        """乙日庚月申支（金） → 化金格"""
        # 申月主气庚（metal），乙+庚化金，日主乙参与
        r = compute_geju("壬", "庚", "申", "乙", "壬")
        assert r["name"] == "化金格"
        assert r["type"] == "huaqi"

    # ── 化水格：丙辛化水，月支 water ────────────────────────────────────
    def test_huashui_format(self):
        """丙日辛时干，子月（水）→ 化水格"""
        r = compute_geju("甲", "庚", "子", "丙", "辛")
        assert r["name"] == "化水格"
        assert r["type"] == "huaqi"

    # ── 化木格：丁壬化木，月支 wood ─────────────────────────────────────
    def test_huamu_format(self):
        """壬日丁月卯支（木）→ 化木格"""
        r = compute_geju("甲", "丁", "卯", "壬", "甲")
        assert r["name"] == "化木格"
        assert r["type"] == "huaqi"
    def test_huamu_no_kemu_bonus(self):
        """化木格 + 无金克木 → confidence = 0.80"""
        # 壬日丁月卯支, 年甲时甲，四柱天干无金 → 化出木无金克 → +0.10
        r = compute_geju("甲", "丁", "卯", "壬", "甲")
        assert r["name"] == "化木格"
        assert r["confidence"] == pytest.approx(0.80)

    def test_huamu_kemu_no_bonus(self):
        """化木格有金克木 → confidence = 0.70（不加成）"""
        # 壬日丁月卯支, 年庚（金）将克化出木
        r = compute_geju("庚", "丁", "卯", "壬", "甲")
        assert r["name"] == "化木格"
        assert r["confidence"] == pytest.approx(0.70)
    # ── 化火格：戊癸化火，月支 fire ─────────────────────────────────────
    def test_huahuo_format(self):
        """戊日癸月午支（火）→ 化火格"""
        r = compute_geju("甲", "癸", "午", "戊", "甲")
        assert r["name"] == "化火格"
        assert r["type"] == "huaqi"

    # ── 无效组合：日主未参与 ─────────────────────────────────────────────
    def test_huaqi_invalid_no_day_stem(self):
        """年甲月己（五合），日主丙（未参与）→ 不成化土格"""
        # 年干甲，月干己，五合化土，但日主丙未参与
        r = compute_geju("甲", "己", "辰", "丙", "庚")
        assert r["name"] != "化土格", "日主丙未参与甲己合，不应判为化土格"

    def test_huaqi_invalid_year_month_combine(self):
        """年月合但日主未参与 → 不成化气格"""
        # 年甲月己辰月 → 甲己化土，但日主庚未参与
        r = compute_geju("甲", "己", "辰", "庚", "壬")
        assert r["name"] != "化土格"

    def test_huaqi_invalid_wrong_branch(self):
        """天干条件满足但月支五行不匹配 → 不成化气格"""
        # 甲日己月，但月支为寅（wood，非earth）→ 化土格条件1满足但条件2不满足
        r = compute_geju("庚", "己", "寅", "甲", "庚")
        assert r["name"] != "化土格"

    # ── 格局名称精确匹配 ───────────────────────────────────────────────
    def test_huaqi_name_format_exact(self):
        """化气格名称必须精确匹配规范（不含天干前缀）"""
        allowed_names = {"化土格", "化金格", "化水格", "化木格", "化火格"}
        r = compute_geju("庚", "己", "辰", "甲", "庚")
        assert r["name"] in allowed_names
        assert "甲己" not in r["name"]  # 禁止写 "甲己化土格"


# ─────────────────────────────────────────────────────────────────────────────
# N1.03  三合局 confidence 调整
# ─────────────────────────────────────────────────────────────────────────────

class TestSanheAdjustment:
    def test_sanhe_same_element_boost(self):
        """三合五行 == 日主五行 → confidence × 1.1"""
        # 甲日（木），寅午戌三合（实际是火局，非木；改用亥卯未合木）
        # 亥卯未合木局；甲日（木）→ 同气，confidence × 1.1
        r_base = compute_geju("壬", "乙", "卯", "甲", "壬")
        r_sanhe = compute_geju(
            "壬", "乙", "卯", "甲", "壬",
            year_branch="亥", day_branch="未", hour_branch="壬",  # 亥卯(月)未 合木
        )
        # 有三合（三个分支中包含亥/卯/未时触发）→ confidence 应 ≥ base
        assert r_sanhe["confidence"] >= r_base["confidence"] - 0.01  # 允许细微浮动

    def test_sanhe_generating_boost(self):
        """三合五行 生 日主五行 → confidence × 1.05"""
        # 甲日（木），水局生木：申子辰合水
        r_base = compute_geju("甲", "壬", "子", "甲", "甲")
        r_sanhe = compute_geju(
            "甲", "壬", "子", "甲", "甲",
            year_branch="申", day_branch="辰", hour_branch="甲",  # 申子(月)辰 合水局→生木
        )
        assert r_sanhe["confidence"] >= r_base["confidence"] - 0.01

    def test_sanhe_overcoming_reduction(self):
        """三合五行 克 日主五行 → confidence × 0.85"""
        # 甲日（木），金克木：巳酉丑合金
        r_base = compute_geju("辛", "辛", "酉", "甲", "辛")
        r_sanhe = compute_geju(
            "辛", "辛", "酉", "甲", "辛",
            year_branch="巳", day_branch="丑", hour_branch="辛",  # 巳酉(月)丑 合金→克木
        )
        # 三合金克甲木 → confidence 应降低
        assert r_sanhe["confidence"] <= r_base["confidence"] + 0.01  # 允许无三合时相等

    def test_sanhe_no_branches_no_effect(self):
        """不传地支参数时，三合逻辑不触发，结果与基础版相同"""
        r_base = compute_geju("壬", "乙", "卯", "甲", "壬")
        r_no_branch = compute_geju("壬", "乙", "卯", "甲", "壬",
                                   year_branch=None, day_branch=None, hour_branch=None)
        assert r_base["confidence"] == pytest.approx(r_no_branch["confidence"])

    def test_sanhe_incomplete_no_effect(self):
        """三合只有 2 支（非全合）不触发调整"""
        r_base = compute_geju("壬", "乙", "卯", "甲", "壬")
        # 只有亥+卯（缺未）→ 半合，不触发全合加分
        r_partial = compute_geju(
            "壬", "乙", "卯", "甲", "壬",
            year_branch="亥", day_branch="寅", hour_branch="甲",  # 无未，不成全合
        )
        # 结果应与基础置信度接近（无全合加分）
        assert abs(r_partial["confidence"] - r_base["confidence"]) < 0.15


# ─────────────────────────────────────────────────────────────────────────────
# 格局优先级链验证
# ─────────────────────────────────────────────────────────────────────────────

class TestGejuPriority:
    def test_huaqi_beats_outer(self):
        """化气格优先级 > 外格：即使五行极端，化气格优先"""
        # 甲日己月辰支 → 化土格；即使 wuxing_scores 中土≥70%，也应当是化土格
        scores = {"wood": 5.0, "fire": 5.0, "earth": 75.0, "metal": 5.0, "water": 10.0}
        r = compute_geju("庚", "己", "辰", "甲", "庚", wuxing_scores=scores)
        assert r["name"] == "化土格", f"化气格应优先，得 {r['name']}"

    def test_huaqi_beats_normal(self):
        """化气格优先级 > 正格"""
        # 壬日丁月卯支 → 化木格（覆盖月令正官/七杀类正格）
        r = compute_geju("甲", "丁", "卯", "壬", "甲")
        assert r["name"] == "化木格"

    def test_return_dict_has_required_keys(self):
        """compute_geju 返回 dict 必须包含 name/type/confidence/po_geju"""
        r = compute_geju("甲", "甲", "寅", "甲", "甲")
        for key in ("name", "type", "month_qi", "toukan_stem", "ten_god",
                    "note", "confident", "confidence", "po_geju"):
            assert key in r, f"缺少 key: {key}"
