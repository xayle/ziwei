"""
tests/test_ziwei_engine.py — 紫微斗数引擎黄金测试案例

黄金案例：2002-03-13 14:55 女 (壬午年 正月三十 未时)
预期结果均已通过人工图盘核验。
"""
import pytest
from services.ziwei_engine import ziwei_full
from services.ziwei_engine.lunar import solar_to_lunar
from services.ziwei_engine.palaces import calc_palaces
from services.ziwei_engine.stars_main import place_main_stars


GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY = 2002, 3, 13
GOLDEN_HOUR, GOLDEN_MIN = 14, 55
GOLDEN_GENDER = "女"


# ──────────────────────────────────────────────────────────────
# 农历转换
# ──────────────────────────────────────────────────────────────
class TestLunar:
    def test_lunar_month_day(self):
        info = solar_to_lunar(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY, GOLDEN_HOUR, GOLDEN_MIN)
        assert info.lunar_month == 1, f"农历月份应为正月(1)，实得 {info.lunar_month}"
        assert info.lunar_day == 30, f"农历日期应为三十，实得 {info.lunar_day}"

    def test_year_ganzhi(self):
        info = solar_to_lunar(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY, GOLDEN_HOUR, GOLDEN_MIN)
        assert info.year_gz == "壬午", f"年干支应为壬午，实得 {info.year_gz}"

    def test_hour_branch(self):
        info = solar_to_lunar(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY, GOLDEN_HOUR, GOLDEN_MIN)
        assert info.hour_branch == "未", f"时辰应为未时，实得 {info.hour_branch}"
        assert info.hour_branch_idx == 7, f"未时索引应为7，实得 {info.hour_branch_idx}"


# ──────────────────────────────────────────────────────────────
# 命宫/身宫/五行局
# ──────────────────────────────────────────────────────────────
class TestPalaces:
    def setup_method(self):
        info = solar_to_lunar(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY, GOLDEN_HOUR, GOLDEN_MIN)
        self.layout = calc_palaces(info)

    def test_life_palace_branch(self):
        # 命宫应在未(7)
        assert self.layout.life_branch_idx == 7, f"命宫地支应为未(7)，实得 {self.layout.life_branch_idx}"

    def test_life_palace_ganzhi(self):
        assert self.layout.life_ganzhi == "丁未", f"命宫干支应为丁未，实得 {self.layout.life_ganzhi}"

    def test_body_palace_branch(self):
        # 身宫应在酉(9)
        assert self.layout.body_branch_idx == 9, f"身宫地支应为酉(9)，实得 {self.layout.body_branch_idx}"

    def test_wuxing_ju(self):
        assert self.layout.wuxing_ju == 2, f"五行局应为2(水二局)，实得 {self.layout.wuxing_ju}"
        assert self.layout.wuxing_ju_name == "水二局", f"五行局名应为水二局，实得 {self.layout.wuxing_ju_name}"


# ──────────────────────────────────────────────────────────────
# 主星布局
# ──────────────────────────────────────────────────────────────
class TestMainStars:
    """
    验证14主星与命盘图对应关系。
    宫位命名：命宫=未(7)，宫名顺序：命宫→兄弟→夫妻→子女→财帛→疾厄→迁移→交友→官禄→田宅→福德→父母
    """
    BRANCH_MAP = {"子":0,"丑":1,"寅":2,"卯":3,"辰":4,"巳":5,"午":6,"未":7,"申":8,"酉":9,"戌":10,"亥":11}

    def setup_method(self):
        info = solar_to_lunar(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY, GOLDEN_HOUR, GOLDEN_MIN)
        layout = calc_palaces(info)
        self.stars = place_main_stars(info.lunar_day, layout.wuxing_ju)

    def _branch(self, star: str) -> int:
        return self.stars[star].branch_idx

    def test_ziwei_in_chen(self):
        assert self._branch("紫微") == 4, "紫微应在辰(子女宫)"

    def test_tianfu_in_zi(self):
        assert self._branch("天府") == 0, "天府应在子(交友宫)"

    def test_lianzheng_in_si(self):
        assert self._branch("廉贞") == 5, "廉贞应在巳(夫妻宫)"

    def test_tianji_in_mao(self):
        assert self._branch("天机") == 3, "天机应在卯(财帛宫)"

    def test_taiyang_in_chou(self):
        assert self._branch("太阳") == 1, "太阳应在丑(迁移宫)"

    def test_wuqu_in_zi(self):
        assert self._branch("武曲") == 0, "武曲应在子(交友宫)"

    def test_tiantong_in_hai(self):
        assert self._branch("天同") == 11, "天同应在亥(官禄宫)"

    def test_tanlang_in_yin(self):
        assert self._branch("贪狼") == 2, "贪狼应在寅(疾厄宫)"

    def test_tianxiang_in_chen(self):
        assert self._branch("天相") == 4, "天相应在辰(子女宫), 与紫微同宫"

    def test_tianmen_in_mao(self):
        assert self._branch("巨门") == 3, "巨门应在卯(财帛宫), 与天机同宫"

    def test_tainliang_in_si(self):
        assert self._branch("天梁") == 5, "天梁应在巳(夫妻宫), 与廉贞同宫"

    def test_qisha_in_wu(self):
        assert self._branch("七杀") == 6, "七杀应在午(兄弟宫)"

    def test_pojun_in_shen(self):
        assert self._branch("破军") == 8, "破军应在申(父母宫)"

    def test_taiyin_in_chou(self):
        assert self._branch("太阴") == 1, "太阴应在丑(迁移宫), 与太阳同宫"


# ──────────────────────────────────────────────────────────────
# 完整命盘集成测试
# ──────────────────────────────────────────────────────────────
class TestZiweiFull:
    def setup_method(self):
        self.chart = ziwei_full(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY,
                                GOLDEN_HOUR, GOLDEN_MIN, GOLDEN_GENDER)

    def test_chart_has_twelve_palaces(self):
        assert len(self.chart.palaces) == 12

    def test_life_palace_gz(self):
        assert self.chart.life_palace_gz == "丁未"

    def test_wuxing_ju_name(self):
        assert self.chart.wuxing_ju_name == "水二局"

    def test_dayun_reversed(self):
        # 壬午年(阳年)女命逆行
        assert not self.chart.dayun.forward, "壬午年女命大运应逆行"

    def test_dayun_start_age(self):
        # 起运虚岁约3岁
        assert self.chart.dayun.start_age == 3, f"起运虚岁应为3, 实得 {self.chart.dayun.start_age}"

    def test_dayun_first_cycle_year(self):
        # 第一组大运起运年份 2004
        first = self.chart.dayun.items[0]
        assert first.start_year == 2004, f"第一组大运起运年应为2004, 实得 {first.start_year}"

    def test_all_main_stars_placed(self):
        all_stars = {"紫微","天机","太阳","武曲","天同","廉贞",
                     "天府","太阴","贪狼","巨门","天相","天梁","七杀","破军"}
        placed = set()
        for p in self.chart.palaces:
            for s in p.main_stars:
                placed.add(s["name"])
        missing = all_stars - placed
        assert not missing, f"以下主星未安放: {missing}"

    def test_flying_chart_has_twelve(self):
        assert self.chart.flying is not None
        assert len(self.chart.flying.palaces) == 12

    def test_liunian_present(self):
        assert self.chart.liunian is not None
        assert self.chart.liunian.year_gz != ""
