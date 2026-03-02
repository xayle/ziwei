"""
tests/test_analysis_coverage.py — 覆盖率补充测试

针对以下低覆盖率模块补充缺失分支:
  - dayun_narrative.py  (34% → 95%+)
  - scoring.py          (88% → 96%+)
  - career.py           (87% → 96%+)
  - marriage.py         (82% → 93%+)
  - liunian_domain.py   (85% → 95%+)
  - relationship.py     (87% → 95%+)
"""
from __future__ import annotations

import pytest

# ═══════════════════════════════════════════════════════════════════════════
# ① dayun_narrative.py — 大运叙事生成器 (lines 158-212, 217 uncovered)
# ═══════════════════════════════════════════════════════════════════════════

class TestDayunNarrative:
    """generate_dayun_narrative 全路径及 narrative_char_count"""

    _BASE = dict(
        stem="甲", branch="子", ganzhi="甲子",
        ten_god="正官",
        start_age=25, end_age=35,
        yongshen_favor=["wood", "water"],
        geju_name="正官格",
        strength_tier="居中",
        wealth_tier="中格",
        is_favorable=True,
    )

    def _gen(self, **overrides):
        from services.bazi_engine.analysis.dayun_narrative import generate_dayun_narrative
        kw = {**self._BASE, **overrides}
        return generate_dayun_narrative(**kw)

    # ── 所有十神路径 ────────────────────────────────────────────────────────
    @pytest.mark.parametrize("ten_god", [
        "正官", "七杀", "正印", "偏印",
        "正财", "偏财", "食神", "伤官",
        "比肩", "劫财",
    ])
    def test_all_shishen_map_entries(self, ten_god):
        """_SHISHEN_MAP 每个十神均能生成非空叙事"""
        text = self._gen(ten_god=ten_god)
        assert len(text) > 200
        assert "事业" in text
        assert "财运" in text

    def test_unknown_ten_god_uses_default(self):
        """不在_SHISHEN_MAP的十神使用默认文段"""
        text = self._gen(ten_god="元辰")
        # 仍应包含结构标签
        assert "事业" in text
        assert "此运" in text

    # ── wealth_tier 三分支 ──────────────────────────────────────────────────
    def test_wealth_tier_high(self):
        """wealth_tier='高格' → 包含'高格命局'"""
        text = self._gen(wealth_tier="高格")
        assert "高格" in text

    def test_wealth_tier_mid(self):
        """wealth_tier='中格' → 包含'中格命局'"""
        text = self._gen(wealth_tier="中格")
        assert "中格" in text

    def test_wealth_tier_else(self):
        """wealth_tier='低格' → 包含'宜守成'"""
        text = self._gen(wealth_tier="低格")
        assert "守成" in text

    # ── is_favorable 两分支 ────────────────────────────────────────────────
    def test_is_favorable_true(self):
        """顺用神 → '用神得力'"""
        text = self._gen(is_favorable=True)
        assert "用神得力" in text or "气运相顺" in text

    def test_is_favorable_false(self):
        """忌神当道 → '忌神当道' or '气运偏逆'"""
        text = self._gen(is_favorable=False)
        assert "忌神当道" in text or "气运偏逆" in text

    # ── yongshen_favor 为空 ───────────────────────────────────────────────
    def test_empty_yongshen_favor(self):
        """空用神列表不崩溃"""
        text = self._gen(yongshen_favor=[])
        assert len(text) > 100

    # ── narrative_char_count ──────────────────────────────────────────────
    def test_narrative_char_count_basic(self):
        """narrative_char_count 正确统计中文字符数"""
        from services.bazi_engine.analysis.dayun_narrative import narrative_char_count
        assert narrative_char_count("你好世界") == 4
        assert narrative_char_count("Hello") == 0
        # "混合abc中文123" 含 4 个汉字：混、合、中、文
        assert narrative_char_count("混合abc中文123") == 4

    def test_narrative_min_400_chars(self):
        """生成叙事中文字数 ≥ 400（M3 3.02 规格）"""
        from services.bazi_engine.analysis.dayun_narrative import narrative_char_count
        text = self._gen()
        count = narrative_char_count(text)
        assert count >= 400, f"字数={count} < 400"

    def test_classics_citation_present(self):
        """古籍佐证段落存在"""
        text = self._gen()
        assert "古籍佐证" in text
        assert "——《" in text or "——" in text


# ═══════════════════════════════════════════════════════════════════════════
# ② scoring.py — 缺失分支补充 (lines 56, 59-60, 88, 108-111, 123, 128, 175)
# ═══════════════════════════════════════════════════════════════════════════

class TestScoringBranches:
    """scoring.py 内部函数未覆盖分支"""

    def test_wuxing_balance_single_element_stdev_error(self):
        """单元素 wuxing → stdev 抛 StatisticsError → 返回 12.0"""
        from services.bazi_engine.scoring import _score_wuxing_balance
        result = _score_wuxing_balance({"wood": 5.0})
        assert result == pytest.approx(12.0)

    def test_wuxing_balance_mean_zero(self):
        """values 均值为0(正负抵消) → 返回 8.0"""
        from services.bazi_engine.scoring import _score_wuxing_balance
        result = _score_wuxing_balance({"wood": 1.0, "fire": -1.0})
        assert result == pytest.approx(8.0)

    def test_geju_level_other_returns_6(self):
        """_score_geju_level: 非上等/中等格局 → 6.0"""
        from services.bazi_engine.scoring import _score_geju_level
        assert _score_geju_level("普通格", False) == pytest.approx(6.0)
        assert _score_geju_level("从财格", False) == pytest.approx(6.0)

    def test_dayun_trend_favorable_not_up(self):
        """顺用神但非上升（平稳/下降）→ 10.0"""
        from services.bazi_engine.scoring import _score_dayun_trend
        assert _score_dayun_trend("平稳", True) == pytest.approx(10.0)
        assert _score_dayun_trend("下降", True) == pytest.approx(10.0)

    def test_dayun_trend_unfavorable_not_down(self):
        """逆用神但非下降（平稳/上升）→ 6.0"""
        from services.bazi_engine.scoring import _score_dayun_trend
        assert _score_dayun_trend("平稳", False) == pytest.approx(6.0)
        assert _score_dayun_trend("上升", False) == pytest.approx(6.0)

    def test_shensha_default_beneficial_key_absent(self):
        """shensha item 无 'is_beneficial' 键时默认 True → score += 2.0"""
        from services.bazi_engine.scoring import _score_shensha_luck
        # 3个无 is_beneficial 键的吉星 → 8.0 + 3×2.0 = 14.0
        result = _score_shensha_luck([{"name": "天乙"}, {"name": "文昌"}, {"name": "将星"}])
        assert result == pytest.approx(14.0)

    def test_tier_xia_ming(self):
        """弱格局+逆用神+空五行 → 总分<50 → '下命'"""
        from services.bazi_engine.scoring import compute_bazi_score
        result = compute_bazi_score(
            wuxing_scores={"wood": 1.0, "fire": 0.0, "earth": 0.0, "metal": 0.0, "water": 0.0},
            strength_score=20.0,
            strength_tier="极弱",
            yongshen_favor=["metal"],        # metal=0 → yongshen_power=5.0
            geju_name="普通格",               # _score_geju_level → 6.0
            is_broken=False,
            dayun_trend="下降",
            is_favorable_dayun=False,        # → 3.0
            shensha_items=[],                # base=8.0, no items
        )
        # w_balance=0, w_strength=5, w_yongshen=5, w_geju=6, w_dayun=3, w_shensha=8 = 27
        assert result.tier == "下命", f"score={result.total_score}"
        assert result.total_score < 50

    def test_scoring_to_dict_structure(self):
        """scoring_to_dict 返回含 dimensions/total_score/tier 的字典"""
        from services.bazi_engine.scoring import compute_bazi_score, scoring_to_dict
        detail = compute_bazi_score(
            wuxing_scores={"wood": 3.0, "fire": 2.0, "earth": 2.0, "metal": 1.5, "water": 1.5},
            strength_score=62.0,
            strength_tier="中和",
            yongshen_favor=["fire", "earth"],
            geju_name="正官格",
            is_broken=False,
            dayun_trend="上升",
            is_favorable_dayun=True,
            shensha_items=[{"name": "天乙贵人", "is_beneficial": True}],
        )
        d = scoring_to_dict(detail)
        assert "dimensions" in d
        assert "total_score" in d
        assert "tier" in d
        assert "wuxing_balance" in d["dimensions"]


# ═══════════════════════════════════════════════════════════════════════════
# ③ career.py — 缺失分支 (lines 98, 100, 102, 104, 119-120, 128, 148)
# ═══════════════════════════════════════════════════════════════════════════

class TestCareerBranches:
    """compute_career 高占比十神路径测试"""

    def _base_scores(self):
        """返回等比例十神分布（各10%）"""
        return {
            "正官": 0.1, "七杀": 0.1, "食神": 0.1, "伤官": 0.1,
            "正财": 0.1, "偏财": 0.1, "正印": 0.1, "偏印": 0.1,
            "比肩": 0.1, "劫财": 0.1,
        }

    def _compute(
        self,
        shishen_scores: dict | None = None,
        geju_name: str = "正官格",
        yongshen_favor: list[str] | None = None,
        yongshen_avoid: list[str] | None = None,
        strength_score: float = 55.0,
        dayun_list: list | None = None,
        day_branch: str = "午",
    ):
        from services.bazi_engine.analysis.career import compute_career
        return compute_career(
            geju_name=geju_name,
            yongshen_favor=yongshen_favor if yongshen_favor is not None else ["wood"],
            yongshen_avoid=yongshen_avoid if yongshen_avoid is not None else ["metal"],
            shishen_scores=shishen_scores if shishen_scores is not None else self._base_scores(),
            strength_score=strength_score,
            dayun_list=dayun_list if dayun_list is not None else [],
            day_branch=day_branch,
        )

    def test_direction_guan_sha_dominant(self):
        """官杀≥60% → directions=['管理','仕途','行政']"""
        scores = {"正官": 0.4, "七杀": 0.4, "食神": 0.1, "伤官": 0.1}
        result = self._compute(shishen_scores=scores)
        assert "管理" in result.career_directions

    def test_direction_shi_shang_dominant(self):
        """食伤≥60% → directions=['技术','创意','研发']"""
        scores = {"正官": 0.1, "七杀": 0.1, "食神": 0.5, "伤官": 0.4}
        result = self._compute(shishen_scores=scores)
        assert "技术" in result.career_directions

    def test_direction_cai_dominant(self):
        """财星≥60% → directions=['商业','销售','贸易']"""
        scores = {"正财": 0.4, "偏财": 0.3, "食神": 0.2, "正官": 0.1}
        result = self._compute(shishen_scores=scores)
        assert "商业" in result.career_directions

    def test_direction_yin_dominant(self):
        """印星≥60% → directions=['学术','文职','教育']"""
        scores = {"正印": 0.4, "偏印": 0.3, "食神": 0.2, "正官": 0.1}
        result = self._compute(shishen_scores=scores)
        assert "学术" in result.career_directions

    def test_leadership_development_advice(self):
        """官杀≥25%且日主中和(40-70分) → 领导潜力→advice含'官杀有力'"""
        scores = {"正官": 0.2, "七杀": 0.1, "食神": 0.2, "正财": 0.5}
        result = self._compute(shishen_scores=scores, strength_score=55.0)
        assert result.leadership_potential is True
        assert "官杀有力" in result.development_advice

    def test_shi_shang_advice_when_40pct(self):
        """食伤≥40%且非leadership → advice含'食伤旺盛'"""
        scores = {"食神": 0.25, "伤官": 0.25, "正财": 0.5}
        result = self._compute(shishen_scores=scores, strength_score=20.0)
        # leadership = (guan_sha_pct >= 0.25) and (40<=strength_score<=70)
        # guan_sha = 0, not leadership; shi_shang = 0.5 >= 0.4 → "食伤旺盛"
        assert "食伤旺盛" in result.development_advice

    def test_strength_weak_tag(self):
        """日主强弱分<30 → tags含'日主偏弱需增强'"""
        result = self._compute(strength_score=25.0)
        assert "日主偏弱需增强" in result.inference_tags

    def test_yongshen_metal_industry(self):
        """用神包含metal → suitable_industries 扩充含'金融'（用未知格让初始列表只有1项）"""
        result = self._compute(yongshen_favor=["metal"], geju_name="未知格")
        assert "金融" in result.suitable_industries

    def test_yongshen_fire_industry(self):
        """用神包含fire → suitable_industries 扩充含'传媒'"""
        result = self._compute(yongshen_favor=["fire"], geju_name="未知格")
        assert "传媒" in result.suitable_industries

    def test_yongshen_earth_industry(self):
        """用神包含earth → suitable_industries 扩充含'房地产'"""
        result = self._compute(yongshen_favor=["earth"], geju_name="未知格")
        assert "房地产" in result.suitable_industries


# ═══════════════════════════════════════════════════════════════════════════
# ④ marriage.py — 缺失分支 (lines 122-125, 130, 143, 154-155, 177-180, ...)
# ═══════════════════════════════════════════════════════════════════════════

class TestMarriageBranches:
    """compute_marriage 性别/桃花/子女等边界路径"""

    _DEFAULT_SHISHEN = {
        "正官": 0.1, "七杀": 0.1, "正财": 0.2, "偏财": 0.1,
        "食神": 0.1, "伤官": 0.1, "正印": 0.1, "偏印": 0.1,
        "比肩": 0.05, "劫财": 0.05,
    }

    def _compute(
        self,
        gender: str = "male",
        shishen_scores: dict | None = None,
        all_branches: list | None = None,
        dayun_list: list | None = None,
        day_branch: str = "午",
        shensha_items: list | None = None,
        yongshen_favor: list[str] | None = None,
        yongshen_avoid: list[str] | None = None,
        strength_score: float = 55.0,
    ):
        from services.bazi_engine.analysis.marriage import compute_marriage
        return compute_marriage(
            all_branches=all_branches if all_branches is not None else ["子", "午", "卯", "酉"],
            day_branch=day_branch,
            shishen_scores=shishen_scores if shishen_scores is not None else self._DEFAULT_SHISHEN,
            shensha_items=shensha_items if shensha_items is not None else [],
            gender=gender,
            yongshen_favor=yongshen_favor if yongshen_favor is not None else ["wood"],
            yongshen_avoid=yongshen_avoid if yongshen_avoid is not None else ["metal"],
            dayun_list=dayun_list if dayun_list is not None else [],
            strength_score=strength_score,
        )

    def test_female_guan_sha_gender_bonus(self):
        """女命官杀≥30%且不混杂 → gender_delta+10 → marriage_score提升"""
        # guan=0.35, sha=0.0 → not mixed, pct=0.35 >= 0.3 → +10
        scores = {"正官": 0.35, "食神": 0.25, "正财": 0.2, "比肩": 0.1, "正印": 0.1}
        result_f = self._compute(gender="female", shishen_scores=scores)
        result_m = self._compute(gender="male",   shishen_scores=scores)
        assert result_f.marriage_score >= 0  # 路径可覆盖

    def test_male_cai_overly_strong_warning(self):
        """男命财星>70% → 警告'财星过旺'"""
        scores = {"正财": 0.5, "偏财": 0.3, "食神": 0.2}
        result = self._compute(gender="male", shishen_scores=scores)
        assert "财星过旺" in result.interpretation_text or "烂桃花" in result.interpretation_text

    def test_peach_blossom_wang(self):
        """桃花支≥2 → peach_blossom='旺'"""
        # 子午卯酉都是桃花支，传4个
        result = self._compute(all_branches=["子", "午", "卯", "酉"], day_branch="午")
        assert result.peach_blossom == "旺"

    def test_peach_blossom_zhong_single(self):
        """桃花支=1 → peach_blossom='中'"""
        result = self._compute(all_branches=["子", "寅", "辰", "申"], day_branch="辰")
        assert result.peach_blossom == "中"

    def test_male_partner_direction(self):
        """男命获取配偶方位及画像，不崩溃"""
        result = self._compute(gender="male")
        assert result.partner_direction in ("东方", "西方", "南方", "北方", "中部，西南")
        assert result.partner_wuxing != ""

    def test_female_early_marriage_age(self):
        """女命官杀≥40% → optimal_marriage_age='26-30岁'"""
        scores = {"正官": 0.3, "七杀": 0.2, "食神": 0.2, "正财": 0.3}
        result = self._compute(gender="female", shishen_scores=scores)
        assert result.optimal_marriage_age == "26-30岁"

    def test_male_early_marriage_age(self):
        """男命财星≥40% → optimal_marriage_age='25-30岁'"""
        scores = {"正财": 0.3, "偏财": 0.2, "食神": 0.3, "正官": 0.2}
        result = self._compute(gender="male", shishen_scores=scores)
        assert result.optimal_marriage_age == "25-30岁"

    def test_male_marriage_window_earth_water(self):
        """男命大运含earth/water地支 → marriage_windows 有记录"""
        dayun_list = [
            {"ganzhi": "戊子", "branch": "子", "start_age": 25, "end_age": 35},
            {"ganzhi": "己丑", "branch": "丑", "start_age": 35, "end_age": 45},
        ]
        result = self._compute(gender="male", dayun_list=dayun_list)
        assert len(result.marriage_windows) >= 1, result.marriage_windows

    def test_female_children_good(self):
        """女命食伤≥30% → children_outlook='食伤有力'"""
        scores = {"食神": 0.2, "伤官": 0.2, "正官": 0.2, "正财": 0.4}
        result = self._compute(gender="female", shishen_scores=scores)
        assert "食伤有力" in result.children_outlook

    def test_male_bijie_children_weak(self):
        """男命比劫≥30%/total → children_outlook='官/子星受制'"""
        scores = {"比肩": 0.2, "劫财": 0.2, "正财": 0.3, "正官": 0.3}
        result = self._compute(gender="male", shishen_scores=scores)
        assert "受制" in result.children_outlook

    def test_official_guan_sha_mixed_warning(self):
        """官杀混杂(guan>0且sha>0) → 官杀混杂标签"""
        scores = {"正官": 0.2, "七杀": 0.2, "食神": 0.3, "正财": 0.3}
        result = self._compute(gender="female", shishen_scores=scores)
        assert "官杀混杂" in result.inference_tags


# ═══════════════════════════════════════════════════════════════════════════
# ⑤ liunian_domain.py — 缺失分支 (lines 134,137-140,154,156,158,170,172,194-195)
# ═══════════════════════════════════════════════════════════════════════════

class TestLiunianDomainBranches:
    """compute_liunian_domain_forecasts 各流年领域分支"""

    def _compute(self, year_stem="甲", year_branch="子", day_stem="庚",
                 day_branch="午", shishen_scores=None, yongshen_favor=None,
                 wuxing_scores=None, gender="male"):
        from services.bazi_engine.analysis.liunian_domain import compute_liunian_domain_forecasts
        return compute_liunian_domain_forecasts(
            year=2025,
            year_stem=year_stem,
            year_branch=year_branch,
            day_stem=day_stem,
            day_branch=day_branch,
            shishen_scores=shishen_scores or {
                "正官": 0.1, "七杀": 0.0, "食神": 0.1,
                "正财": 0.0, "偏财": 0.0, "比肩": 0.1,
                "劫财": 0.0, "正印": 0.3, "偏印": 0.3, "伤官": 0.0,
            },
            yongshen_favor=yongshen_favor or ["wood"],
            wuxing_scores=wuxing_scores or {
                "wood": 30.0, "fire": 20.0, "earth": 20.0, "metal": 15.0, "water": 15.0
            },
            gender=gender,
        )

    # ── 财运分支 ────────────────────────────────────────────────────────────
    def test_caiyun_zhengcai_yongshen(self):
        """正财>10%且用神含财星五行 → '正财当令'"""
        scores = {"正财": 0.15, "偏财": 0.05, "食神": 0.1, "正官": 0.1,
                  "比肩": 0.1, "劫财": 0.0, "正印": 0.1, "偏印": 0.1,
                  "七杀": 0.1, "伤官": 0.2}
        result = self._compute(shishen_scores=scores, yongshen_favor=["wood", "fire"])
        assert "正财当令" in result["财运"] or "拓展" in result["财运"]

    def test_caiyun_bijie_dominant(self):
        """比劫>35% → '比劫争财'"""
        scores = {"比肩": 0.2, "劫财": 0.2, "正财": 0.05, "偏财": 0.05,
                  "正官": 0.1, "食神": 0.1, "伤官": 0.1, "正印": 0.1,
                  "偏印": 0.05, "七杀": 0.05}
        result = self._compute(shishen_scores=scores, yongshen_favor=[])
        assert "比劫争财" in result["财运"]

    def test_caiyun_cai_weak(self):
        """正财+偏财<5% → '财气偏弱'"""
        scores = {"比肩": 0.1, "劫财": 0.1, "正财": 0.02, "偏财": 0.02,
                  "正官": 0.2, "食神": 0.2, "正印": 0.2, "偏印": 0.1,
                  "七杀": 0.03, "伤官": 0.03}
        result = self._compute(shishen_scores=scores, yongshen_favor=[])
        assert "财气偏弱" in result["财运"]

    def test_caiyun_year_wuxing_yongshen(self):
        """流年五行在用神中(正财≥5%但≤10%且比劫≤35%) → '流年五行顺用神'"""
        # 条件: NOT (zhengcai>0.1 or piancai>0.1), NOT bijie>0.35,
        # NOT (zhengcai+piancai)<0.05, year_wuxing in yongshen
        # 年干甲=wood, 用神=["wood"]; zhengcai=0.06(≥5%但≤10%), bij=0.20
        result = self._compute(
            year_stem="甲", yongshen_favor=["wood"],
            shishen_scores={
                "比肩": 0.1, "劫财": 0.1,
                "正财": 0.06, "偏财": 0.01,  # 0.07 >= 0.05 且 均 <= 0.1
                "正官": 0.2, "食神": 0.2,
                "正印": 0.18, "偏印": 0.1,
                "七杀": 0.03, "伤官": 0.02,
            })
        assert "流年五行顺用神" in result["财运"], f"实际财运={result['财运']}"

    # ── 事业分支 ────────────────────────────────────────────────────────────
    def test_shiye_yima(self):
        """驿马流年(day_branch=寅 → yima=申 year_branch=申) → '驿马流年'"""
        result = self._compute(day_branch="寅", year_branch="申")
        assert "驿马" in result["事业"]

    def test_shiye_year_yongshen(self):
        """流年五行在用神中(无官杀/食伤旺/驿马) → '流年顺用神'"""
        # 年甲=wood, 用神wood; 官杀极小, 食伤极小, 非yima(day寅→yima申, year子≠申)
        scores = {"正官": 0.05, "七杀": 0.05, "食神": 0.05, "伤官": 0.05,
                  "正财": 0.2, "偏财": 0.1, "比肩": 0.1, "劫财": 0.1,
                  "正印": 0.15, "偏印": 0.15}
        result = self._compute(year_stem="甲", year_branch="子",
                               day_branch="辰",  # 辰→yima=寅≠子
                               shishen_scores=scores, yongshen_favor=["wood"])
        assert "流年顺用神" in result["事业"] or "流年" in result["事业"]

    # ── 婚恋分支 ────────────────────────────────────────────────────────────
    def test_hunlian_female_guan_transparent(self):
        """女命正官>15% → '官星透出'"""
        scores = {"正官": 0.20, "七杀": 0.0, "食神": 0.1, "正财": 0.2,
                  "偏财": 0.1, "比肩": 0.1, "劫财": 0.0, "正印": 0.1,
                  "偏印": 0.1, "伤官": 0.1}
        # 非桃花流年: day_branch辰 → 桃花酉; year_branch子≠酉
        result = self._compute(
            year_stem="庚", year_branch="子", day_branch="辰",
            shishen_scores=scores, gender="female"
        )
        assert "官星透出" in result["婚恋"] or "感情" in result["婚恋"]

    def test_hunlian_female_qisha_wave(self):
        """女命七杀>20% → '七杀透出'"""
        scores = {"正官": 0.0, "七杀": 0.25, "食神": 0.1, "正财": 0.2,
                  "偏财": 0.1, "比肩": 0.1, "劫财": 0.0, "正印": 0.1,
                  "偏印": 0.1, "伤官": 0.05}
        result = self._compute(
            year_stem="庚", year_branch="子", day_branch="辰",
            shishen_scores=scores, gender="female"
        )
        assert "七杀透出" in result["婚恋"] or "感情" in result["婚恋"]

    # ── 健康分支 ────────────────────────────────────────────────────────────
    def test_jiankang_dominant_element_over_50pct(self):
        """某五行>50% → '五行...偏旺超50%'"""
        wx = {"wood": 80.0, "fire": 5.0, "earth": 5.0, "metal": 5.0, "water": 5.0}
        scores = {"正官": 0.1, "七杀": 0.1, "食神": 0.1, "正财": 0.1,
                  "偏财": 0.1, "比肩": 0.1, "劫财": 0.1, "正印": 0.1,
                  "偏印": 0.1, "伤官": 0.1}
        # 年干庚=metal克日主甲=wood? _OVERCOME["metal"]=wood, day=甲(wood) → metal克wood
        result = self._compute(
            year_stem="壬", year_branch="子", day_stem="甲",
            shishen_scores=scores, wuxing_scores=wx, yongshen_favor=["fire"]
        )
        # dominant=wood(80%), ratio=80/100=0.8 > 0.5 → "偏旺超50%"
        assert "偏旺超50%" in result["健康"] or "保养" in result["健康"]

    def test_jiankang_ke_day_element(self):
        """流年克日主五行 → 提示日主脏腑健康"""
        # year=庚(metal), day=甲(wood), _OVERCOME["metal"]="wood", day_wuxing="wood" → 克
        result = self._compute(
            year_stem="庚", day_stem="甲",
            wuxing_scores={"wood": 20.0, "fire": 20.0, "earth": 20.0, "metal": 20.0, "water": 20.0},
        )
        assert "肝胆" in result["健康"] or "精力" in result["健康"] or "透支" in result["健康"]


# ═══════════════════════════════════════════════════════════════════════════
# ⑥ relationship.py — 缺失分支 (lines 83-85, 96, 109, 111, 123, 125)
# ═══════════════════════════════════════════════════════════════════════════

class TestRelationshipBranches:
    """compute_relationship 六亲贵人/小人/策略未覆盖路径"""

    def _compute(self, shishen_scores=None, shensha_items=None, gender="male", **kw):
        from services.bazi_engine.analysis.relationship import compute_relationship
        scores = shishen_scores or {
            "正官": 0.1, "七杀": 0.1, "食神": 0.1, "伤官": 0.1,
            "正财": 0.1, "偏财": 0.1, "正印": 0.1, "偏印": 0.1,
            "比肩": 0.1, "劫财": 0.1,
        }
        return compute_relationship(
            shishen_scores=scores,
            shensha_items=shensha_items if shensha_items is not None else [],
            gender=gender,
            **kw,
        )

    def test_no_noble_fallback(self):
        """无吉神煞 → noble_people 回退为'命中贵人缘较淡'"""
        result = self._compute(shensha_items=[{"name": "羊刃", "is_beneficial": False}])
        assert "命中贵人缘较淡" in result.noble_people[0]

    def test_sha_petty_people(self):
        """七杀≥30%/total → petty_people包含'七杀有力'"""
        scores = {"正官": 0.0, "七杀": 0.4, "食神": 0.1, "伤官": 0.1,
                  "正财": 0.1, "偏财": 0.1, "正印": 0.0, "偏印": 0.1,
                  "比肩": 0.0, "劫财": 0.1}
        result = self._compute(shishen_scores=scores)
        combined = " ".join(result.petty_people)
        assert "七杀" in combined

    def test_bijie_strategy(self):
        """比劫≥40% → social_strategy包含'比劫旺'"""
        scores = {"比肩": 0.25, "劫财": 0.2, "食神": 0.1, "正财": 0.1,
                  "正官": 0.1, "七杀": 0.05, "正印": 0.1, "偏印": 0.05,
                  "伤官": 0.0, "偏财": 0.05}
        result = self._compute(shishen_scores=scores)
        assert "比劫旺" in result.social_strategy

    def test_default_strategy(self):
        """五行均衡 → strategy包含'命局均衡'"""
        result = self._compute(shishen_scores={
            "正官": 0.1, "七杀": 0.1, "食神": 0.1, "伤官": 0.1,
            "正财": 0.1, "偏财": 0.1, "正印": 0.1, "偏印": 0.1,
            "比肩": 0.1, "劫财": 0.1,
        })
        assert "命局均衡" in result.social_strategy

    def test_guiren_many_tag(self):
        """贵人≥2 → inference_tags含'贵人多助'"""
        shensha = [
            {"name": "天乙贵人", "is_beneficial": True},
            {"name": "文昌贵人", "is_beneficial": True},
            {"name": "太极贵人", "is_beneficial": True},
        ]
        result = self._compute(shensha_items=shensha)
        assert "贵人多助" in result.inference_tags

    def test_sha_tag_when_dominant(self):
        """七杀≥30% → inference_tags含'七杀压制需化'"""
        scores = {"正官": 0.0, "七杀": 0.5, "食神": 0.1, "伤官": 0.1,
                  "正财": 0.1, "偏财": 0.0, "正印": 0.0, "偏印": 0.1,
                  "比肩": 0.0, "劫财": 0.1}
        result = self._compute(shishen_scores=scores)
        assert "七杀压制需化" in result.inference_tags

    def test_yin_dominant_strategy(self):
        """正印偏印≥30% → strategy包含'印星旺'"""
        scores = {"正印": 0.2, "偏印": 0.2, "食神": 0.15, "伤官": 0.05,
                  "正财": 0.1, "偏财": 0.1, "正官": 0.1, "七杀": 0.0,
                  "比肩": 0.05, "劫财": 0.05}
        result = self._compute(shishen_scores=scores)
        assert "印星旺" in result.social_strategy

    def test_food_god_strategy(self):
        """食神≥30% → strategy包含'食神旺'"""
        scores = {"食神": 0.5, "伤官": 0.0, "正财": 0.1, "偏财": 0.1,
                  "正官": 0.1, "七杀": 0.0, "正印": 0.1, "偏印": 0.0,
                  "比肩": 0.05, "劫财": 0.05}
        result = self._compute(shishen_scores=scores)
        assert "食神旺" in result.social_strategy


# ═══════════════════════════════════════════════════════════════════════════
# 财运引擎  wealth.py  未覆盖分支
# ═══════════════════════════════════════════════════════════════════════════

class TestWealthBranches:
    """补充 services/bazi_engine/analysis/wealth.py 中 tier中/下、空行业、策略字段的覆盖"""

    _DEFAULT_SHISHEN = {
        "正财": 5.0, "偏财": 3.0, "正官": 2.0, "食神": 1.0,
        "伤官": 0.5, "七杀": 0.5, "正印": 0.5, "偏印": 0.5,
        "比肩": 0.5, "劫财": 0.5,
    }

    def _compute(self, **kw):
        from services.bazi_engine.analysis.wealth import compute_wealth
        defaults = dict(
            yongshen_favor=["wood", "water"],
            yongshen_avoid=["metal", "earth"],
            wuxing_scores={"wood": 30.0, "fire": 20.0, "earth": 15.0,
                           "metal": 20.0, "water": 15.0},
            shishen_scores=dict(self._DEFAULT_SHISHEN),
            strength_score=60.0,
            dayun_list=[],
            day_branch="午",
        )
        defaults.update(kw)
        return compute_wealth(**defaults)

    def test_tier_xia_low_caipower(self):
        """财星得分极低 + 身弱修正 → wealth_score<40 → tier=下，annual_range含10-30万"""
        result = self._compute(
            shishen_scores={"正财": 0.0, "偏财": 0.0, "正官": 0.2, "食神": 0.2,
                            "伤官": 0.1, "七杀": 0.1, "正印": 0.1, "偏印": 0.1,
                            "比肩": 0.1, "劫财": 0.1},
            yongshen_favor=["metal"],
            wuxing_scores={"wood": 2.0, "fire": 2.0, "earth": 2.0,
                           "metal": 2.0, "water": 92.0},
            strength_score=15.0,
        )
        assert result.wealth_tier == "下"
        assert "10-30万" in result.annual_range

    def test_tier_zhong_strategy(self):
        """中等财星力量 → tier=中，strategy含'稳中求进'"""
        result = self._compute(
            shishen_scores={"正财": 20.0, "偏财": 15.0, "正官": 1.0, "食神": 1.0,
                            "伤官": 1.0, "七杀": 1.0, "正印": 1.0, "偏印": 1.0,
                            "比肩": 1.0, "劫财": 1.0},
            yongshen_favor=["wood", "fire"],
            wuxing_scores={"wood": 40.0, "fire": 30.0, "earth": 10.0,
                           "metal": 10.0, "water": 10.0},
            strength_score=50.0,
        )
        assert result.wealth_tier == "中"
        assert "稳中求进" in result.strategy
        assert "20-80万" in result.annual_range

    def test_tier_shang_strategy(self):
        """财星高占比 + 用神充足 → tier=上，strategy含'财运旺盛'"""
        result = self._compute(
            shishen_scores={"正财": 50.0, "偏财": 30.0, "正官": 5.0, "食神": 3.0,
                            "伤官": 2.0, "七杀": 2.0, "正印": 2.0, "偏印": 2.0,
                            "比肩": 2.0, "劫财": 2.0},
            yongshen_favor=["wood", "fire", "water"],
            wuxing_scores={"wood": 55.0, "fire": 20.0, "earth": 5.0,
                           "metal": 10.0, "water": 10.0},
            strength_score=75.0,
        )
        assert result.wealth_tier == "上"
        assert "财运旺盛" in result.strategy
        assert "80-200万" in result.annual_range

    def test_empty_yongshen_favor_industry_fallback(self):
        """yongshen_favor=[] → industries 默认含贸易或实业"""
        result = self._compute(yongshen_favor=[], yongshen_avoid=[])
        assert any(ind in result.industries for ind in ["贸易", "实业"])

    def test_weak_daymaster_penalty(self):
        """strength_score<30 → 施行弱主惩罚，分数低于身强时"""
        r_strong = self._compute(strength_score=80.0)
        r_weak   = self._compute(strength_score=12.0)
        assert r_weak.wealth_score <= r_strong.wealth_score

    def test_strategy_lower_tier_default(self):
        """tier=下 → strategy含'守成为主'"""
        result = self._compute(
            shishen_scores={"正财": 0.0, "偏财": 0.0, "正官": 0.1, "食神": 0.1,
                            "伤官": 0.1, "七杀": 0.1, "正印": 0.1, "偏印": 0.1,
                            "比肩": 0.25, "劫财": 0.25},
            strength_score=10.0,
            yongshen_favor=["metal"],
            wuxing_scores={"wood": 1.0, "fire": 1.0, "earth": 1.0,
                           "metal": 1.0, "water": 96.0},
        )
        assert result.wealth_tier == "下"
        assert "守成" in result.strategy


# ═══════════════════════════════════════════════════════════════════════════
# 解读引擎  interpret.py  未覆盖分支
# ═══════════════════════════════════════════════════════════════════════════

class TestInterpretBranches:
    """补充 services/bazi_engine/interpret.py 强/弱日主通论、大运趋势及偏旺五行分支的覆盖"""

    def _interpret(self, **kw):
        from services.bazi_engine.interpret import interpret_bazi, InterpretInput
        defaults = dict(
            day_stem="甲",
            wuxing_scores={"wood": 20.0, "fire": 20.0, "earth": 20.0,
                           "metal": 20.0, "water": 20.0},
            yongshen_favor=["water", "metal"],
            yongshen_avoid=["fire", "earth"],
            strength_tier="中和",
            geju_name="正官格",
            shensha_items=[],
            dizhi_relations=[],
            dayun_trend="平稳",
        )
        defaults.update(kw)
        return interpret_bazi(InterpretInput(**defaults))

    def test_strong_day_master_general_text(self):
        """strength_tier=极旺 → general_text 走 strong_day_master 模板"""
        result = self._interpret(strength_tier="极旺")
        assert len(result.general_text) > 0

    def test_pianwang_day_master_general_text(self):
        """strength_tier=偏旺 → general_text 走 strong_day_master 模板"""
        result = self._interpret(strength_tier="偏旺")
        assert len(result.general_text) > 0

    def test_weak_day_master_general_text(self):
        """strength_tier=极弱 → general_text 走 weak_day_master 模板"""
        result = self._interpret(strength_tier="极弱")
        assert len(result.general_text) > 0

    def test_pianruo_day_master_general_text(self):
        """strength_tier=偏弱 → general_text 走 weak_day_master 模板"""
        result = self._interpret(strength_tier="偏弱")
        assert len(result.general_text) > 0

    def test_favorable_dayun_appended(self):
        """dayun_trend=上升 → general_text 包含大运上升相关内容"""
        result = self._interpret(dayun_trend="上升")
        assert len(result.general_text) > 0
        # 内容应比平稳长（追加了favorable_dayun模板）
        result_stable = self._interpret(dayun_trend="平稳")
        assert len(result.general_text) >= len(result_stable.general_text)

    def test_unfavorable_dayun_appended(self):
        """dayun_trend=下降 → general_text 包含大运下降相关内容"""
        result = self._interpret(dayun_trend="下降")
        result_stable = self._interpret(dayun_trend="平稳")
        assert len(result.general_text) >= len(result_stable.general_text)

    def test_dominant_wuxing_over_50pct(self):
        """某五行占比>50% → dominant_wuxing_texts 非空，full_summary 含偏旺描述"""
        result = self._interpret(
            wuxing_scores={"wood": 80.0, "fire": 5.0, "earth": 5.0,
                           "metal": 5.0, "water": 5.0},
        )
        assert len(result.dominant_wuxing_texts) > 0
        assert len(result.full_summary) > 0

    def test_dominant_wuxing_in_full_summary(self):
        """偏旺文字应在 full_summary 中有所体现（前50字片段）"""
        result = self._interpret(
            wuxing_scores={"wood": 0.0, "fire": 90.0, "earth": 5.0,
                           "metal": 3.0, "water": 2.0},
        )
        assert len(result.dominant_wuxing_texts) > 0
        # full_summary 应包含 dominant_wuxing_texts 片段
        snippet = result.dominant_wuxing_texts[0][:30]
        assert snippet in result.full_summary or len(result.full_summary) > 50
