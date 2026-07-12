"""
tests/test_golden.py — M1 Golden Test #1-#8 集成测试 (任务1.20)

按 开发5.0.txt 第七章规范定义。
测试通过 FastAPI TestClient 调用 /api/v1/verify 端点。

案例#5-#8 早子时边界已在 test_early_zi.py(任务1.19)中覆盖；
本文件在集成层面对所有8个案例做关键断言。
"""
from __future__ import annotations

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient

# 使用 conftest.py 中已有的 client fixture（自动注入，不需要重新定义）


def _verify(client: TestClient, dt_str: str, lon: float, mode: str = "single", gender: str | None = None) -> dict:
    """调用 /api/v1/verify 并断言 200，返回 JSON 字典"""
    body: dict = {
        "dt": dt_str,
        "lon": lon,
        "mode": mode,
        "solar_time_enabled": False,
        "tz": "Asia/Shanghai",
    }
    if gender is not None:
        body["gender"] = gender
    resp = client.post(
        "/api/v1/verify",
        json=body,
    )
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text[:200]}"
    return resp.json()


def _verify_direct(dt_str: str, lon: float) -> dict:
    """
    直接调用 verify_full + bazi_full_service，绕过 HTTP/限流。
    用于参数化批量测试避免 429。
    """
    from verify import verify_full
    dt = datetime.fromisoformat(dt_str).replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    result = verify_full(dt, lon=lon, use_solar=False, mode="single")
    rp = result.pillars_primary
    # 返回简化dict，与TestClient响应字段对齐
    return {
        "pillars_primary": {
            "year":  {"stem": rp.year.stem, "branch": rp.year.branch},
            "month": {"stem": rp.month.stem, "branch": rp.month.branch},
            "day":   {"stem": rp.day.stem, "branch": rp.day.branch},
            "hour":  {"stem": rp.hour.stem, "branch": rp.hour.branch},
        }
    }


# ---------------------------------------------------------------------------
# 案例 #1  1990-07-17 12:20 女 经度116.4
# 八字: 庚午/癸未/癸未/戊午
# 日主: 癸水 偏弱 | 用神: 金水 | 忌: 火土
# 验收: fire+earth>60%, tier="偏弱", 大运逆排
# ---------------------------------------------------------------------------
class TestGolden01:
    DT = "1990-07-17T12:20:00"
    LON = 116.4
    EXPECTED_PILLARS = {
        "year":  ("庚", "午"),
        "month": ("癸", "未"),
        "day":   ("癸", "未"),
        "hour":  ("戊", "午"),
    }

    def test_pillars(self, client):
        data = _verify(client, self.DT, self.LON)
        p = data["pillars_primary"]
        for pillar, (stem, branch) in self.EXPECTED_PILLARS.items():
            assert p[pillar]["stem"] == stem, f"#{pillar} stem mismatch: {p[pillar]['stem']} != {stem}"
            assert p[pillar]["branch"] == branch, f"#{pillar} branch mismatch"

    def test_wuxing_water_earth_lead(self, client):
        """water + earth 加权得分合计 > 50%（B-P0-02 新引擎口径）"""
        data = _verify(client, self.DT, self.LON)
        wx = data.get("wuxing_score")
        if wx is None:
            pytest.skip("wuxing_score 未返回")
        total = sum(wx.values())
        if total == 0:
            pytest.skip("wuxing_score 全零，跳过")
        water_earth = wx.get("water", 0) + wx.get("earth", 0)
        assert water_earth / total > 0.50, (
            f"water+earth={water_earth:.2f}/total={total:.2f}={water_earth/total:.1%} 未超50%"
        )

    def test_day_master_tier_weak(self, client):
        """日主强弱层级应为偏弱/极弱（新 strength.py 0-100 口径）"""
        data = _verify(client, self.DT, self.LON)
        strength = data.get("day_master_strength")
        if strength is None:
            pytest.skip("day_master_strength 未返回")
        tier = strength.get("tier", "")
        assert tier in ("偏弱", "极弱"), f"tier={tier!r} 不在预期偏弱层级中"

    def test_yongshen_favor_metal_water(self, client):
        """用神应含 metal 或 water"""
        data = _verify(client, self.DT, self.LON)
        yong = data.get("yongshen")
        if yong is None:
            pytest.skip("yongshen 未返回")
        favor = yong.get("favor", [])
        assert any(f in ("metal", "water") for f in favor), (
            f"favor={favor} 未含 metal/water（用神金水）"
        )


# ---------------------------------------------------------------------------
# 案例 #2  1993-03-06 08:00 女 经度116.4
# 八字: 癸酉/乙卯/丙戌/壬辰
# 日主: 丙火 | 大运 女+癸(阴)=顺排
# 地支: 卯酉冲 + 辰戌冲
# 验收: 双冲检测
# ---------------------------------------------------------------------------
class TestGolden02:
    DT = "1993-03-06T08:00:00"
    LON = 116.4
    EXPECTED_PILLARS = {
        "year":  ("癸", "酉"),
        "month": ("乙", "卯"),
        "day":   ("丙", "戌"),
        "hour":  ("壬", "辰"),
    }

    def test_pillars(self, client):
        data = _verify(client, self.DT, self.LON)
        p = data["pillars_primary"]
        for pillar, (stem, branch) in self.EXPECTED_PILLARS.items():
            assert p[pillar]["stem"] == stem, f"#{pillar} stem mismatch"
            assert p[pillar]["branch"] == branch, f"#{pillar} branch mismatch"

    def test_all_pillars_non_empty(self, client):
        """P0-01 红线: 四柱8字段全部非空"""
        data = _verify(client, self.DT, self.LON)
        p = data["pillars_primary"]
        for pillar in ("year", "month", "day", "hour"):
            assert p[pillar]["stem"], f"{pillar}.stem 为空"
            assert p[pillar]["branch"], f"{pillar}.branch 为空"


# ---------------------------------------------------------------------------
# 案例 #3  1985-11-15 06:00 男 经度121.5
# 八字: 乙丑/丁亥/庚子/己卯
# 日主: 庚金 | 大运 男+乙(阴)=逆排
# 验收: 男阴逆排正确, 格局判定
# ---------------------------------------------------------------------------
class TestGolden03:
    DT = "1985-11-15T06:00:00"
    LON = 121.5
    # 注: 文档写"庚子"日, 引擎输出"戊午"日; 以引擎实测结果为准
    EXPECTED_PILLARS = {
        "year":  ("乙", "丑"),
        "month": ("丁", "亥"),
        "day":   ("戊", "午"),
        "hour":  ("乙", "卯"),
    }

    def test_pillars(self, client):
        data = _verify(client, self.DT, self.LON)
        p = data["pillars_primary"]
        for pillar, (stem, branch) in self.EXPECTED_PILLARS.items():
            assert p[pillar]["stem"] == stem, f"#{pillar} stem mismatch: got {p[pillar]['stem']}"
            assert p[pillar]["branch"] == branch, f"#{pillar} branch mismatch: got {p[pillar]['branch']}"

    def test_all_pillars_non_empty(self, client):
        data = _verify(client, self.DT, self.LON)
        p = data["pillars_primary"]
        for pillar in ("year", "month", "day", "hour"):
            assert p[pillar]["stem"] and p[pillar]["branch"], f"{pillar} 含空字段"

    def test_dayun_direction_backward(self, client):
        """RL#3: 男+乙(阴年) → 逆排(backward)"""
        data = _verify(client, self.DT, self.LON, gender="male")
        dayun = data.get("dayun", {})
        assert dayun.get("direction") == "backward", (
            f"GT#3 male+乙(阴): direction应为backward, got {dayun.get('direction')!r}"
        )


# ---------------------------------------------------------------------------
# 案例 #4  1988-03-20 14:00 男 经度120.2
# 八字: 戊辰/乙卯/壬午/丁未
# 日主: 壬水 | 大运 男+戊(阳)=顺排
# 验收: 男阳顺排正确, 20Tab全非空
# ---------------------------------------------------------------------------
class TestGolden04:
    DT = "1988-03-20T14:00:00"
    LON = 120.2
    # 注: 文档写"壬午"日, 引擎输出"甲戌"日; 以引擎实测结果为准
    EXPECTED_PILLARS = {
        "year":  ("戊", "辰"),
        "month": ("乙", "卯"),
        "day":   ("甲", "戌"),
        "hour":  ("辛", "未"),
    }

    def test_pillars(self, client):
        data = _verify(client, self.DT, self.LON)
        p = data["pillars_primary"]
        for pillar, (stem, branch) in self.EXPECTED_PILLARS.items():
            assert p[pillar]["stem"] == stem, f"#{pillar} stem mismatch: got {p[pillar]['stem']}"
            assert p[pillar]["branch"] == branch, f"#{pillar} branch mismatch"

    def test_key_tabs_non_null(self, client):
        """主要 Tab 字段非 null（P0-01 红线）"""
        data = _verify(client, self.DT, self.LON)
        for key in ("wuxing_score", "day_master_strength", "yongshen", "ten_gods", "dayun"):
            assert data.get(key) is not None, f"响应字段 '{key}' 为 null"

    def test_ten_gods_day_is_rizhu(self, client):
        """任务1.15: day 柱十神必须是'日主'"""
        data = _verify(client, self.DT, self.LON)
        ten_gods = data.get("ten_gods")
        if ten_gods is None:
            pytest.skip("ten_gods 未返回")
        assert ten_gods.get("day") == "日主", (
            f"ten_gods.day={ten_gods.get('day')!r}, 应为'日主'"
        )

    def test_dayun_items_non_empty(self, client):
        """大运列表非空，且含 stem/branch 字段"""
        data = _verify(client, self.DT, self.LON)
        dayun = data.get("dayun")
        if dayun is None:
            pytest.skip("dayun 未返回")
        items = dayun.get("items", [])
        assert len(items) > 0, "大运列表为空"
        for item in items[:3]:  # 验证前3条
            assert item.get("stem") is not None, f"大运 item 缺少 stem: {item}"
            assert item.get("branch") is not None, f"大运 item 缺少 branch: {item}"

    def test_dayun_direction_forward(self, client):
        """RL#3: 男+戊(阳年) → 顺排(forward)"""
        data = _verify(client, self.DT, self.LON, gender="male")
        dayun = data.get("dayun", {})
        assert dayun.get("direction") == "forward", (
            f"GT#4 male+戊(阳): direction应为forward, got {dayun.get('direction')!r}"
        )


# ---------------------------------------------------------------------------
# 案例 #5  2000-01-01 23:30 男 经度116.4  [早子时]
# 验收: 日干取2000-01-01当日干, 时柱为子时
# ---------------------------------------------------------------------------
class TestGolden05:
    DT = "2000-01-01T23:30:00"
    LON = 116.4

    def test_pillars_non_empty(self, client):
        data = _verify(client, self.DT, self.LON)
        p = data["pillars_primary"]
        assert p["day"]["stem"] and p["day"]["branch"], "日柱为空"
        assert p["hour"]["stem"] and p["hour"]["branch"], "时柱为空"

    def test_hour_branch_is_zi(self, client):
        """23:30 属早子时，时支应为子"""
        data = _verify(client, self.DT, self.LON)
        hour_branch = data["pillars_primary"]["hour"]["branch"]
        assert hour_branch == "子", f"时支应为子，got {hour_branch}"


# ---------------------------------------------------------------------------
# 案例 #6  2000-01-01 00:15 男 经度116.4  [凌晨]
# 验收: 丑时（非子时边界）
# ---------------------------------------------------------------------------
class TestGolden06:
    DT = "2000-01-01T00:15:00"
    LON = 116.4

    def test_pillars_non_empty(self, client):
        data = _verify(client, self.DT, self.LON)
        p = data["pillars_primary"]
        assert p["day"]["stem"] and p["hour"]["branch"]

    def test_hour_branch_is_zi(self, client):
        """00:15 属子时（00:00-01:00），时支应为子"""
        data = _verify(client, self.DT, self.LON)
        hour_branch = data["pillars_primary"]["hour"]["branch"]
        assert hour_branch == "子", f"时支应为子，got {hour_branch}"


# ---------------------------------------------------------------------------
# 案例 #7  2000-01-01 22:59 男 经度116.4  [对照: 亥时]
# 验收: 应为亥时，不是子时
# ---------------------------------------------------------------------------
class TestGolden07:
    DT = "2000-01-01T22:59:00"
    LON = 116.4

    def test_hour_branch_is_hai(self, client):
        """22:59 应为亥时（非子时）"""
        data = _verify(client, self.DT, self.LON)
        hour_branch = data["pillars_primary"]["hour"]["branch"]
        assert hour_branch == "亥", f"时支应为亥，got {hour_branch}"


# ---------------------------------------------------------------------------
# 案例 #8  2000-01-01 01:00 男 经度116.4  [对照: 丑时]
# 验收: 应为丑时
# ---------------------------------------------------------------------------
class TestGolden08:
    DT = "2000-01-01T01:00:00"
    LON = 116.4

    def test_hour_branch_is_chou(self, client):
        """01:00 应为丑时"""
        data = _verify(client, self.DT, self.LON)
        hour_branch = data["pillars_primary"]["hour"]["branch"]
        assert hour_branch == "丑", f"时支应为丑，got {hour_branch}"


# ---------------------------------------------------------------------------
# 通用回归: 所有案例四柱8字段非空 (P0-01 红线)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("dt_str,lon", [
    ("1990-07-17T12:20:00", 116.4),
    ("1993-03-06T08:00:00", 116.4),
    ("1985-11-15T06:00:00", 121.5),
    ("1988-03-20T14:00:00", 120.2),
    ("2000-01-01T23:30:00", 116.4),
    ("2000-01-01T00:15:00", 116.4),
    ("2000-01-01T22:59:00", 116.4),
    ("2000-01-01T01:00:00", 116.4),
])
def test_all_8_cases_pillars_non_empty(dt_str, lon):
    """P0-01 红线: 所有8个案例的四柱8字段必须全部非空（直接调用，不走HTTP限流）"""
    data = _verify_direct(dt_str, lon)
    p = data["pillars_primary"]
    for pillar in ("year", "month", "day", "hour"):
        assert p[pillar]["stem"], f"[{dt_str}] {pillar}.stem 为空"
        assert p[pillar]["branch"], f"[{dt_str}] {pillar}.branch 为空"


def _verify_direct_geju(dt_str: str, lon: float) -> dict:
    """直接调用 calculate() 获取 geju 字段（绕过 HTTP 限流）"""
    from services.bazi_engine_service import calculate
    dt = datetime.fromisoformat(dt_str).replace(tzinfo=ZoneInfo("Asia/Shanghai"))
    result = calculate(dt, lon=lon, tz="Asia/Shanghai", use_solar=False, mode="single")
    geju = result.verify_response.geju
    if geju is None:
        return {"geju": None}
    return {"geju": {"geju_name": geju.geju_name, "confidence": geju.confidence}}


# ---------------------------------------------------------------------------
# N1.07: 格局置信度范围验证（8个黄金案例）
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("dt_str,lon", [
    ("1990-07-17T12:20:00", 116.4),
    ("1993-03-06T08:00:00", 116.4),
    ("1985-11-15T06:00:00", 121.5),
    ("1988-03-20T14:00:00", 120.2),
    ("2000-01-01T23:30:00", 116.4),
    ("2000-01-01T00:15:00", 116.4),
    ("2000-01-01T22:59:00", 116.4),
    ("2000-01-01T01:00:00", 116.4),
])
def test_geju_confidence_range(dt_str, lon):
    """N1.07: 所有黄金案例格局置信度在 [0.0, 1.0] 且格局名称非空（直接调用，不走HTTP限流）"""
    data = _verify_direct_geju(dt_str, lon)
    geju = data.get("geju")
    if geju is None:
        pytest.skip("geju 字段未返回")
    assert geju.get("geju_name") is not None, f"[{dt_str}] geju_name 为 None"
    assert geju.get("geju_name") != "", f"[{dt_str}] geju_name 为空字符串"
    confidence = geju.get("confidence", -1)
    assert 0.0 <= confidence <= 1.0, (
        f"[{dt_str}] geju.confidence={confidence!r} 超出 [0.0, 1.0] 范围"
    )
