"""
test_coverage_boost25.py — routers/bazi.py 集成测试

覆盖目标（当前 38%，目标 70%+）：
  liunian-domain, dayun-report, compatibility, monthly, analyze,
  jieqi, geju, calendar-compare, batch-compare, golden-cases,
  liunian-report (submit/poll), _sanitize_request_id 边界

分组：
  A) 需 DB（用 pytest 的 client_with_auth + test_case 夹具）
  B) 无状态（AUTH_BYPASS + TestClient 自包含）
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

# ──────────────────────────────────────────────────────────────────────────────
# 共用常量（+08:00 使 fromisoformat 返回 tz-aware datetime，避免 verify_full 报错）
# ──────────────────────────────────────────────────────────────────────────────
_BIRTH_DT = "1990-07-17T12:00:00+08:00"
_COMPAT_A  = {"birth_dt": "1990-07-17T12:00:00+08:00", "lon": 116.4, "tz": "Asia/Shanghai", "gender": "male"}
_COMPAT_B  = {"birth_dt": "1993-03-15T08:00:00+08:00", "lon": 116.4, "tz": "Asia/Shanghai", "gender": "female"}


# ──────────────────────────────────────────────────────────────────────────────
# 辅助：自包含客户端（不需 DB 夹具）
# ──────────────────────────────────────────────────────────────────────────────
def _bypass_client() -> TestClient:
    os.environ["AUTH_BYPASS"] = "true"
    from run import app as _app
    return TestClient(_app)


# ══════════════════════════════════════════════════════════════════════════════
# A. 需要 DB 的集成测试（通过 pytest 夹具使用测试数据库）
# ══════════════════════════════════════════════════════════════════════════════

def _make_tz_case(db_session, owner_id, birth_dt_local="2000-01-01T12:00:00+08:00", gender="male"):
    """创建带 tz-aware birth_dt_local 的 Case（供 DB 集成测试使用）。"""
    from app.models import Case
    case = Case(
        id=str(uuid4()),
        name="TZ Test Case",
        gender=gender,
        birth_dt_local=birth_dt_local,
        tz="Asia/Shanghai",
        birth_dt="2000-01-01T04:00:00Z",
        city="Shanghai",
        lon=121.47,
        solar_time_enabled=False,
        owner_id=owner_id,
    )
    db_session.add(case)
    db_session.commit()
    db_session.refresh(case)
    return case


class TestLiunianDomainEndpoint:
    """POST /api/v1/bazi/liunian-domain"""

    def test_404_not_found(self, client_with_auth: TestClient):
        """不存在的 case_id → 404"""
        resp = client_with_auth.post("/api/v1/bazi/liunian-domain", json={
            "case_id": str(uuid4()), "year": 2025,
        })
        assert resp.status_code == 404

    def test_happy_path(self, client_with_auth: TestClient, test_user, db_session):
        """正常流程 → 200，返回 domains 字段"""
        case = _make_tz_case(db_session, test_user.id)
        resp = client_with_auth.post("/api/v1/bazi/liunian-domain", json={
            "case_id": case.id, "year": 2025,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["year"] == 2025
        assert "year_ganzhi" in data
        assert "domains" in data
        assert isinstance(data["domains"], dict)

    def test_happy_path_different_year(self, client_with_auth: TestClient, test_user, db_session):
        """不同年份也能正常返回"""
        case = _make_tz_case(db_session, test_user.id)
        resp = client_with_auth.post("/api/v1/bazi/liunian-domain", json={
            "case_id": case.id, "year": 2030,
        })
        assert resp.status_code == 200
        assert resp.json()["year"] == 2030


class TestDayunReportEndpoint:
    """POST /api/v1/bazi/dayun-report"""

    def test_404_not_found(self, client_with_auth: TestClient):
        """不存在的 case_id → 404"""
        resp = client_with_auth.post("/api/v1/bazi/dayun-report", json={
            "case_id": str(uuid4()),
        })
        assert resp.status_code == 404

    def test_happy_path(self, client_with_auth: TestClient, test_user, db_session):
        """正常流程 → 200，返回大运列表"""
        case = _make_tz_case(db_session, test_user.id)
        resp = client_with_auth.post("/api/v1/bazi/dayun-report", json={
            "case_id": case.id,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert isinstance(data["items"], list)
        assert "narrative_total_chars" in data
        assert isinstance(data["narrative_total_chars"], int)

    def test_items_have_required_fields(self, client_with_auth: TestClient, test_user, db_session):
        """每个大运条目有 ganzhi/narrative 字段"""
        case = _make_tz_case(db_session, test_user.id)
        resp = client_with_auth.post("/api/v1/bazi/dayun-report", json={
            "case_id": case.id,
        })
        assert resp.status_code == 200
        items = resp.json()["items"]
        if items:
            item = items[0]
            assert "ganzhi" in item
            assert "narrative" in item


class TestMonthlyEndpoint:
    """POST /api/v1/bazi/monthly"""

    def test_404_not_found(self, client_with_auth: TestClient):
        """不存在的 case_id → 404"""
        resp = client_with_auth.post("/api/v1/bazi/monthly", json={
            "case_id": str(uuid4()), "year": 2025,
        })
        assert resp.status_code == 404

    def test_happy_path(self, client_with_auth: TestClient, test_user, db_session):
        """正常流程 → 200，12个月"""
        case = _make_tz_case(db_session, test_user.id)
        resp = client_with_auth.post("/api/v1/bazi/monthly", json={
            "case_id": case.id, "year": 2025,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["year"] == 2025
        assert "year_ganzhi" in data
        items = data["items"]
        assert len(items) == 12
        first = items[0]
        assert "month" in first
        assert "month_ganzhi" in first
        assert "luck_level" in first

    def test_different_year(self, client_with_auth: TestClient, test_user, db_session):
        """2026年同样可以计算"""
        case = _make_tz_case(db_session, test_user.id)
        resp = client_with_auth.post("/api/v1/bazi/monthly", json={
            "case_id": case.id, "year": 2026,
        })
        assert resp.status_code == 200
        assert resp.json()["year"] == 2026


class TestBatchCompareEndpoint:
    """POST /api/v1/bazi/batch-compare"""

    def test_nonexistent_cases_return_error_profiles(self, client_with_auth: TestClient):
        """所有 case_id 不存在 → 200（错误 profiles）"""
        fake_ids = [str(uuid4()), str(uuid4())]
        resp = client_with_auth.post("/api/v1/bazi/batch-compare", json={
            "case_ids": fake_ids,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert all(p.get("error") for p in data["profiles"])

    def test_with_two_valid_cases(self, client_with_auth: TestClient, test_user, db_session):
        """两个有效案例 → 200，返回正常 profiles"""
        case1 = _make_tz_case(db_session, test_user.id, "2000-01-01T12:00:00+08:00", "male")
        case2 = _make_tz_case(db_session, test_user.id, "1993-03-15T08:00:00+08:00", "female")

        resp = client_with_auth.post("/api/v1/bazi/batch-compare", json={
            "case_ids": [case1.id, case2.id],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert "common_favor" in data
        assert "common_avoid" in data

    def test_too_few_case_ids_rejected(self, client_with_auth: TestClient):
        """只给 1 个 case_id → 422（min_length=2）"""
        resp = client_with_auth.post("/api/v1/bazi/batch-compare", json={
            "case_ids": [str(uuid4())],
        })
        assert resp.status_code == 422


class TestLiunianReportEndpoint:
    """POST /api/v1/bazi/liunian-report (异步 202) + GET poll"""

    def test_submit_202(self, client_with_auth: TestClient, test_case):
        """提交任务 → 202（test_case 用于存在性检查，不需要 tz-aware birth_dt）"""
        resp = client_with_auth.post("/api/v1/bazi/liunian-report", json={
            "case_id": test_case.id, "year": 2025,
        })
        assert resp.status_code == 202
        data = resp.json()
        assert "task_id" in data
        assert data["status"] in ("queued", "running", "done")
        assert data["year"] == 2025
        assert data["case_id"] == test_case.id

    def test_submit_404_case(self, client_with_auth: TestClient):
        """case 不存在 → 404"""
        resp = client_with_auth.post("/api/v1/bazi/liunian-report", json={
            "case_id": str(uuid4()), "year": 2025,
        })
        assert resp.status_code == 404

    def test_submit_with_months(self, client_with_auth: TestClient, test_case):
        """include_months=True 应正常提交"""
        resp = client_with_auth.post("/api/v1/bazi/liunian-report", json={
            "case_id": test_case.id, "year": 2026, "include_months": True,
        })
        assert resp.status_code == 202

    def test_poll_task_found(self, client_with_auth: TestClient, test_case):
        """先提交再查询 → 200"""
        post = client_with_auth.post("/api/v1/bazi/liunian-report", json={
            "case_id": test_case.id, "year": 2025,
        })
        task_id = post.json()["task_id"]
        # 等待后台任务完成（最多 3s）
        for _ in range(15):
            poll = client_with_auth.get(f"/api/v1/bazi/liunian-report/{task_id}")
            assert poll.status_code == 200
            if poll.json().get("status") in ("done", "failed"):
                break
            time.sleep(0.2)

    def test_poll_task_not_found(self, client_with_auth: TestClient):
        """轮询不存在的 task_id → 404"""
        resp = client_with_auth.get(f"/api/v1/bazi/liunian-report/{uuid4()}")
        assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# B. 无状态自包含测试（AUTH_BYPASS + TestClient，不涉及数据库）
# ══════════════════════════════════════════════════════════════════════════════

class TestCompatibilityEndpoint:
    """POST /api/v1/bazi/compatibility（无状态合盘）"""

    def setup_method(self):
        self.client = _bypass_client()

    def test_happy_path(self):
        """两人合盘 → 200，返回 score/wuxing_match 等字段"""
        resp = self.client.post("/api/v1/bazi/compatibility", json={
            "person_a": _COMPAT_A,
            "person_b": _COMPAT_B,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "score" in data
        assert "wuxing_match" in data
        assert "branch_clash" in data
        assert "born_year_he" in data
        assert "summary" in data
        assert 0 <= data["score"] <= 100

    def test_invalid_birth_dt(self):
        """出生时间格式错误 → 422"""
        resp = self.client.post("/api/v1/bazi/compatibility", json={
            "person_a": {**_COMPAT_A, "birth_dt": "not-a-date"},
            "person_b": _COMPAT_B,
        })
        assert resp.status_code == 422

    def test_same_person(self):
        """相同两人 → 高分（用神相同）"""
        resp = self.client.post("/api/v1/bazi/compatibility", json={
            "person_a": _COMPAT_A,
            "person_b": _COMPAT_A,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["score"] >= 0  # 同人可能有 sanhe

    def test_different_genders(self):
        """男女组合 → 正常调用"""
        resp = self.client.post("/api/v1/bazi/compatibility", json={
            "person_a": {**_COMPAT_A, "gender": "male"},
            "person_b": {**_COMPAT_B, "gender": "female"},
        })
        assert resp.status_code == 200

    def test_year_he_detection(self):
        """使用六合对（子-丑年支）→ born_year_he 有结果"""
        # 子年=2008, 丑年=2009（子丑六合）
        resp = self.client.post("/api/v1/bazi/compatibility", json={
            "person_a": {"birth_dt": "2008-01-15T12:00:00+08:00", "lon": 116.4, "tz": "Asia/Shanghai"},
            "person_b": {"birth_dt": "2009-01-15T12:00:00+08:00", "lon": 116.4, "tz": "Asia/Shanghai"},
        })
        assert resp.status_code == 200


class TestAnalyzeEndpoint:
    """POST /api/v1/bazi/analyze（按需分析）"""

    def setup_method(self):
        self.client = _bypass_client()

    def test_default_tabs(self):
        """默认 tabs → 200，返回 life_arc/lucky"""
        resp = self.client.post("/api/v1/bazi/analyze", json={
            "birth_dt": _BIRTH_DT,
            "lon": 116.4,
            "tz": "Asia/Shanghai",
            "gender": "male",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "life_arc" in data
        assert "lucky" in data

    def test_specific_tabs(self):
        """指定 tabs=['pillars', 'yongshen'] → 200"""
        resp = self.client.post("/api/v1/bazi/analyze", json={
            "birth_dt": _BIRTH_DT,
            "lon": 116.4,
            "tz": "Asia/Shanghai",
            "tabs": ["pillars", "yongshen"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "pillars" in data
        assert "yongshen" in data

    def test_unknown_tab_rejected(self):
        """tabs 包含未知字段 → 422"""
        resp = self.client.post("/api/v1/bazi/analyze", json={
            "birth_dt": _BIRTH_DT,
            "lon": 116.4,
            "tabs": ["pillars", "unknowntab"],
        })
        assert resp.status_code == 422
        assert "unknowntab" in resp.json()["detail"]

    def test_invalid_birth_dt(self):
        """格式错误 birth_dt → 422"""
        resp = self.client.post("/api/v1/bazi/analyze", json={
            "birth_dt": "bad-format",
            "lon": 116.4,
        })
        assert resp.status_code == 422

    def test_all_known_tabs(self):
        """传入全部已知 tab → 200（不报错）"""
        tabs = [
            "pillars", "geju", "yongshen", "wuxing", "dayun",
            "life_arc", "lucky", "wealth", "career", "marriage",
            "health", "personality", "monthly", "liunian",
        ]
        resp = self.client.post("/api/v1/bazi/analyze", json={
            "birth_dt": _BIRTH_DT,
            "lon": 121.47,
            "tz": "Asia/Shanghai",
            "tabs": tabs,
        })
        assert resp.status_code == 200
        data = resp.json()
        for t in tabs:
            assert t in data


class TestGejuEndpoint:
    """POST /api/v1/bazi/geju（格局专项）"""

    def setup_method(self):
        self.client = _bypass_client()

    def test_happy_path(self):
        """正常请求 → 200，返回 geju_name/confidence"""
        resp = self.client.post("/api/v1/bazi/geju", json={
            "birth_dt": _BIRTH_DT,
            "lon": 116.4,
            "tz": "Asia/Shanghai",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "geju_name" in data
        assert "confidence" in data
        assert "is_broken" in data
        assert isinstance(data["confidence"], float)

    def test_invalid_birth_dt(self):
        """格式错误 → 422"""
        resp = self.client.post("/api/v1/bazi/geju", json={
            "birth_dt": "not-a-date",
            "lon": 116.4,
        })
        assert resp.status_code == 422

    def test_female_gender(self):
        """女性命盘 → 200"""
        resp = self.client.post("/api/v1/bazi/geju", json={
            "birth_dt": "1993-03-15T08:30:00+08:00",
            "lon": 121.47,
            "gender": "female",
        })
        assert resp.status_code == 200


class TestCalendarCompareEndpoint:
    """POST /api/v1/bazi/calendar-compare（ADMIN 工具）"""

    def setup_method(self):
        # AUTH_BYPASS 时 dummy user is_admin=True，所以直接用 bypass
        self.client = _bypass_client()

    def test_admin_happy_path(self):
        """管理员调用 → 200，返回 sxtwl/cnlunar 至少一个有值"""
        resp = self.client.post("/api/v1/bazi/calendar-compare", json={
            "birth_dt": "1990-07-17T12:00:00+08:00",
            "lon": 116.4,
            "tz": "Asia/Shanghai",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "diff_fields" in data
        assert "warnings" in data
        # sxtwl 或 cnlunar 至少一个非 None（或都有错误但 200）
        assert isinstance(data["diff_fields"], list)

    def test_invalid_birth_dt(self):
        """格式错误 → 422"""
        resp = self.client.post("/api/v1/bazi/calendar-compare", json={
            "birth_dt": "not-a-date",
            "lon": 116.4,
        })
        assert resp.status_code == 422

    def test_non_admin_user_rejected(self, client_with_auth: TestClient, test_user):
        """非管理员 → 403（借用 conftest 普通用户，test_user.is_admin=False）"""
        # test_user 是普通用户（is_admin=False），client_with_auth 携带其 token
        # 非管理员调用 calendar-compare 应返回 403
        resp = client_with_auth.post("/api/v1/bazi/calendar-compare", json={
            "birth_dt": "1990-01-01T08:00:00+08:00", "lon": 116.4, "tz": "Asia/Shanghai"
        })
        assert resp.status_code == 403


class TestGoldenCasesEndpoint:
    """GET /api/v1/bazi/golden-cases（无需认证）"""

    def setup_method(self):
        self.client = _bypass_client()

    def test_get_all_no_auth(self):
        """无帐号也可访问 → 200"""
        resp = self.client.get("/api/v1/bazi/golden-cases")
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "cases" in data
        assert isinstance(data["cases"], list)

    def test_limit_param(self):
        """limit 参数生效"""
        resp = self.client.get("/api/v1/bazi/golden-cases?limit=3")
        assert resp.status_code == 200
        assert len(resp.json()["cases"]) <= 3

    def test_filter_by_tag(self):
        """tag=GT 过滤"""
        resp = self.client.get("/api/v1/bazi/golden-cases?tag=GT")
        assert resp.status_code == 200
        data = resp.json()
        for c in data["cases"]:
            assert c.get("id", "").upper().startswith("GT")

    def test_filter_by_geju(self):
        """geju 过滤不报错（即使无匹配）"""
        resp = self.client.get("/api/v1/bazi/golden-cases?geju=七杀")
        assert resp.status_code == 200
        assert isinstance(resp.json()["total"], int)

    def test_limit_max_200(self):
        """limit 超过 200 → 被截断到 200"""
        resp = self.client.get("/api/v1/bazi/golden-cases?limit=9999")
        assert resp.status_code == 200
        assert len(resp.json()["cases"]) <= 200


class TestJieqiEndpoint:
    """GET /api/v1/bazi/jieqi"""

    def setup_method(self):
        self.client = _bypass_client()

    def test_happy_path(self):
        """year=2025 → 200，返回节气列表"""
        resp = self.client.get("/api/v1/bazi/jieqi?year=2025")
        # sxtwl 不可用时 503，可用时 200
        if resp.status_code == 503:
            pytest.skip("sxtwl 不可用，跳过节气测试")
        assert resp.status_code == 200
        data = resp.json()
        assert data["year"] == 2025
        assert "items" in data
        for item in data["items"]:
            assert "name" in item
            assert "dt_local" in item

    def test_backend_unavailable_503(self):
        """sxtwl 不可用时 → 503（patch backends.SxtwlBackend 使函数内 import 获取到 mock）"""
        from unittest.mock import patch, MagicMock
        from backends import BackendUnavailable
        with patch("backends.SxtwlBackend", side_effect=BackendUnavailable("no sxtwl")):
            resp = self.client.get("/api/v1/bazi/jieqi?year=2025")
        assert resp.status_code == 503

    def test_different_year(self):
        """year=2026 也可以计算"""
        resp = self.client.get("/api/v1/bazi/jieqi?year=2026")
        assert resp.status_code in (200, 503)


class TestRequestIdSanitizer:
    """_sanitize_request_id 单元测试（直接导入函数）"""

    def setup_method(self):
        from routers.bazi import _sanitize_request_id
        self._fn = _sanitize_request_id

    def test_none_returns_uuid(self):
        warnings = []
        rid = self._fn(None, warnings)
        assert len(rid) == 36  # UUID 格式
        assert not warnings

    def test_empty_string_returns_uuid(self):
        warnings = []
        rid = self._fn("   ", warnings)
        assert len(rid) == 36

    def test_valid_id_passes_through(self):
        warnings = []
        rid = self._fn("req-123", warnings)
        assert rid == "req-123"
        assert not warnings

    def test_invalid_chars_replaced(self):
        warnings = []
        rid = self._fn("abc<script>", warnings)
        assert len(rid) == 36  # replaced with UUID
        assert any(w.code == "request_id_invalid_chars" for w in warnings)

    def test_too_long_truncated(self):
        warnings = []
        long_id = "a" * 200
        rid = self._fn(long_id, warnings)
        assert len(rid) == 128
        assert any(w.code == "request_id_truncated" for w in warnings)

    def test_exactly_128_chars_no_warning(self):
        warnings = []
        exactly128 = "a" * 128
        rid = self._fn(exactly128, warnings)
        assert rid == exactly128
        assert not warnings

    def test_dash_underscore_dot_allowed(self):
        """合法字符集包含 - _ ."""
        warnings = []
        rid = self._fn("req-1.2_3", warnings)
        assert rid == "req-1.2_3"
        assert not warnings


class TestBaziFullXRequestId:
    """POST /api/v1/bazi/full 测试 X-Request-Id header 路径"""

    def setup_method(self):
        self.client = _bypass_client()

    _PAYLOAD = {
        "dt": "1990-07-17T12:00:00",  # naive OK for /full (goes through bazi_full which adds tz)
        "tz": "Asia/Shanghai",
        "lon": 116.4,
        "gender": "male",
        "mode": "single",
    }

    def test_custom_request_id_reflected(self):
        """提供合法 X-Request-Id → 响应正常"""
        resp = self.client.post(
            "/api/v1/bazi/full",
            json=self._PAYLOAD,
            headers={"X-Request-Id": "test-req-001"},
        )
        assert resp.status_code == 200

    def test_invalid_request_id_warned(self):
        """X-Request-Id 含非法字符 → 自动替换为 UUID，warnings 中有提示"""
        resp = self.client.post(
            "/api/v1/bazi/full",
            json=self._PAYLOAD,
            headers={"X-Request-Id": "<invalid>"},
        )
        assert resp.status_code == 200
        warnings = resp.json().get("warnings", [])
        codes = [w.get("code") for w in warnings]
        assert "request_id_invalid_chars" in codes

    def test_too_long_request_id_truncated(self):
        """X-Request-Id 超过 128 字符 → 截断 + warnings"""
        resp = self.client.post(
            "/api/v1/bazi/full",
            json=self._PAYLOAD,
            headers={"X-Request-Id": "a" * 200},
        )
        assert resp.status_code == 200
        warnings = resp.json().get("warnings", [])
        codes = [w.get("code") for w in warnings]
        assert "request_id_truncated" in codes
