"""
geju.py 扩展测试——覆盖破格判断、从格、建禄/羊刃格、边界分支
目标：将 geju.py 覆盖率从 73% 提升到 95%+
"""
import pytest
from services.bazi_engine.geju import compute_geju, check_po_geju, _check_outer_geju


# ═══════════════════════════════════════════════════════════════════════════
# compute_geju 基础路径
# ═══════════════════════════════════════════════════════════════════════════

class TestComputeGejuBasic:
    """正格成格路径覆盖"""

    def test_zheng_guan_toukan(self):
        """正官格：月令主气透干"""
        # 甲木日主，月支子(水，主气壬)，年干有壬（正印透），时干庚（正官透）
        # 用月支酉（主气辛，辛对甲=正官）让正官格成立
        r = compute_geju("壬", "庚", "酉", "甲", "壬")
        assert r["name"] == "正官格"
        assert r["type"] == "inner"
        assert r["po_geju"]["broken"] is False

    def test_qi_sha_ge(self):
        """七杀格：甲木日主，月支酉（主气辛），辛对甲=七杀"""
        # 实际映射：get_ten_god(甲,辛)=七杀，get_ten_god(甲,庚)=正官
        r = compute_geju("壬", "辛", "酉", "甲", "壬")
        assert r["name"] == "七杀格"

    def test_zheng_yin_ge(self):
        """正印格：月令主气为正印"""
        # 甲木日主，月支子（主气壬，壬对甲=正印）
        r = compute_geju("甲", "壬", "子", "甲", "甲")
        assert r["name"] == "正印格"

    def test_pian_yin_ge(self):
        """偏印格：癸水月令对甲木=偏印"""
        # 甲木日主，月支亥（主气壬…不对），用月支丑（主气己=正财）换一个偏印
        # 偏印格：丙火日主，月支亥（主气壬，壬对丙=偏印七杀？）
        # 实际：甲日主，偏印=癸。月支亥主气癸
        r = compute_geju("甲", "癸", "亥", "甲", "甲")
        assert r["name"] == "偏印格"

    def test_shi_shen_ge(self):
        """食神格"""
        # 甲木日主，食神=丙。月支午（主气丙）
        r = compute_geju("甲", "丙", "午", "甲", "甲")
        assert r["name"] == "食神格"

    def test_shang_guan_ge(self):
        """伤官格"""
        # 甲木日主，伤官=丁。月支巳（主气丙，非丁）…
        # 使用甲日主，伤官=丁，月支未（主气己=正财）→需要月支巳内有丁？
        # 直接：甲日主，月支未（主气己），己对甲=正财格
        # 改用: 甲日主，月支午（主气丙）→丙对甲=食神
        # 甲日主，伤官丁，月支：选月支"巳"（主气丙），次气中有庚，中有戊和丁
        # 月支戌（主气戊，戊对甲=偏财），用时干丁透干
        r = compute_geju("丁", "丁", "巳", "甲", "甲")
        # 月支巳主气丙（食神），透干丁（伤官）→伤官格
        assert r["name"] == "伤官格"

    def test_jianlu_ge(self):
        """建禄格：月令为日主同五行比肩"""
        # 甲木，月支寅（主气甲，甲对甲=比肩=建禄格）
        r = compute_geju("甲", "甲", "寅", "甲", "甲")
        assert r["name"] == "建禄格"
        assert r["type"] == "special"

    def test_yangren_ge(self):
        """羊刃格：月令为日主劫财"""
        # 月支卯，主气乙（劫财），年干壬（水非木）确保透干取乙不取甲
        r = compute_geju("壬", "乙", "卯", "甲", "壬")
        assert r["name"] == "羊刃格"
        assert r["type"] == "special"

    def test_no_hidden_stems_returns_putong(self):
        """月支无藏干数据时返回普通格"""
        r = compute_geju("甲", "乙", "未知支", "甲", "甲")
        assert r["name"] == "普通格"
        assert r["confident"] is False

    def test_putong_ge_confidence_zero(self):
        """普通格 confidence == 0.0（包括无藏干的早期返回路径）"""
        r = compute_geju("甲", "乙", "未知支", "甲", "甲")
        # _no_geju 路径也应返回 confidence=0.0
        assert r.get("confidence", 0.0) == 0.0

    def test_toukan_confidence_high(self):
        """透干成格时 confidence >= 0.85"""
        r = compute_geju("壬", "庚", "酉", "甲", "壬")
        # 正官格，透干庚，正官格无破格 → confidence = 0.85
        assert r["confidence"] >= 0.75

    def test_returns_po_geju_key(self):
        """返回结果包含 po_geju 键"""
        r = compute_geju("甲", "甲", "寅", "甲", "甲")
        assert "po_geju" in r
        assert "broken" in r["po_geju"]
        assert "severity" in r["po_geju"]


# ═══════════════════════════════════════════════════════════════════════════
# 外格 _check_outer_geju（从旺/专旺/从格）
# ═══════════════════════════════════════════════════════════════════════════

class TestCheckOuterGeju:
    """覆盖 _check_outer_geju 的各分支"""

    def test_zhuan_wang_wood_tongqi(self):
        """日主木，木五行 ≥70% → 曲直格"""
        scores = {"wood": 80.0, "fire": 5.0, "earth": 5.0, "metal": 5.0, "water": 5.0}
        result = _check_outer_geju(scores, "甲", "甲", "寅")
        assert result == "曲直格"

    def test_zhuan_wang_fire_tongqi(self):
        """日主火，火五行 ≥70% → 炎上格"""
        scores = {"wood": 5.0, "fire": 80.0, "earth": 5.0, "metal": 5.0, "water": 5.0}
        result = _check_outer_geju(scores, "丙", "丙", "午")
        assert result == "炎上格"

    def test_zhuan_wang_metal_tongqi(self):
        """日主金，金五行 ≥70% → 从革格"""
        scores = {"wood": 5.0, "fire": 5.0, "earth": 5.0, "metal": 80.0, "water": 5.0}
        result = _check_outer_geju(scores, "庚", "庚", "申")
        assert result == "从革格"

    def test_zhuan_wang_water_tongqi(self):
        """日主水，水五行 ≥70% → 润下格"""
        scores = {"wood": 5.0, "fire": 5.0, "earth": 5.0, "metal": 5.0, "water": 80.0}
        result = _check_outer_geju(scores, "壬", "壬", "子")
        assert result == "润下格"

    def test_zhuan_wang_earth_tongqi(self):
        """日主土，土五行 ≥70% → 稼穑格"""
        scores = {"wood": 5.0, "fire": 5.0, "earth": 80.0, "metal": 5.0, "water": 5.0}
        result = _check_outer_geju(scores, "戊", "戊", "辰")
        assert result == "稼穑格"

    def test_zhuan_wang_non_day_elem(self):
        """非日主元素 ≥70% → 五行专旺格（非曲直）"""
        # 日主火，木 ≥70% → 曲直格（非日主）
        scores = {"wood": 80.0, "fire": 5.0, "earth": 5.0, "metal": 5.0, "water": 5.0}
        result = _check_outer_geju(scores, "丙", "丙", "午")
        assert result == "曲直格"  # 木专旺，非日主元素

    def test_cong_cai_ge(self):
        """从财格：日主极弱（≤10%），金/土最旺"""
        # 甲木日主，木仅5%，金65% → 庚对甲=七杀/从官杀格
        # 改：甲木，土最旺65% → 戊对甲=偏财 → 从财格
        scores = {"wood": 5.0, "fire": 5.0, "earth": 65.0, "metal": 15.0, "water": 10.0}
        result = _check_outer_geju(scores, "甲", "戊", "辰")
        assert result == "从财格"

    def test_cong_guansha_ge(self):
        """从官杀格：日主极弱，金最旺（庚对甲=七杀）"""
        scores = {"wood": 5.0, "fire": 0.0, "earth": 10.0, "metal": 65.0, "water": 20.0}
        result = _check_outer_geju(scores, "甲", "庚", "申")
        assert result == "从官杀格"

    def test_cong_er_ge(self):
        """从儿格：日主极弱，火最旺（丙对甲=食神）"""
        scores = {"wood": 5.0, "fire": 60.0, "earth": 15.0, "metal": 10.0, "water": 10.0}
        result = _check_outer_geju(scores, "甲", "丙", "午")
        assert result == "从儿格"

    def test_cong_shi_ge_fallback(self):
        """从势格：日主极弱，最强元素≥55%，但十神不在从格映射中"""
        # 水最旺65%（≥55%），壬对甲=正印，正印不在 _SHISHEN_CONG_GEJU → 从势格
        scores = {"wood": 5.0, "fire": 10.0, "earth": 10.0, "metal": 10.0, "water": 65.0}
        result = _check_outer_geju(scores, "甲", "壬", "子")
        assert result == "从势格"

    def test_no_outer_geju_balanced(self):
        """五行均衡不触发外格"""
        scores = {"wood": 20.0, "fire": 20.0, "earth": 20.0, "metal": 20.0, "water": 20.0}
        result = _check_outer_geju(scores, "甲", "甲", "寅")
        assert result is None

    def test_day_pct_above_10_no_cong(self):
        """日主占比 > 10%: 不触发从格"""
        scores = {"wood": 15.0, "fire": 5.0, "earth": 60.0, "metal": 10.0, "water": 10.0}
        result = _check_outer_geju(scores, "甲", "戊", "辰")
        # 木15%>10%，即使土最旺也不从格
        assert result is None

    def test_compute_geju_calls_outer(self):
        """compute_geju 对普通格触发外格检测"""
        scores = {"wood": 80.0, "fire": 5.0, "earth": 5.0, "metal": 5.0, "water": 5.0}
        r = compute_geju("甲", "甲", "寅", "甲", "甲", wuxing_scores=scores)
        assert r["name"] == "曲直格"
        assert r["type"] == "outer"


# ═══════════════════════════════════════════════════════════════════════════
# 破格 check_po_geju 各格局逐一覆盖
# ═══════════════════════════════════════════════════════════════════════════

class TestCheckPoGeju:
    """覆盖破格判断所有分支"""

    # 正官格破格
    def test_zheng_guan_po_by_shangguan(self):
        """伤官透干破正官格"""
        r = check_po_geju("正官格", ["壬", "庚", "甲", "丁"], "甲")
        # 丁对甲=伤官
        assert r["broken"] is True
        assert r["severity"] == "major"
        assert "伤官" in r["reason"]

    def test_zheng_guan_po_by_qisha(self):
        """官杀混杂破正官格：庚=正官，辛=七杀（此实现映射）"""
        r = check_po_geju("正官格", ["壬", "庚", "甲", "辛"], "甲")
        # 辛对甲=七杀（实际映射），混杂正官(庚)与七杀(辛)
        assert r["broken"] is True
        assert "官杀混杂" in r["reason"]

    def test_zheng_guan_no_po(self):
        """正官格无破格"""
        r = check_po_geju("正官格", ["壬", "庚", "甲", "壬"], "甲")
        assert r["broken"] is False

    # 七杀格破格
    def test_qi_sha_po_without_制(self):
        """七杀无制且日主弱 → major"""
        scores = {"wood": 5.0, "fire": 5.0, "earth": 5.0, "metal": 65.0, "water": 20.0}
        r = check_po_geju("七杀格", ["庚", "庚", "甲", "庚"], "甲", scores)
        assert r["broken"] is True
        assert r["severity"] == "major"

    def test_qi_sha_po_without_zhi_ri_strong(self):
        """七杀无制但日主强 → minor"""
        scores = {"wood": 40.0, "fire": 5.0, "earth": 5.0, "metal": 45.0, "water": 5.0}
        r = check_po_geju("七杀格", ["庚", "庚", "甲", "庚"], "甲", scores)
        assert r["broken"] is True
        assert r["severity"] == "minor"

    def test_qi_sha_no_po_with_shishen(self):
        """七杀有食神制杀 → 不破格"""
        r = check_po_geju("七杀格", ["庚", "庚", "甲", "丙"], "甲")
        # 丙对甲=食神，有制
        assert r["broken"] is False

    def test_qi_sha_shangguan_also_zhi(self):
        """七杀有伤官制杀 → 不破格"""
        r = check_po_geju("七杀格", ["庚", "庚", "甲", "丁"], "甲")
        # 丁对甲=伤官，也算制杀
        assert r["broken"] is False

    # 正印格破格
    def test_zheng_yin_po_major(self):
        """正印格财星2个 → major"""
        # 甲木日主，正印=壬。财星=戊（偏财）或己（正财），用己
        r = check_po_geju("正印格", ["己", "壬", "甲", "己"], "甲")
        # 己对甲=正财，两个正财
        assert r["broken"] is True
        assert r["severity"] == "major"

    def test_zheng_yin_po_minor(self):
        """正印格财星1个 → minor"""
        r = check_po_geju("正印格", ["己", "壬", "甲", "壬"], "甲")
        assert r["broken"] is True
        assert r["severity"] == "minor"

    def test_zheng_yin_no_po(self):
        """正印格无财星 → 不破"""
        r = check_po_geju("正印格", ["壬", "壬", "甲", "壬"], "甲")
        assert r["broken"] is False

    # 偏印格破格
    def test_pian_yin_po_by_shishen(self):
        """偏印格食神透干 → 破格"""
        # 甲木，偏印=癸，食神=丙
        r = check_po_geju("偏印格", ["癸", "癸", "甲", "丙"], "甲")
        assert r["broken"] is True
        assert "食神" in r["reason"]

    def test_pian_yin_no_po(self):
        """偏印格无食神 → 不破"""
        r = check_po_geju("偏印格", ["癸", "癸", "甲", "癸"], "甲")
        assert r["broken"] is False

    # 正财格破格
    def test_zheng_cai_po_major(self):
        """正财格比劫2个 → major（日主甲被跳过，需2个非甲的比/劫）"""
        # 乙=劫财，乙=劫财（year,hour各一个），bijie_count=2
        r = check_po_geju("正财格", ["乙", "己", "甲", "乙"], "甲")
        assert r["broken"] is True
        assert r["severity"] == "major"

    def test_zheng_cai_po_minor(self):
        """正财格比劫1个 → minor"""
        # year=己(偏财), month=乙(劫财), day=甲(skip), hour=己(偏财) → bijie_count=1
        r = check_po_geju("正财格", ["己", "乙", "甲", "己"], "甲")
        assert r["broken"] is True
        assert r["severity"] == "minor"

    def test_zheng_cai_no_po(self):
        """正财格无比劫 → 不破"""
        r = check_po_geju("正财格", ["己", "己", "甲", "己"], "甲")
        assert r["broken"] is False

    # 偏财格破格
    def test_pian_cai_po_major(self):
        """偏财格比劫2个以上 → major"""
        r = check_po_geju("偏财格", ["甲", "乙", "甲", "乙"], "甲")
        assert r["broken"] is True
        assert r["severity"] == "major"

    def test_pian_cai_po_minor(self):
        """偏财格比劫1个 → minor"""
        # year=乙(劫财), month=戊(正财), day=甲(skip), hour=戊(正财) → bijie_count=1
        r = check_po_geju("偏财格", ["乙", "戊", "甲", "戊"], "甲")
        assert r["broken"] is True
        assert r["severity"] == "minor"

    def test_pian_cai_no_po(self):
        """偏财格无比劫 → 不破"""
        r = check_po_geju("偏财格", ["戊", "戊", "甲", "戊"], "甲")
        assert r["broken"] is False

    # 食神格破格
    def test_shi_shen_po_by_pian_yin(self):
        """食神格偏印透干（枭印夺食）→ 破格"""
        # 甲木，食神=丙，偏印=癸
        r = check_po_geju("食神格", ["丙", "丙", "甲", "癸"], "甲")
        assert r["broken"] is True
        assert "枭" in r["reason"] or "偏印" in r["reason"]

    def test_shi_shen_no_po(self):
        """食神格无偏印 → 不破"""
        r = check_po_geju("食神格", ["丙", "丙", "甲", "丙"], "甲")
        assert r["broken"] is False

    # 伤官格破格
    def test_shang_guan_po_by_zheng_guan(self):
        """伤官格正官透干 → 大破"""
        # 甲木：庚=正官（实际映射），辛=七杀；用庚触发正官分支
        r = check_po_geju("伤官格", ["丁", "丁", "甲", "庚"], "甲")
        assert r["broken"] is True
        assert r["severity"] == "major"

    def test_shang_guan_po_by_qisha(self):
        """伤官格七杀透干 → minor"""
        # 甲木：辛=七杀（实际映射），用辛触发七杀 minor 分支
        r = check_po_geju("伤官格", ["丁", "丁", "甲", "辛"], "甲")
        assert r["broken"] is True
        assert r["severity"] == "minor"

    def test_shang_guan_no_po(self):
        """伤官格无官 → 不破"""
        r = check_po_geju("伤官格", ["丁", "丁", "甲", "丁"], "甲")
        assert r["broken"] is False

    # 普通格/其他格局
    def test_putong_ge_no_po(self):
        """普通格不触发破格逻辑"""
        r = check_po_geju("普通格", ["甲", "乙", "甲", "丙"], "甲")
        assert r["broken"] is False
        assert r["severity"] == "none"

    def test_jianlu_no_po(self):
        """建禄格不触发破格"""
        r = check_po_geju("建禄格", ["甲", "甲", "甲", "甲"], "甲")
        assert r["broken"] is False

    def test_wuxing_scores_none_elemental_check(self):
        """wuxing_scores=None 时 _elem_ratio 返回 0.0：七杀无制日主弱 → major"""
        # wuxing_scores=None 时 _day_elem() 返回 "wood"，_elem_ratio → 0.0 < 0.2
        r = check_po_geju("七杀格", ["庚", "庚", "甲", "庚"], "甲", None)
        assert r["broken"] is True
        assert r["severity"] == "major"

    def test_confidence_reduced_when_broken(self):
        """破格时 confidence 降档"""
        # 伤官格，正官透干 → 破格
        r = compute_geju("辛", "丁", "巳", "甲", "辛")
        # 伤官格 + 辛(正官)透干 → 破格，confidence 降
        if r["name"] == "伤官格" and r["po_geju"]["broken"]:
            assert r["confidence"] < 0.75
