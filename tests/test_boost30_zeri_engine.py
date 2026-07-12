"""Coverage boost 30 — services/ziwei_engine/zeri_engine.py (T-07)

当前覆盖率 27%，miss=164 行。
重点覆盖：
  - _natal_wx 各五行解析
  - _stem_favor 五种生克关系
  - _branch_rel_score 三合/六合/相冲/相刑/相害/无关系
  - _virtue_score 天德/月德
  - _purpose_bonus 六种用途分支
  - _lunar_day_str 农历显示
  - recommend_month 主函数全流程
  - ZeriDayResult / ZeriMonthResult dataclass
"""
from __future__ import annotations

import pytest


# ══════════════════════════════════════════════════════════════════════════
#  导入被测模块（延迟到函数级别，确保 sxtwl 已在 path 中）
# ══════════════════════════════════════════════════════════════════════════

def _import():
    from services.ziwei_engine.zeri_engine import (
        _natal_wx,
        _stem_favor,
        _branch_rel_score,
        _virtue_score,
        _purpose_bonus,
        _lunar_day_str,
        recommend_month,
        ZeriDayResult,
        ZeriMonthResult,
        PURPOSES,
        _STEM_WX,
        _SHENG_ME,
        _I_SHENG,
        _KE_ME,
        _I_KE,
    )
    return (
        _natal_wx, _stem_favor, _branch_rel_score, _virtue_score,
        _purpose_bonus, _lunar_day_str, recommend_month,
        ZeriDayResult, ZeriMonthResult, PURPOSES,
        _STEM_WX, _SHENG_ME, _I_SHENG, _KE_ME, _I_KE,
    )


# ══════════════════════════════════════════════════════════════════════════
#  _natal_wx — 五行局解析
# ══════════════════════════════════════════════════════════════════════════

class TestNatalWx:
    def test_water(self):
        _natal_wx = _import()[0]
        assert _natal_wx("水二局") == 4

    def test_wood(self):
        _natal_wx = _import()[0]
        assert _natal_wx("木三局") == 0

    def test_gold(self):
        _natal_wx = _import()[0]
        assert _natal_wx("金四局") == 3

    def test_earth(self):
        _natal_wx = _import()[0]
        assert _natal_wx("土五局") == 2

    def test_fire(self):
        _natal_wx = _import()[0]
        assert _natal_wx("火六局") == 1

    def test_default_earth_on_unknown(self):
        _natal_wx = _import()[0]
        assert _natal_wx("未知局") == 2

    def test_empty_string_defaults_earth(self):
        _natal_wx = _import()[0]
        assert _natal_wx("") == 2


# ══════════════════════════════════════════════════════════════════════════
#  _stem_favor — 天干五行生克得分
# ══════════════════════════════════════════════════════════════════════════

class TestStemFavor:
    """验证 5 种生克关系都能触发正确得分。"""

    def test_same_element_returns_6(self):
        _natal_wx, _stem_favor = _import()[0], _import()[1]
        # 木(0) 对 木(0) → 同我 +6
        # 甲=0, 乙=1 都是木
        assert _stem_favor(0, 0) == 6  # 甲(木) vs 命主木
        assert _stem_favor(1, 0) == 6  # 乙(木) vs 命主木

    def test_sheng_me_returns_12(self):
        _stem_favor = _import()[1]
        # 水生木：命主木(0)，水(4) 生我 → +12
        # _SHENG_ME[0]=4, 壬=8(水), 癸=9(水)
        assert _stem_favor(8, 0) == 12   # 壬(水) vs 命主木
        assert _stem_favor(9, 0) == 12   # 癸(水) vs 命主木

    def test_i_sheng_returns_4(self):
        _stem_favor = _import()[1]
        # 木生火：命主木(0)，我生火(1) → +4
        # 丙=2(火), 丁=3(火)
        assert _stem_favor(2, 0) == 4   # 丙(火) vs 命主木
        assert _stem_favor(3, 0) == 4   # 丁(火) vs 命主木

    def test_ke_me_returns_neg12(self):
        _stem_favor = _import()[1]
        # 金克木：命主木(0)，金(3) 克我 → -12
        # 庚=6(金), 辛=7(金)
        assert _stem_favor(6, 0) == -12  # 庚(金) vs 命主木
        assert _stem_favor(7, 0) == -12  # 辛(金) vs 命主木

    def test_i_ke_returns_neg8(self):
        _stem_favor = _import()[1]
        # 木克土：命主木(0)，土(2) 我克 → -8
        # 戊=4(土), 己=5(土)
        assert _stem_favor(4, 0) == -8   # 戊(土) vs 命主木
        assert _stem_favor(5, 0) == -8   # 己(土) vs 命主木

    def test_all_natal_wx_covered(self):
        _stem_favor = _import()[1]
        # 命主火(1)：水克火→-12，木生火→+12，火同→+6，土受生→+4，金受克→-8
        assert _stem_favor(8, 1) == -12  # 壬(水) 克 命主火
        assert _stem_favor(0, 1) == 12   # 甲(木) 生 命主火
        assert _stem_favor(2, 1) == 6    # 丙(火) 同 命主火
        assert _stem_favor(4, 1) == 4    # 戊(土) 受生 命主火
        assert _stem_favor(6, 1) == -8   # 庚(金) 被火克 → 我克(-8)


# ══════════════════════════════════════════════════════════════════════════
#  _branch_rel_score — 地支关系评分
# ══════════════════════════════════════════════════════════════════════════

class TestBranchRelScore:
    """覆盖全部 6 种地支关系分支。"""

    def test_sanhe(self):
        _branch_rel_score = _import()[2]
        # 申(8)子(0)辰(4) 三合水局
        score, rel = _branch_rel_score(8, 0)
        assert score == 22
        assert rel == "三合"

    def test_liuhe(self):
        _branch_rel_score = _import()[2]
        # 子(0)丑(1) 六合土
        score, rel = _branch_rel_score(0, 1)
        assert score == 16
        assert rel == "六合"

    def test_chong(self):
        _branch_rel_score = _import()[2]
        # 子(0)午(6) 相冲
        score, rel = _branch_rel_score(0, 6)
        assert score == -30
        assert rel == "相冲"

    def test_xing(self):
        _branch_rel_score = _import()[2]
        # 子(0)卯(3) 相刑
        score, rel = _branch_rel_score(0, 3)
        assert score == -18
        assert rel == "相刑"

    def test_hai(self):
        _branch_rel_score = _import()[2]
        # 子(0)未(7) 相害
        score, rel = _branch_rel_score(0, 7)
        assert score == -10
        assert rel == "相害"

    def test_no_relation(self):
        _branch_rel_score = _import()[2]
        # 子(0)寅(2) 无关系
        score, rel = _branch_rel_score(0, 2)
        assert score == 0
        assert rel == ""

    def test_symmetry_sanhe(self):
        _branch_rel_score = _import()[2]
        s1, r1 = _branch_rel_score(8, 4)  # 申辰
        s2, r2 = _branch_rel_score(4, 8)  # 辰申
        assert s1 == s2
        assert r1 == r2 == "三合"

    def test_all_chong_pairs(self):
        _branch_rel_score = _import()[2]
        # 六冲对全覆盖
        chong_pairs = [(0,6),(1,7),(2,8),(3,9),(4,10),(5,11)]
        for a, b in chong_pairs:
            score, rel = _branch_rel_score(a, b)
            assert score == -30, f"pair {a},{b} should be 相冲"
            assert rel == "相冲"

    def test_all_liuhe_pairs(self):
        _branch_rel_score = _import()[2]
        liuhe_pairs = [(0,1),(2,11),(3,10),(4,9),(5,8),(6,7)]
        for a, b in liuhe_pairs:
            score, rel = _branch_rel_score(a, b)
            assert score == 16
            assert rel == "六合"


# ══════════════════════════════════════════════════════════════════════════
#  _virtue_score — 天德/月德
# ══════════════════════════════════════════════════════════════════════════

class TestVirtueScore:
    def test_tiande_digit_match(self):
        _virtue_score = _import()[3]
        # 月支=2(寅月), 天德=丁(idx=3)，丁=天干index 3
        # 若日天干=3(丁)，应加 +15
        bonus, labels = _virtue_score(3, 0, 2)
        assert bonus >= 15
        assert any("天德" in l for l in labels)

    def test_tiande_no_match(self):
        _virtue_score = _import()[3]
        # 月支=2(寅月), 天德=丁(3)，日天干=0(甲) 不匹配
        bonus, labels = _virtue_score(0, 0, 2)
        # 月德：寅月月德=丙(2)，甲≠丙，无月德加分
        # 天德：甲≠丁，无天德加分
        # bonus 可能为0，也可能仅有月德（若丙=甲则不可能）
        assert bonus == 0

    def test_yuede_match(self):
        _virtue_score = _import()[3]
        # 月支=2(寅月)，月德=丙(idx=2)
        # 日天干=2(丙)
        bonus, labels = _virtue_score(2, 0, 2)
        assert bonus >= 10
        assert any("月德" in l for l in labels)

    def test_both_tiande_and_yuede(self):
        _virtue_score = _import()[3]
        # 月支=7(未月)，天德=甲(0)，月德=甲(0)
        # 日天干=0(甲) 同时满足
        bonus, labels = _virtue_score(0, 0, 7)
        assert bonus >= 25  # 15 + 10
        assert any("天德" in l for l in labels)
        assert any("月德" in l for l in labels)

    def test_no_virtue(self):
        _virtue_score = _import()[3]
        # 使用无天德天干匹配的情况
        # 月支=4(辰月)，天德=壬(8)，月德=壬(8)，日天干=5(己)
        bonus, labels = _virtue_score(5, 0, 4)
        assert bonus == 0
        assert labels == []

    def test_branch_type_tiande_matches(self):
        _virtue_score = _import()[3]
        # 月支=3(卯月)，天德落申(8)；日地支=8 → +15
        bonus, labels = _virtue_score(0, 8, 3)
        assert bonus == 25  # 天德15 + 月德10（卯月月德=甲，日天干=甲）
        assert any("天德" in l for l in labels)
        assert any("月德" in l for l in labels)


# ══════════════════════════════════════════════════════════════════════════
#  _purpose_bonus — 六种用途分支
# ══════════════════════════════════════════════════════════════════════════

class TestPurposeBonus:
    def test_marriage_liuhe(self):
        _purpose_bonus = _import()[4]
        # 命宫子(0)，日支丑(1)，子丑六合
        score, desc = _purpose_bonus("marriage", 1, 0, -1, 0, 0)
        assert score == 10
        assert "六合" in desc

    def test_marriage_sanhe(self):
        _purpose_bonus = _import()[4]
        # 命宫子(0)，日支辰(4)，申子辰三合水局；但 0 和 4 在同一三合
        score, desc = _purpose_bonus("marriage", 4, 0, -1, 0, 0)
        assert score == 8
        assert "三合" in desc

    def test_marriage_no_match(self):
        _purpose_bonus = _import()[4]
        # 命宫子(0)，日支寅(2)，无六合三合关系
        score, desc = _purpose_bonus("marriage", 2, 0, -1, 0, 0)
        assert score == 0

    def test_business_sheng_wo_or_same(self):
        _purpose_bonus = _import()[4]
        # 命主木(0)，日天干甲(0)=木=同 → +10
        score, desc = _purpose_bonus("business", 0, 0, -1, 0, 0)
        assert score == 10
        assert "生旺" in desc or "财运" in desc

    def test_business_no_match(self):
        _purpose_bonus = _import()[4]
        # 命主木(0)，日天干庚(6)=金=克我 → 0（business 只判断生旺条件）
        score, desc = _purpose_bonus("business", 0, 0, -1, 0, 6)
        assert score == 0

    def test_travel_liuhe(self):
        _purpose_bonus = _import()[4]
        # 命宫子(0)，日支丑(1)，六合 → +8
        score, desc = _purpose_bonus("travel", 1, 0, -1, 0, 0)
        assert score == 8
        assert "出行" in desc

    def test_travel_no_match(self):
        _purpose_bonus = _import()[4]
        # 命宫子(0)，日支卯(3)，无六合
        score, desc = _purpose_bonus("travel", 3, 0, -1, 0, 0)
        assert score == 0

    def test_medical_water_stem(self):
        _purpose_bonus = _import()[4]
        # 日天干壬(8)=水(4) → +6
        score, desc = _purpose_bonus("medical", 0, 0, -1, 0, 8)
        assert score == 6
        assert "水" in desc or "壬癸" in desc

    def test_medical_no_water(self):
        _purpose_bonus = _import()[4]
        # 日天干甲(0)=木 → 0
        score, desc = _purpose_bonus("medical", 0, 0, -1, 0, 0)
        assert score == 0

    def test_move_sansha_penalty(self):
        _purpose_bonus = _import()[4]
        # natal_b=2(寅年)，三煞={8,9,10}，日支=8(申) → -12
        score, desc = _purpose_bonus("move", 8, 0, 2, 0, 0)
        assert score == -12
        assert "三煞" in desc

    def test_move_no_sansha(self):
        _purpose_bonus = _import()[4]
        # natal_b=2(寅年)，三煞={8,9,10}，日支=0(子) 不在三煞
        score, desc = _purpose_bonus("move", 0, 0, 2, 0, 0)
        assert score == 0

    def test_move_no_natal_branch(self):
        _purpose_bonus = _import()[4]
        # natal_b=-1 → 跳过三煞检查
        score, desc = _purpose_bonus("move", 8, 0, -1, 0, 0)
        assert score == 0

    def test_career_sanhe_guanlu(self):
        _purpose_bonus = _import()[4]
        # 命宫子(0)，官禄宫=(0+8)%12=8(申)
        # 申(8)子(0)辰(4)三合，日支=4(辰) 在三合中
        score, desc = _purpose_bonus("career", 4, 0, -1, 0, 0)
        assert score == 8
        assert "官禄" in desc

    def test_career_no_match(self):
        _purpose_bonus = _import()[4]
        # 命宫子(0)，官禄宫=8(申)，日支=1(丑) 不在三合
        score, desc = _purpose_bonus("career", 1, 0, -1, 0, 0)
        assert score == 0

    def test_general_returns_zero(self):
        _purpose_bonus = _import()[4]
        score, desc = _purpose_bonus("general", 0, 0, -1, 0, 0)
        assert score == 0

    def test_marriage_no_life_b(self):
        _purpose_bonus = _import()[4]
        # life_b=-1 时 marriage 应安全返回 0
        score, desc = _purpose_bonus("marriage", 1, -1, -1, 0, 0)
        assert score == 0

    def test_travel_no_life_b(self):
        _purpose_bonus = _import()[4]
        score, desc = _purpose_bonus("travel", 1, -1, -1, 0, 0)
        assert score == 0

    def test_career_no_life_b(self):
        _purpose_bonus = _import()[4]
        score, desc = _purpose_bonus("career", 4, -1, -1, 0, 0)
        assert score == 0


# ══════════════════════════════════════════════════════════════════════════
#  _lunar_day_str — 农历日期显示
# ══════════════════════════════════════════════════════════════════════════

class TestLunarDayStr:
    def test_regular_month(self):
        _lunar_day_str = _import()[5]
        result = _lunar_day_str(3, 5)
        assert result == "三月初五"

    def test_first_day(self):
        _lunar_day_str = _import()[5]
        result = _lunar_day_str(1, 1)
        assert result == "正月初一"

    def test_leap_month(self):
        _lunar_day_str = _import()[5]
        # 闰月用负数表示
        result = _lunar_day_str(-4, 15)
        assert result == "闰四月十五"

    def test_thirtieth_day(self):
        _lunar_day_str = _import()[5]
        result = _lunar_day_str(12, 30)
        assert result == "十二月三十"

    def test_twelfth_month(self):
        _lunar_day_str = _import()[5]
        result = _lunar_day_str(12, 1)
        assert result == "十二月初一"

    def test_day_out_of_range(self):
        _lunar_day_str = _import()[5]
        # 越界时直接用数字
        result = _lunar_day_str(6, 31)
        assert "31" in result

    def test_eleventh_month(self):
        _lunar_day_str = _import()[5]
        result = _lunar_day_str(11, 20)
        assert result == "十一月二十"


# ══════════════════════════════════════════════════════════════════════════
#  recommend_month — 主函数全流程
# ══════════════════════════════════════════════════════════════════════════

class TestRecommendMonth:
    """集成测试：调用 sxtwl 真实计算一个月的择日结果。"""

    def test_returns_correct_type(self):
        recommend_month, ZeriMonthResult = _import()[6], _import()[8]
        result = recommend_month(2026, 4, "子", "水二局")
        assert isinstance(result, ZeriMonthResult)

    def test_year_and_month_match(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 4, "子", "水二局")
        assert result.year == 2026
        assert result.month == 4

    def test_days_count_correct(self):
        recommend_month, ZeriDayResult = _import()[6], _import()[7]
        result = recommend_month(2026, 4, "子", "水二局")
        assert len(result.days) == 30  # 4月30天

    def test_days_for_31_day_month(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 1, "子", "木三局")
        assert len(result.days) == 31

    def test_days_for_february(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 2, "午", "火六局")
        assert len(result.days) == 28

    def test_score_in_range(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 4, "子", "水二局")
        for day in result.days:
            assert 0 <= day.score <= 100

    def test_level_valid(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 4, "子", "水二局")
        valid_levels = {"大吉", "吉", "中", "凶"}
        for day in result.days:
            assert day.level in valid_levels

    def test_level_css_valid(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 4, "子", "水二局")
        valid_css = {"daji", "ji", "zhong", "xiong"}
        for day in result.days:
            assert day.level_css in valid_css

    def test_date_format(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 4, "子", "水二局")
        assert result.days[0].date == "2026-04-01"
        assert result.days[-1].date == "2026-04-30"

    def test_weekday_zh(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 4, "子", "水二局")
        valid_weekdays = {"一", "二", "三", "四", "五", "六", "日"}
        for day in result.days:
            assert day.weekday in valid_weekdays

    def test_lunar_info_not_empty(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 4, "子", "水二局")
        for day in result.days:
            assert day.lunar_info  # 非空字符串

    def test_day_gz_format(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 4, "子", "水二局")
        stems = set("甲乙丙丁戊己庚辛壬癸")
        branches = set("子丑寅卯辰巳午未申酉戌亥")
        for day in result.days:
            assert day.day_stem in stems
            assert day.day_branch in branches
            assert len(day.day_gz) == 2

    def test_top_days_subset_of_days(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 4, "子", "水二局")
        all_dates = {d.date for d in result.days}
        for td in result.top_days:
            assert td in all_dates

    def test_top_days_max_8(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 4, "子", "水二局")
        assert len(result.top_days) <= 8

    def test_top_days_only_good_levels(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 4, "子", "水二局")
        date_to_day = {d.date: d for d in result.days}
        for td in result.top_days:
            assert date_to_day[td].level in ("大吉", "吉")

    def test_purpose_label_correct(self):
        recommend_month, PURPOSES = _import()[6], _import()[9]
        for purpose_key in PURPOSES:
            result = recommend_month(2026, 4, "子", "水二局", purpose=purpose_key)
            assert result.purpose == purpose_key
            assert result.purpose_label == PURPOSES[purpose_key]

    def test_year_gz_format(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 4, "子", "水二局")
        assert len(result.year_gz) == 2

    def test_month_gz_format(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 4, "子", "水二局")
        assert len(result.month_gz) == 2

    def test_with_natal_year_branch(self):
        recommend_month = _import()[6]
        # 带本命年支，不应报错，且天数正确
        result = recommend_month(2026, 4, "子", "水二局", natal_year_branch="午")
        assert len(result.days) == 30

    def test_invalid_life_palace_branch(self):
        recommend_month = _import()[6]
        # 无效命宫地支 → 不报错，life_b=-1 跳过地支相关计算
        result = recommend_month(2026, 4, "InvalidBranch", "水二局")
        assert len(result.days) == 30

    def test_all_purposes_run_without_error(self):
        recommend_month = _import()[6]
        for purpose in ("marriage", "business", "travel", "medical", "move", "career", "general"):
            result = recommend_month(2026, 4, "子", "水二局", natal_year_branch="寅", purpose=purpose)
            assert len(result.days) == 30

    def test_break_days_have_is_break_true(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 4, "子", "水二局")
        for day in result.days:
            if day.is_break:
                # 有岁破/月破的日一定有对应 evidence
                assert any("破" in e for e in day.evidence)

    def test_virtue_days_have_evidence(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 4, "子", "水二局")
        for day in result.days:
            if day.is_virtue:
                assert any("天德" in e or "月德" in e for e in day.evidence)

    def test_score_lower_on_break_days(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 4, "子", "水二局")
        break_days = [d for d in result.days if d.is_break]
        if break_days:
            # 岁破-40 / 月破-25，得分必然受影响（一般不会大吉）
            for bd in break_days:
                assert bd.score < 90  # 不可能得大吉满分

    def test_evidence_is_list(self):
        recommend_month = _import()[6]
        result = recommend_month(2026, 4, "子", "水二局")
        for day in result.days:
            assert isinstance(day.evidence, list)

    def test_different_months_give_different_month_gz(self):
        recommend_month = _import()[6]
        r1 = recommend_month(2026, 3, "子", "水二局")
        r2 = recommend_month(2026, 6, "子", "水二局")
        # 不同月份的月柱应该不同
        assert r1.month_gz != r2.month_gz


# ══════════════════════════════════════════════════════════════════════════
#  数据结构 & 常量
# ══════════════════════════════════════════════════════════════════════════

class TestDataStructures:
    def test_purposes_dict_has_all_keys(self):
        PURPOSES = _import()[9]
        expected = {"marriage", "business", "travel", "medical", "move", "career", "general"}
        assert set(PURPOSES.keys()) == expected

    def test_stem_wx_length(self):
        _STEM_WX = _import()[10]
        assert len(_STEM_WX) == 10  # 10天干

    def test_zeri_day_result_dataclass(self):
        ZeriDayResult = _import()[7]
        d = ZeriDayResult(
            date="2026-04-01", weekday="三", day_gz="甲子",
            day_stem="甲", day_branch="子", lunar_info="三月初五",
            score=75, level="吉", level_css="ji",
            evidence=["天干有利"], is_break=False, is_virtue=False,
        )
        assert d.score == 75
        assert d.level == "吉"
        assert d.is_break is False
        assert d.evidence == ["天干有利"]

    def test_zeri_month_result_dataclass(self):
        ZeriMonthResult = _import()[8]
        r = ZeriMonthResult(
            year=2026, month=4, purpose="general", purpose_label="通用",
            year_gz="丙午", month_gz="甲辰",
        )
        assert r.year == 2026
        assert r.days == []
        assert r.top_days == []
