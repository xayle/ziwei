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

    def test_lianzheng_in_shen(self):
        assert self._branch("廉贞") == 8, "廉贞应在申(迁移宫)，紫微逆行8位"

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
        assert self._branch("天梁") == 5, "天梁应在巳(夹妻宫)"

    def test_qisha_in_wu(self):
        assert self._branch("七杀") == 6, "七杀应在午(兄弟宫)"

    def test_pojun_in_xu(self):
        assert self._branch("破军") == 10, "破军应在戌(福德宫)，天府顺行10位"

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
        # 紫微大限起运虚岁 = 五行局数（水二局=2）
        assert self.chart.dayun.start_age == 2, f"起运虚岁应为2(水二局), 实得 {self.chart.dayun.start_age}"

    def test_dayun_first_cycle_year(self):
        # 紫微大限：第一组大运起运年份 = 出生年 + 起运虚岁 - 1 = 2002 + 2 - 1 = 2003
        first = self.chart.dayun.items[0]
        assert first.start_year == 2003, f"第一组大运起运年应为2003, 实得 {first.start_year}"

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


# ──────────────────────────────────────────────────────────────
# 命主 / 身主
# ──────────────────────────────────────────────────────────────
class TestLifeBodyRuler:
    """
    黄金案例: 壬午年 女, 水二局, 命宫未(7)
    贪狼在寅(2)，命宫在未(7)，步数=(7-2)=5，六星周期[0贪狼…5武曲]→ 命主武曲
    身主: 年支午(6) → 火星
    """
    def setup_method(self):
        self.chart = ziwei_full(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY,
                                GOLDEN_HOUR, GOLDEN_MIN, GOLDEN_GENDER)

    def test_life_ruler_star(self):
        assert self.chart.life_ruler_star == "武曲", \
            f"命主应为武曲，实得 {self.chart.life_ruler_star}"

    def test_body_ruler_star(self):
        assert self.chart.body_ruler_star == "火星", \
            f"身主应为火星，实得 {self.chart.body_ruler_star}"


# ──────────────────────────────────────────────────────────────
# 小限
# ──────────────────────────────────────────────────────────────
class TestXiaoXian:
    """
    黄金案例: 女命壬午年(午支=6, 三合火)
    standard 口径（Z-05）：寅午戌组起辰(4)，女命逆数:
      辰(4)=1岁, 卯(3)=2岁, 寅(2)=3岁, …, 未(7=命宫)=10岁
    """
    def setup_method(self):
        self.chart = ziwei_full(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY,
                                GOLDEN_HOUR, GOLDEN_MIN, GOLDEN_GENDER)

    def _palace_by_branch(self, branch_idx: int):
        return next(p for p in self.chart.palaces if p.branch_idx == branch_idx)

    def test_start_palace_has_age1(self):
        # 女命壬午 standard: 小限1岁在辰(4)宫
        chen = self._palace_by_branch(4)
        assert 1 in chen.xiaoxian_ages, f"辰宫应含小限1岁，实得 {chen.xiaoxian_ages[:5]}"

    def test_start_palace_has_age13(self):
        chen = self._palace_by_branch(4)
        assert 13 in chen.xiaoxian_ages, f"辰宫应含小限13岁"

    def test_life_palace_has_age10(self):
        # 命宫在未(7): 10岁
        wei = self._palace_by_branch(7)
        assert 10 in wei.xiaoxian_ages, f"命宫(未)应含小限10岁，实得 {wei.xiaoxian_ages[:5]}"

    def test_life_palace_has_age22(self):
        wei = self._palace_by_branch(7)
        assert 22 in wei.xiaoxian_ages, "命宫(未)应含小限22岁"

    def test_life_palace_has_age34(self):
        wei = self._palace_by_branch(7)
        assert 34 in wei.xiaoxian_ages, "命宫(未)应含小限34岁"

    def test_legacy_gender_split_still_available(self):
        legacy = ziwei_full(
            GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY,
            GOLDEN_HOUR, GOLDEN_MIN, GOLDEN_GENDER,
            xiaoxian_start_method="gender_split",
        )
        shen = next(p for p in legacy.palaces if p.branch_idx == 8)
        assert 1 in shen.xiaoxian_ages

    def test_all_palaces_have_xiaoxian(self):
        # 每宫都应分有小限年龄
        for p in self.chart.palaces:
            assert len(p.xiaoxian_ages) > 0, f"{p.name}({p.branch})小限年龄列表不应为空"

    def test_total_xiaoxian_count(self):
        total = sum(len(p.xiaoxian_ages) for p in self.chart.palaces)
        assert total == 120, f"全部小限应覆盖1-120岁共120个，实得 {total}"


# ──────────────────────────────────────────────────────────────
# 大运四化 + 博士流曜
# ──────────────────────────────────────────────────────────────
class TestDayunEnrichment:
    def setup_method(self):
        self.chart = ziwei_full(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY,
                                GOLDEN_HOUR, GOLDEN_MIN, GOLDEN_GENDER)

    def test_dayun_sihua_nonempty(self):
        for d in self.chart.dayun.items:
            assert len(d.sihua) > 0, f"第{d.index}柱大运({d.ganzhi})应有四化"

    def test_dayun_sihua_count(self):
        # 每柱大运恰好有4条四化
        for d in self.chart.dayun.items:
            assert len(d.sihua) == 4, \
                f"第{d.index}柱大运({d.ganzhi})四化应有4条，实得 {len(d.sihua)}"

    def test_dayun_boshi_12_stars(self):
        for d in self.chart.dayun.items:
            assert len(d.boshi_stars) == 12, \
                f"第{d.index}柱大运博士流曜应有12颗，实得 {len(d.boshi_stars)}"

    def test_dayun_boshi_keys(self):
        expected = {"博士", "力士", "青龙", "小耗", "将军", "奏书",
                    "飞廉", "喜神", "病符", "大耗", "伏兵", "官府"}
        for d in self.chart.dayun.items:
            assert set(d.boshi_stars.keys()) == expected, \
                f"博士流曜名称不符: {set(d.boshi_stars.keys()) - expected}"


# ──────────────────────────────────────────────────────────────
# 真太阳时
# ──────────────────────────────────────────────────────────────
class TestTrueSolarTime:
    def test_no_longitude_empty(self):
        chart = ziwei_full(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY,
                           GOLDEN_HOUR, GOLDEN_MIN, GOLDEN_GENDER)
        assert chart.true_solar_time == "", "不传经度时 true_solar_time 应为空"

    def test_with_longitude_has_value(self):
        # 东经116.4度（北京附近）
        chart = ziwei_full(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY,
                           GOLDEN_HOUR, GOLDEN_MIN, GOLDEN_GENDER, longitude=116.4)
        assert chart.true_solar_time != "", "传入经度后 true_solar_time 不应为空"
        assert ":" in chart.true_solar_time, "true_solar_time 格式应为 HH:MM"

    def test_solar_time_format(self):
        chart = ziwei_full(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY,
                           GOLDEN_HOUR, GOLDEN_MIN, GOLDEN_GENDER, longitude=121.5)
        parts = chart.true_solar_time.split(":")
        assert len(parts) == 2
        assert int(parts[0]) in range(24)
        assert int(parts[1]) in range(60)


# ──────────────────────────────────────────────────────────────
# _place_ziwei 奇加偶减算法验证
# ──────────────────────────────────────────────────────────────
class TestPlaceZiwei:
    """验证紫微定位（设计文档 03-紫微星定位.md）。"""

    def _ziwei_branch(self, day: int, ju: int) -> int:
        from services.ziwei_engine.stars_main import _place_ziwei
        return _place_ziwei(day, ju)

    def test_exact_divisible_water2_day30(self):
        # 水二局 day=30 → 15 → 3(辰)
        assert self._ziwei_branch(30, 2) == 4

    def test_exact_divisible_wood3_day3(self):
        assert self._ziwei_branch(3, 3) == 2  # 寅

    def test_design_earth5_day14(self):
        # 土五局14日 → 卯(3)
        assert self._ziwei_branch(14, 5) == 3

    def test_design_wood3_day22(self):
        # 木三局22日 → 亥(11)
        assert self._ziwei_branch(22, 3) == 11

    def test_design_gold4_day27(self):
        # 金四局27日 → 未(7)
        assert self._ziwei_branch(27, 4) == 7

    def test_zw02_fire6_day21(self):
        # 火六局21日（ZW02 农历日）→ 寅(2)
        assert self._ziwei_branch(21, 6) == 2


# ──────────────────────────────────────────────────────────────
# 飞星对冲 + 自化
# ──────────────────────────────────────────────────────────────
class TestFlyingOppositionSelfTransform:
    def setup_method(self):
        self.chart = ziwei_full(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY,
                                GOLDEN_HOUR, GOLDEN_MIN, GOLDEN_GENDER)

    def test_opposition_palace_field_exists(self):
        """每个飞星宫位应有 opposition_palace 字段且非空。"""
        assert self.chart.flying is not None
        for fp in self.chart.flying.palaces:
            assert fp.opposition_palace != "", \
                f"{fp.palace_name} 应有对冲宫位字段"

    def test_opposition_is_6_apart(self):
        """命宫(0)对冲迁移宫(6)，兄弟宫(1)对冲交友宫(7)等。"""
        from services.ziwei_engine.tables import PALACE_NAMES
        fly = self.chart.flying
        assert fly is not None
        for fp in fly.palaces:
            opp_idx = (fp.palace_idx + 6) % 12
            expected_opp = PALACE_NAMES[opp_idx]
            assert fp.opposition_palace == expected_opp, \
                f"{fp.palace_name}(idx={fp.palace_idx})对冲应为{expected_opp}，实得{fp.opposition_palace}"

    def test_chonged_dict_has_all_palaces(self):
        """chonged 字典应包含全部12宫名。"""
        from services.ziwei_engine.tables import PALACE_NAMES
        fly = self.chart.flying
        assert fly is not None
        for name in PALACE_NAMES:
            assert name in fly.chonged, f"chonged 中缺失 {name}"

    def test_chonged_symmetric_with_received(self):
        """飞化落入X宫时，X的对面宫Y应在chonged[Y]有对应条目数。"""
        fly = self.chart.flying
        assert fly is not None
        from services.ziwei_engine.tables import PALACE_NAMES
        pname_to_idx = {n: i for i, n in enumerate(PALACE_NAMES)}
        total_received = sum(len(v) for v in fly.received.values())
        total_chonged = sum(len(v) for v in fly.chonged.values())
        # 每一条 received 对应一条 chonged（一对一）
        assert total_chonged == total_received, \
            f"received总计({total_received})应等于chonged总计({total_chonged})"

    def test_self_transforms_list_exists(self):
        """self_transforms 字段应存在（可为空列表）。"""
        fly = self.chart.flying
        assert fly is not None
        assert isinstance(fly.self_transforms, list)


# ──────────────────────────────────────────────────────────────
# 流月四化
# ──────────────────────────────────────────────────────────────
class TestLiuyueSihua:
    def setup_method(self):
        self.chart = ziwei_full(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY,
                                GOLDEN_HOUR, GOLDEN_MIN, GOLDEN_GENDER)

    def test_liuyue_has_sihua(self):
        """每个流月应有 sihua 字段且为4条。"""
        for d in self.chart.liuyue_data:
            assert d.sihua, f"第{d.month}月缺少sihua字段"
            assert len(d.sihua) == 4, \
                f"第{d.month}月四化应有4条，实得{len(d.sihua)}"

    def test_liuyue_sihua_keys(self):
        """四化值应包含化禄/化权/化科/化忌之一。"""
        valid_hua = {"化禄", "化权", "化科", "化忌"}
        for d in self.chart.liuyue_data:
            for star, hua in d.sihua.items():
                assert hua in valid_hua, \
                    f"第{d.month}月四化值'{hua}'不合法"


# ──────────────────────────────────────────────────────────────
# 空宫借对宫、opposition_name 字段
# ──────────────────────────────────────────────────────────────
class TestOppositionName:
    def setup_method(self):
        self.chart = ziwei_full(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY,
                                GOLDEN_HOUR, GOLDEN_MIN, GOLDEN_GENDER)

    def test_all_palaces_have_opposition_name(self):
        """每个宫位应有 opposition_name 字段且非空。"""
        for p in self.chart.palaces:
            assert p.opposition_name != "", \
                f"{p.name}(idx={p.index}) 应有对宫名称"

    def test_opposition_name_is_correct(self):
        """命宫(0)对迁移宫(6)，验证各宫对宫正确。"""
        from services.ziwei_engine.tables import PALACE_NAMES
        for p in self.chart.palaces:
            expected = PALACE_NAMES[(p.index + 6) % 12]
            assert p.opposition_name == expected, \
                f"{p.name}对宫应为{expected}，实得{p.opposition_name}"

    def test_empty_palace_analysis_borrows(self):
        """空宫的 analysis 应包含借对宫字样。"""
        empty_palaces = [p for p in self.chart.palaces if not p.main_stars]
        for p in empty_palaces:
            assert "借" in p.analysis or "空宫" in p.analysis, \
                f"空宫{p.name}的analysis应包含'借'或'空宫'字样"


# ──────────────────────────────────────────────────────────────
# 综合运势预测 (ForecastResult)
# ──────────────────────────────────────────────────────────────
class TestForecast:
    """验证运势预测引擎基本正确性。"""
    from services.ziwei_engine.forecast import ForecastResult as _FR
    fc: _FR  # narrowed type; setup assigns Optional[ForecastResult] with type: ignore

    def setup_method(self):
        self.chart = ziwei_full(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY,
                                GOLDEN_HOUR, GOLDEN_MIN, GOLDEN_GENDER)
        self.fc = self.chart.forecast  # type: ignore[assignment]

    def test_forecast_not_none(self):
        """forecast 字段不应为 None。"""
        assert self.fc is not None, "ZiweiChart.forecast 不应为 None"

    def test_yearly_has_palace_name(self):
        """年运 palace_name 应为有效本命宫位名。"""
        from services.ziwei_engine.tables import PALACE_NAMES
        assert self.fc.yearly.palace_name in PALACE_NAMES, \
            f"年运宫位名不合法: {self.fc.yearly.palace_name}"

    def test_yearly_score_in_range(self):
        """年运评分应在 1-100 之间。"""
        score = self.fc.yearly.score
        assert 1 <= score <= 100, f"年运评分应在1-100，实得{score}"

    def test_yearly_has_overall(self):
        """年运 overall 不应为空。"""
        assert self.fc.yearly.overall != "", "年运 overall 不应为空"

    def test_yearly_has_ganzhi(self):
        """年运 ganzhi 不应为空。"""
        assert self.fc.yearly.ganzhi != "", "年运 ganzhi 不应为空"

    def test_yearly_has_advice(self):
        """年运 advice 不应为空。"""
        assert self.fc.yearly.advice != "", "年运 advice 不应为空"

    def test_yearly_details_keys(self):
        """年运 details 应有感情/财运/事业/健康四个维度。"""
        expected = {"感情", "财运", "事业", "健康"}
        actual = set(self.fc.yearly.details.keys())
        assert actual >= expected, f"年运 details 缺少维度: {expected - actual}"

    def test_monthly_count(self):
        """月运列表应有12项。"""
        assert len(self.fc.monthly) == 12, \
            f"月运列表应有12项，实得{len(self.fc.monthly)}"

    def test_monthly_all_have_ganzhi(self):
        """每个月运都应有 ganzhi。"""
        for m in self.fc.monthly:
            assert m.ganzhi != "", f"{m.period} 月运 ganzhi 不应为空"

    def test_monthly_score_in_range(self):
        """每个月运评分应在 1-100 之间。"""
        for m in self.fc.monthly:
            assert 1 <= m.score <= 100, \
                f"{m.period} 月运评分应在1-100，实得{m.score}"

    def test_monthly_palace_names_valid(self):
        """每个月运的 palace_name 应为有效本命宫位名。"""
        from services.ziwei_engine.tables import PALACE_NAMES
        for m in self.fc.monthly:
            assert m.palace_name in PALACE_NAMES, \
                f"{m.period} 月运宫位名不合法: {m.palace_name}"

    def test_current_month_not_none(self):
        """current_month 不应为 None。"""
        assert self.fc.current_month is not None

    def test_current_month_in_monthly(self):
        """current_month 应与 monthly 中对应月份一致。"""
        import datetime
        cur = datetime.date.today().month
        # monthly 按农历月排列，正月=1
        matching = [m for m in self.fc.monthly
                    if self.fc.current_month.ganzhi == m.ganzhi]
        assert len(matching) >= 1, "current_month 应能在 monthly 中找到"

    def test_events_have_valid_level(self):
        """所有事件 level 应为 强/中/弱 之一。"""
        valid_levels = {"强", "中", "弱"}
        for e in self.fc.yearly.events:
            assert e.level in valid_levels, \
                f"事件 level 不合法: {e.level}"
        for m in self.fc.monthly:
            for e in m.events:
                assert e.level in valid_levels, \
                    f"{m.period} 事件 level 不合法: {e.level}"

    def test_events_have_source(self):
        """所有事件 source 不应为空。"""
        for e in self.fc.yearly.events:
            assert e.source != "", f"年运事件 source 不应为空: {e.category}"

    def test_forecast_from_engine_integration(self):
        """从引擎直接测试 generate_forecast 函数。"""
        from services.ziwei_engine.forecast import generate_forecast
        fc2 = generate_forecast(self.chart, 2026)
        assert fc2.year == 2026
        assert fc2.yearly is not None
        assert len(fc2.monthly) == 12

    def test_forecast_different_years(self):
        """不同流年应产生不同的运势预测（不同大运/流年四化）。"""
        from services.ziwei_engine.forecast import generate_forecast
        fc_2026 = generate_forecast(self.chart, 2026)
        fc_2027 = generate_forecast(self.chart, 2027)
        # 年份不同
        assert fc_2026.year != fc_2027.year
        # 干支不同（2026=丙午, 2027=丁未）
        assert fc_2026.yearly.ganzhi != fc_2027.yearly.ganzhi, \
            f"2026与2027年干支应不同，均为{fc_2026.yearly.ganzhi}"


# ──────────────────────────────────────────────────────────────
# Phase 1B P0：口径修正回归
# ──────────────────────────────────────────────────────────────
class TestZiweiPhase1BP0:
    """Z-P0-01 ~ Z-P0-04：日支、安星、流年、斗君流月。"""

    def setup_method(self):
        from services.ziwei_engine.lunar import solar_to_lunar
        from services.ziwei_engine.palaces import calc_palaces
        from services.ziwei_engine.stars_aux import place_aux_stars

        self.lunar = solar_to_lunar(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY, GOLDEN_HOUR, GOLDEN_MIN)
        self.layout = calc_palaces(self.lunar)
        self.aux = place_aux_stars(self.lunar, lp_b=self.layout.life_branch_idx)

    def test_day_branch_idx_populated(self):
        from services.ziwei_engine.tables import BRANCHES

        assert self.lunar.day_gz[1] == BRANCHES[self.lunar.day_branch_idx]
        assert 0 <= self.lunar.day_branch_idx <= 11

    def test_wenchang_wenqu_by_hour(self):
        # 未时(7)：文昌卯(3)，文曲亥(11)
        assert self.aux["文昌"] == 3
        assert self.aux["文曲"] == 11

    def test_youbi_by_month(self):
        # 正月：右弼酉(9)
        assert self.aux["右弼"] == 9

    def test_santai_bazuo_use_day_branch(self):
        zuofu = self.aux["左辅"]
        youbi = self.aux["右弼"]
        db = self.lunar.day_branch_idx
        assert self.aux["三台"] == (zuofu + db) % 12
        assert self.aux["八座"] == (youbi - db + 12) % 12

    def test_liunian_taisui(self):
        from services.ziwei_engine.liunian import calc_liunian

        ln = calc_liunian(2026, GOLDEN_YEAR, self.layout.life_branch_idx)
        assert ln.liunian_life_method == "taisui"
        assert ln.year_branch_idx == 6  # 午
        assert ln.life_palace_branch == 6

    def test_doujun_liuyue(self):
        from services.ziwei_engine.liunian import calc_doujun, calc_liunian, calc_liuyue_list

        ln = calc_liunian(2026, GOLDEN_YEAR, self.layout.life_branch_idx)
        doujun = calc_doujun(ln.year_branch_idx, self.lunar.calc_lunar_month, self.lunar.hour_branch_idx)
        assert doujun == 1  # 丑

        branch_map = {b: f"宫{b}" for b in range(12)}
        items = calc_liuyue_list(
            ln,
            branch_map,
            birth_month=self.lunar.calc_lunar_month,
            birth_hour_branch=self.lunar.hour_branch_idx,
            liuyue_method="doujun",
        )
        assert items[0].liuyue_method == "doujun"
        assert items[0].doujun_branch == 1
        assert items[0].life_palace_branch == 1

    def test_legacy_methods_still_available(self):
        from services.ziwei_engine.stars_aux import place_aux_stars

        legacy = place_aux_stars(
            self.lunar,
            lp_b=self.layout.life_branch_idx,
            wenchang_method="year_branch",
            youbi_method="hour",
        )
        yb = self.lunar.year_branch_idx
        hb = self.lunar.hour_branch_idx
        assert legacy["文昌"] == (9 - yb) % 12
        assert legacy["文曲"] == (4 + yb) % 12
        assert legacy["右弼"] == (10 - hb) % 12


# ──────────────────────────────────────────────────────────────
# Phase 2 P1：结构补齐回归
# ──────────────────────────────────────────────────────────────
class TestZiweiPhase2P1:
    """Z-P1-01 ~ Z-P1-06：LiuyueInfo、missing_fields、身宫、小限、真太阳时、月德。"""

    def setup_method(self):
        self.chart = ziwei_full(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY,
                                GOLDEN_HOUR, GOLDEN_MIN, GOLDEN_GENDER)

    def test_liuyue_data_is_liuyue_info(self):
        from services.ziwei_engine.liunian import LiuyueInfo

        assert len(self.chart.liuyue_data) == 12
        assert all(isinstance(d, LiuyueInfo) for d in self.chart.liuyue_data)

    def test_body_palace_flag(self):
        body_palaces = [p for p in self.chart.palaces if p.is_body_palace]
        assert len(body_palaces) == 1
        assert body_palaces[0].branch_idx == self.chart.body_palace_branch

    def test_yuede_star_placed(self):
        from services.ziwei_engine.lunar import solar_to_lunar
        from services.ziwei_engine.palaces import calc_palaces
        from services.ziwei_engine.stars_aux import place_aux_stars

        lunar = solar_to_lunar(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY, GOLDEN_HOUR, GOLDEN_MIN)
        layout = calc_palaces(lunar)
        aux = place_aux_stars(lunar, lp_b=layout.life_branch_idx)
        assert "月德" in aux
        yb = lunar.year_branch_idx
        assert aux["月德"] == yb % 12
        assert aux.get("天德") == (9 + yb) % 12

    def test_missing_fields_empty_on_success(self):
        assert isinstance(self.chart.missing_fields, list)
        assert "true_solar_time" not in self.chart.missing_fields

    def test_xiaoxian_standard_default(self):
        chen = next(p for p in self.chart.palaces if p.branch_idx == 4)
        assert 1 in chen.xiaoxian_ages


# ──────────────────────────────────────────────────────────────
# Phase 3 P2：流日/流时、格局增强
# ──────────────────────────────────────────────────────────────
class TestZiweiPhase3P2:
    def test_liuri_liushi_integration(self):
        chart = ziwei_full(
            GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY,
            GOLDEN_HOUR, GOLDEN_MIN, GOLDEN_GENDER,
            flow_lunar_day=3,
            flow_liuyue_month=1,
            flow_hour_branch=7,  # 未时
        )
        assert chart.liuri_liushi is not None
        assert chart.liuri_liushi.liuri.lunar_day == 3
        assert chart.liuri_liushi.liushi.hour_branch_idx == 7

    def test_patterns_include_enhanced_checks(self):
        chart = ziwei_full(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY,
                           GOLDEN_HOUR, GOLDEN_MIN, GOLDEN_GENDER)
        names = {p.name for p in chart.patterns}
        # 至少应检测到若干已知格局（吉或凶）
        assert len(names) >= 1

    def test_pattern_tiers_top20_are_canonical(self):
        """Top-20 ZRULE_001–020 格局应标记为 canonical tier。"""
        chart = ziwei_full(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY,
                           GOLDEN_HOUR, GOLDEN_MIN, GOLDEN_GENDER)
        canonical_rules = {f"ZRULE_{i:03d}" for i in range(1, 21)}
        for p in chart.patterns:
            if p.rule_id in canonical_rules:
                assert getattr(p, "tier", "") == "canonical", (
                    f"{p.name} ({p.rule_id}) expected canonical, got {getattr(p, 'tier', None)}"
                )

    def test_pattern_tier_field_present(self):
        chart = ziwei_full(GOLDEN_YEAR, GOLDEN_MONTH, GOLDEN_DAY,
                           GOLDEN_HOUR, GOLDEN_MIN, GOLDEN_GENDER)
        for p in chart.patterns:
            assert getattr(p, "tier", None) in ("canonical", "extended", "heuristic")
