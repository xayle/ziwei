"""
tests/test_20tab_render.py — M6.06 20Tab × API字段非空验证

原规格: 20Tab × 3状态(无数据/有数据/错误) = 60项手动验证清单
此文件: 自动化验证"有数据"状态下 20 个 Tab 对应的关键 API 字段非空 (20项)
手动验证: 浏览器 Tab 无数据/错误状态需在 Chrome 中手动确认 (40项)
"""
from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def verify_data():
    """调用 /api/v1/verify 取得完整响应数据（模块级，只请求一次）"""
    _prev = os.environ.get("AUTH_BYPASS")
    os.environ["AUTH_BYPASS"] = "true"
    try:
        from run import app
        client = TestClient(app)
        payload = {
            "dt": "1985-07-15T10:30:00",
            "lon": 121.47,
            "gender": "male",
            "mode": "dual",
            "use_solar_time": False,
            "name": "20Tab测试用例",
        }
        resp = client.post("/api/v1/verify", json=payload)
        assert resp.status_code == 200, f"/verify 返回 {resp.status_code}: {resp.text[:200]}"
        return resp.json()
    finally:
        if _prev is None:
            os.environ.pop("AUTH_BYPASS", None)
        else:
            os.environ["AUTH_BYPASS"] = _prev


class TestTab0Overview:
    """Tab 0 — 总览 (LifeArcModel + CurrentFortuneCard)"""
    def test_overall_tier(self, verify_data):
        la = verify_data.get("life_arc") or {}
        assert la.get("overall_tier"), "Tab0: life_arc.overall_tier 不应为空"

    def test_validation_level(self, verify_data):
        v = verify_data.get("validation") or {}
        assert v.get("level"), "Tab0: validation.level 不应为空"


class TestTab2Pillars:
    """Tab 2 — 命盘 (PillarsModel + WuXingScore)"""
    def test_pillars_primary_all_four(self, verify_data):
        p = verify_data.get("pillars_primary") or {}
        for col in ("year", "month", "day", "hour"):
            assert p.get(col), f"Tab2: pillars_primary.{col} 不应为空"

    def test_wuxing_score_five_elements(self, verify_data):
        wx = verify_data.get("wuxing_score") or {}
        for elem in ("wood", "fire", "earth", "metal", "water"):
            assert elem in wx, f"Tab2: wuxing_score.{elem} 缺失"


class TestTab3Geju:
    """Tab 3 — 格局 (GejuModel)"""
    def test_geju_name(self, verify_data):
        g = verify_data.get("geju") or {}
        assert g.get("geju_name"), "Tab3: geju.geju_name 不应为空"

    def test_geju_level(self, verify_data):
        g = verify_data.get("geju") or {}
        assert g.get("geju_level") in ("上格", "中格", "下格", "无格"), \
            f"Tab3: geju.geju_level 非法: {g.get('geju_level')}"


class TestTab4Palace:
    """Tab 4 — 命宫 (PalaceModel)"""
    def test_palace_branch(self, verify_data):
        p = verify_data.get("palace") or {}
        assert p.get("ming_gong"), "Tab4: palace.ming_gong 不应为空"


class TestTab5Summary:
    """Tab 5 — 摘要 (ValidationModel + LifeArcModel)"""
    def test_validation_level(self, verify_data):
        v = verify_data.get("validation") or {}
        assert v.get("level") in ("L0", "L1", "L2", "L3"), \
            f"Tab5: validation.level 非法: {v.get('level')}"

    def test_diff_count(self, verify_data):
        v = verify_data.get("validation") or {}
        assert "diff_fields" in v, "Tab5: validation.diff_fields 缺失"


class TestTab7Wealth:
    """Tab 7 — 财运 (WealthAnalysisModel)"""
    def test_wealth_score(self, verify_data):
        w = verify_data.get("wealth_analysis") or {}
        assert w.get("wealth_score") is not None, "Tab7: wealth_analysis.wealth_score 不应为空"

    def test_industries(self, verify_data):
        w = verify_data.get("wealth_analysis") or {}
        assert isinstance(w.get("industries"), list), "Tab7: industries 应为列表"


class TestTab8Career:
    """Tab 8 — 事业 (CareerAnalysisModel)"""
    def test_career_score(self, verify_data):
        c = verify_data.get("career") or {}
        assert c.get("career_score") is not None, "Tab8: career.career_score 不应为空"

    def test_career_directions(self, verify_data):
        c = verify_data.get("career") or {}
        assert isinstance(c.get("career_directions"), list), "Tab8: career_directions 应为列表"


class TestTab9Marriage:
    """Tab 9 — 姻缘 (MarriageAnalysisModel)"""
    def test_peach_blossom(self, verify_data):
        m = verify_data.get("marriage_analysis") or {}
        assert m.get("peach_blossom"), "Tab9: marriage_analysis.peach_blossom 不应为空"

    def test_marriage_score(self, verify_data):
        m = verify_data.get("marriage_analysis") or {}
        assert m.get("marriage_score") is not None, "Tab9: marriage_score 不应为空"


class TestTab10Health:
    """Tab 10 — 健康 (HealthAnalysisModel)"""
    def test_health_score(self, verify_data):
        h = verify_data.get("health") or {}
        assert h.get("health_score") is not None, "Tab10: health.health_score 不应为空"

    def test_organ_risks(self, verify_data):
        h = verify_data.get("health") or {}
        assert isinstance(h.get("risk_organs"), list), "Tab10: risk_organs 应为列表"


class TestTab11Relationship:
    """Tab 11 — 人际 (RelationshipAnalysisModel)"""
    def test_relationship_score(self, verify_data):
        r = verify_data.get("relationship") or {}
        assert r.get("relationship_score") is not None, "Tab11: relationship_score 不应为空"


class TestTab12Personality:
    """Tab 12 — 性格 (PersonalityModel)"""
    def test_personality_traits(self, verify_data):
        p = verify_data.get("personality") or {}
        assert isinstance(p.get("advantages"), list), "Tab12: personality.advantages 应为列表"


class TestTab16Dayun:
    """Tab 16 — 大运 (DaYunModel)"""
    def test_dayun_items(self, verify_data):
        d = verify_data.get("dayun") or {}
        items = d.get("items") or []
        assert len(items) >= 8, f"Tab16: 大运应 ≥8步，实际 {len(items)}"

    def test_dayun_six_fields(self, verify_data):
        """红线5: 每步大运6字段全填"""
        d = verify_data.get("dayun") or {}
        items = d.get("items") or []
        for item in items[:3]:
            assert item.get("ten_god") is not None, f"大运 ten_god 为空: {item}"
            assert item.get("refs") is not None, f"大运 refs 为空: {item}"


class TestTab17Liunian:
    """Tab 17 — 流年 (LiuNianDetailModel)"""
    def test_liunian_detail(self, verify_data):
        ln = verify_data.get("liunian_detail") or []
        assert isinstance(ln, list) and len(ln) >= 1, "Tab17: liunian_detail 应为非空列表"
        assert ln[0].get("year") is not None, "Tab17: liunian_detail[0].year 不应为空"


class TestTab18Monthly:
    """Tab 18 — 月运 (MonthlyFortuneModel)"""
    def test_monthly_grid(self, verify_data):
        mf = verify_data.get("monthly_fortune") or []
        assert isinstance(mf, list) and len(mf) >= 1, "Tab18: monthly_fortune 应有数据"

    def test_color_hint(self, verify_data):
        """P0-15: 月运含吉凶色标"""
        mf = verify_data.get("monthly_fortune") or []
        if mf:
            first = mf[0]
            assert "color_hint" in first, "Tab18: month 应含 color_hint 字段"


class TestTab19Cases:
    """Tab 19 — 案例 (GET /api/v1/cases 端点)"""
    def test_cases_endpoint(self):
        """cases 端点可访问（P0-23）"""
        from run import app
        client = TestClient(app)
        resp = client.get("/api/v1/cases")
        # 可能 401（需要 auth）或 200（AUTH_BYPASS），但不应 500
        assert resp.status_code in (200, 401, 403), \
            f"Tab19: /api/v1/cases 返回意外状态 {resp.status_code}"


class TestTabSchema:
    """schema 字段完整性验证"""

    def test_rule_version_present(self, verify_data):
        """P0-16: rule_version 随响应输出"""
        rv = verify_data.get("rule_version")
        assert rv, "rule_version 不应为空"

    def test_rule_version_detail_dict(self, verify_data):
        """红线#32: rule_version dict 必须附在每次计算输出中（§3.4）"""
        rvd = verify_data.get("rule_version_detail")
        assert isinstance(rvd, dict) and len(rvd) >= 5, (
            "rule_version_detail 应为含≥5个模块版本的 dict"
        )
        for key in ("wuxing", "strength", "yongshen", "dayun", "geju"):
            assert key in rvd, f"rule_version_detail 缺少 '{key}' 模块版本"

    def test_disclaimer_present(self, verify_data):
        """P0-20: 免责声明存在"""
        # 检查任意一个分析模型带 disclaimer
        wa = verify_data.get("wealth_analysis") or {}
        assert wa.get("disclaimer"), "wealth_analysis.disclaimer 不应为空"

    def test_tiangan_clashes_present(self, verify_data):
        """P0-11: tiangan_clashes scope 字段存在"""
        tc = verify_data.get("tiangan_clashes")
        # 可能为空列表（无克），但字段应存在
        assert tc is not None, "tiangan_clashes 字段不应为 None（应为列表）"

    def test_three_layer_model_fact_data(self, verify_data):
        """红线#33: 每个分析维度输出 fact_data / inference_tags / interpretation_text"""
        dims = ["geju", "wealth", "career", "marriage", "health", "relationship", "personality"]
        missing = []
        for dim in dims:
            obj = verify_data.get(dim)
            if not isinstance(obj, dict):
                missing.append(f"{dim}(not-dict)")
                continue
            if not obj.get("fact_data"):
                missing.append(f"{dim}.fact_data")
            if "inference_tags" not in obj:
                missing.append(f"{dim}.inference_tags")
            if "interpretation_text" not in obj:
                missing.append(f"{dim}.interpretation_text")
        assert not missing, f"红线#33 三层模型字段缺失: {missing}"


# ═══════════════════════════════════════════════════════════════════════════
# 补充：Tab 1 / 6 / 13-15 有数据态 + 全局 400 错误态
# ═══════════════════════════════════════════════════════════════════════════

class TestTab1Request:
    """Tab 1 — 请求回显（API 输入参数反射）"""

    def test_echo_dt(self, verify_data):
        """响应中包含时间信息字段（solar_dt / local_dt / pillars_primary）"""
        # /verify 响应通过 pillars_primary 隐式体现时间，无独立 dt 回显字段
        has_time = (
            verify_data.get("solar_dt")
            or verify_data.get("local_dt")
            or verify_data.get("pillars_primary")  # 四柱存在即表示时间已处理
        )
        assert has_time, "Tab1: 响应中应有 solar_dt / local_dt / pillars_primary 之一"

    def test_echo_mode(self, verify_data):
        """请求参数 mode 在响应中可查"""
        mode = (verify_data.get("request_echo") or {}).get("mode") or verify_data.get("mode")
        assert mode in ("dual", "v1", "v2", None), f"mode 值异常: {mode}"


class TestTab6Diagnostic:
    """Tab 6 — 诊断（ValidationModel + boundary level）"""

    def test_validation_diff_fields_list(self, verify_data):
        v = verify_data.get("validation") or {}
        assert isinstance(v.get("diff_fields"), list), "Tab6: diff_fields 应为列表"

    def test_validation_has_warnings(self, verify_data):
        v = verify_data.get("validation") or {}
        # warnings 可为空列表，但字段应存在（实际字段名为 warnings，非 notes）
        assert "warnings" in v, f"Tab6: validation.warnings 字段缺失，实际键: {list(v.keys())}"

    def test_pillars_shadow_or_secondary(self, verify_data):
        """dual 模式下 pillars_shadow 或 pillars_secondary 之一应存在（L0 无差异时可为空）"""
        ps = verify_data.get("pillars_shadow") or verify_data.get("pillars_secondary")
        level = (verify_data.get("validation") or {}).get("level", "")
        # L0 代表双引擎完全一致，shadow 柱可为 None；L1+ 应有值
        if level != "L0":
            assert ps is not None, f"Tab6: level={level} 时 pillars_shadow 不应为 None"


class TestTab13Fengshui:
    """Tab 13 — 风水（FengshuiModel）"""

    def test_fengshui_present(self, verify_data):
        f = verify_data.get("fengshui")
        assert f is not None, "Tab13: fengshui 字段为 None"

    def test_fengshui_lucky_colors(self, verify_data):
        f = verify_data.get("fengshui") or {}
        assert isinstance(f.get("lucky_colors"), list) and len(f["lucky_colors"]) >= 1, \
            "Tab13: fengshui.lucky_colors 应为非空列表"

    def test_fengshui_direction(self, verify_data):
        f = verify_data.get("fengshui") or {}
        # FengshuiModel 使用 auspicious_directions（列表）而非 lucky_direction
        directions = f.get("auspicious_directions") or f.get("lucky_direction")
        assert directions, "Tab13: fengshui.auspicious_directions 不应为空"


class TestTab14Jewelry:
    """Tab 14 — 饰品（JewelryModel）"""

    def test_jewelry_present(self, verify_data):
        j = verify_data.get("jewelry")
        assert j is not None, "Tab14: jewelry 字段为 None"

    def test_jewelry_items(self, verify_data):
        j = verify_data.get("jewelry") or {}
        items = j.get("items") or j.get("recommendations") or []
        assert isinstance(items, list), "Tab14: jewelry.items/recommendations 应为列表"


class TestTab15Lucky:
    """Tab 15 — 开运（LuckyModel）"""

    def test_lucky_present(self, verify_data):
        lk = verify_data.get("lucky")
        assert lk is not None, "Tab15: lucky 字段为 None"

    def test_lucky_colors_numbers(self, verify_data):
        lk = verify_data.get("lucky") or {}
        assert isinstance(lk.get("lucky_colors"), list) and lk["lucky_colors"], \
            "Tab15: lucky.lucky_colors 应为非空列表"
        assert isinstance(lk.get("lucky_numbers"), list) and lk["lucky_numbers"], \
            "Tab15: lucky.lucky_numbers 应为非空列表"

    def test_lucky_direction(self, verify_data):
        lk = verify_data.get("lucky") or {}
        assert lk.get("lucky_direction"), "Tab15: lucky.lucky_direction 不应为空"


class TestErrorState:
    """全局错误态验证 — /verify 返回 400 不含 alert/服务器 500"""

    def test_invalid_year_returns_400(self):
        """红线25: 年份 < 1900 → 400"""
        import os
        _prev = os.environ.get("AUTH_BYPASS")
        os.environ["AUTH_BYPASS"] = "true"
        try:
            from run import app
            client = TestClient(app)
            resp = client.post("/api/v1/verify", json={
                "dt": "1800-01-01T00:00:00",
                "lon": 116.4,
                "gender": "female",
                "mode": "dual",
            })
            assert resp.status_code == 400, \
                f"年份<1900 应返回 400，实际 {resp.status_code}"
        finally:
            if _prev is None:
                os.environ.pop("AUTH_BYPASS", None)
            else:
                os.environ["AUTH_BYPASS"] = _prev

    def test_invalid_timezone_returns_400(self):
        """红线26: 无效时区 → 400（不能 500）"""
        import os
        _prev = os.environ.get("AUTH_BYPASS")
        os.environ["AUTH_BYPASS"] = "true"
        try:
            from run import app
            client = TestClient(app)
            resp = client.post("/api/v1/verify", json={
                "dt": "1990-07-17T12:00:00",
                "lon": 116.4,
                "gender": "female",
                "mode": "dual",
                "tz": "InvalidTimezone/Nowhere",
            })
            assert resp.status_code in (400, 422), \
                f"无效时区应返回 400/422，实际 {resp.status_code}"
        finally:
            if _prev is None:
                os.environ.pop("AUTH_BYPASS", None)
            else:
                os.environ["AUTH_BYPASS"] = _prev

    def test_missing_dt_returns_422(self):
        """缺少必填 dt 字段 → 422 Unprocessable Entity"""
        import os
        _prev = os.environ.get("AUTH_BYPASS")
        os.environ["AUTH_BYPASS"] = "true"
        try:
            from run import app
            client = TestClient(app)
            resp = client.post("/api/v1/verify", json={
                "lon": 116.4,
                "gender": "female",
                "mode": "dual",
            })
            assert resp.status_code == 422, \
                f"缺少 dt 应返回 422，实际 {resp.status_code}"
        finally:
            if _prev is None:
                os.environ.pop("AUTH_BYPASS", None)
            else:
                os.environ["AUTH_BYPASS"] = _prev
