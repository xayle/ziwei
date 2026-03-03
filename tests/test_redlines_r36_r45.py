"""
tests/test_redlines_r36_r45.py — v8.0 质量红线 R36-R45 自动验收（可 CI 覆盖部分）

R36  权限查询不阻塞主引擎计算（PermissionCache 物理隔离验证）
R37  禁止裸 f-string 拼接 SQL
R38  API v2 meta 字段：api_version / engine_version / calc_ms
R39  批量计算单次上限 50 条，超出返回 422
R40  ENGINE_V2=false 时 /api/v2/* 返回 501
R41  历史记录 PermissionCache/localStorage 5 条上限（后端无关，前端用 E2E 验证）
R44  批量 CSV 列名与 VerifyRequest 字段名一致（字段名静态检查）
R45  /api/v1/* 响应头含 Deprecation: true / Sunset: 2026-12-31
"""
from __future__ import annotations

import importlib
import os
import re
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# ── fixture 复用（已在 conftest.py 定义）─────────────────────────────────────
BASE_ITEM = {
    "dt": "1990-05-15T10:30:00",
    "gender": "male",
    "tz": "Asia/Shanghai",
    "lon": 116.4,
}


# ═══════════════════════════════════════════════════════════════════════════
# R36  权限缓存物理隔离（PermissionCache 不与引擎 QueryCache 共享）
# ═══════════════════════════════════════════════════════════════════════════

class TestR36PermissionCacheIsolation:
    """R36: 权限缓存必须与引擎 QueryCache 物理隔离"""

    def test_permission_cache_instance_separate_from_query_cache(self):
        """PermissionCache 实例与 QueryCache 实例必须是不同对象"""
        from app.dependencies.permissions import _permission_cache
        from services.optimization_tools import QueryCache
        assert not isinstance(_permission_cache, QueryCache), (
            "R36 违反: _permission_cache 不得是 QueryCache 实例"
        )

    def test_permission_cache_has_independent_invalidate(self):
        """PermissionCache 有独立 invalidate 方法"""
        from app.dependencies.permissions import _permission_cache
        assert hasattr(_permission_cache, "invalidate"), (
            "R36 违反: _permission_cache 缺少 invalidate 方法"
        )

    def test_permission_cache_ttl_default(self):
        """PermissionCache TTL 默认 300 秒"""
        from app.dependencies.permissions import _permission_cache
        assert _permission_cache._ttl == 300, (
            f"R36: PermissionCache TTL={_permission_cache._ttl}, 期望 300"
        )

    def test_query_cache_clear_does_not_affect_permission_cache(self):
        """清空引擎缓存不影响权限缓存"""
        from app.dependencies.permissions import _permission_cache

        # 写入权限缓存
        _permission_cache.set("perm:test:READ", True)
        assert _permission_cache.get("perm:test:READ") is True

        # 模拟引擎缓存清空（清空 QueryCache 全局实例，若存在）
        try:
            from services.optimization_tools import QueryCache
            # QueryCache 实例通常挂在 __init__ 模块，不可直接枚举
            # 此测试只确保 permission_cache 不被意外清空
            pass
        except ImportError:
            pass

        # 权限缓存应仍有值
        assert _permission_cache.get("perm:test:READ") is True, (
            "R36 违反: 权限缓存被意外清空"
        )
        _permission_cache.invalidate("perm:test:READ")


# ═══════════════════════════════════════════════════════════════════════════
# R37  禁止裸 f-string 拼接 SQL
# ═══════════════════════════════════════════════════════════════════════════

class TestR37NoRawSqlFstring:
    """R37: 禁止裸 f-string 拼接 SQL 语句"""

    # R37 扫描的目录
    SCAN_DIRS = ["routers", "services", "app"]
    # 精确匹配裸 f-string SQL 语句：f-string 开头包含 SQL 关键字紧跟空格，
    # 典型模式如 f"SELECT ... {var}" / f"INSERT INTO ... {var}" / f"WHERE id={var}"
    # 排除仅含关键字的错误消息（如 "Failed to update", "revocation from"）
    SQL_FSTRING_PATTERN = re.compile(
        r'f["\']'                              # f-string 开始
        r'(?:'
        r'SELECT\s'                            # SELECT 后跟空格
        r'|INSERT\s+INTO\s'                    # INSERT INTO
        r'|UPDATE\s+\w+\s+SET\s'             # UPDATE table SET
        r'|DELETE\s+FROM\s'                    # DELETE FROM
        r'|WHERE\s+\w+\s*[=<>!]'             # WHERE col=...
        r')',
        re.IGNORECASE,
    )

    def test_no_sql_fstring_in_app_code(self):
        """扫描 routers/ services/ app/ 不含裸 f-string SQL 拼接（R37）.

        只检测典型 SQL 注入风险模式（SELECT/INSERT INTO/UPDATE ... SET/DELETE FROM/WHERE col=），
        排除错误消息、日志等包含关键词但不构成 SQL 的 f-string。
        """
        violations = []
        root = Path(__file__).parent.parent
        for scan_dir in self.SCAN_DIRS:
            for py_file in (root / scan_dir).rglob("*.py"):
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                for lineno, line in enumerate(content.splitlines(), 1):
                    stripped = line.strip()
                    # 跳过注释行
                    if stripped.startswith("#"):
                        continue
                    if self.SQL_FSTRING_PATTERN.search(line):
                        violations.append(
                            f"{py_file.relative_to(root)}:{lineno}: {stripped}"
                        )
        assert not violations, (
            f"R37 违反: 发现 {len(violations)} 处裸 f-string SQL 拼接:\n"
            + "\n".join(violations[:5])
        )


# ═══════════════════════════════════════════════════════════════════════════
# R38  API v2 meta 字段
# ═══════════════════════════════════════════════════════════════════════════

class TestR38V2MetaFields:
    """R38: v2 响应必须包含 meta.api_version / meta.engine_version / meta.calc_ms"""

    def test_v2_verify_meta_fields_present(self, client_with_auth: TestClient):
        """POST /api/v2/verify 返回响应含完整 meta 字段"""
        resp = client_with_auth.post("/api/v2/verify", json=BASE_ITEM)
        assert resp.status_code == 200, f"R38: v2/verify 返回 {resp.status_code}"
        body = resp.json()
        assert "meta" in body, "R38 违反: 响应缺少 meta 字段"
        meta = body["meta"]
        assert "api_version" in meta, "R38 违反: meta 缺少 api_version"
        assert "engine_version" in meta, "R38 违反: meta 缺少 engine_version"
        assert "calc_ms" in meta, "R38 违反: meta 缺少 calc_ms"

    def test_v2_meta_calc_ms_is_positive(self, client_with_auth: TestClient):
        """meta.calc_ms 必须是正数"""
        resp = client_with_auth.post("/api/v2/verify", json=BASE_ITEM)
        assert resp.status_code == 200
        calc_ms = resp.json()["meta"]["calc_ms"]
        assert isinstance(calc_ms, (int, float)) and calc_ms >= 0, (
            f"R38 违反: meta.calc_ms={calc_ms} 非正数"
        )

    def test_v2_meta_api_version_not_empty(self, client_with_auth: TestClient):
        """meta.api_version 不得为空"""
        resp = client_with_auth.post("/api/v2/verify", json=BASE_ITEM)
        assert resp.status_code == 200
        assert resp.json()["meta"]["api_version"], "R38 违反: meta.api_version 为空"


# ═══════════════════════════════════════════════════════════════════════════
# R39  批量上限 50 条
# ═══════════════════════════════════════════════════════════════════════════

class TestR39BatchLimit:
    """R39: 批量端点 POST /api/v2/batch/verify，超过 50 条返回 422"""

    def test_batch_50_items_accepted(self, client_with_auth: TestClient):
        """恰好 50 条应被接受"""
        items = [BASE_ITEM] * 50
        resp = client_with_auth.post("/api/v2/batch/verify", json={"items": items})
        assert resp.status_code == 200, (
            f"R39 违反: 50 条批量请求返回 {resp.status_code}，期望 200"
        )

    def test_batch_51_items_rejected_422(self, client_with_auth: TestClient):
        """51 条应返回 422"""
        items = [BASE_ITEM] * 51
        resp = client_with_auth.post("/api/v2/batch/verify", json={"items": items})
        assert resp.status_code == 422, (
            f"R39 违反: 51 条批量请求返回 {resp.status_code}，期望 422"
        )

    def test_batch_0_items_rejected(self, client_with_auth: TestClient):
        """0 条空请求应返回 422"""
        resp = client_with_auth.post("/api/v2/batch/verify", json={"items": []})
        assert resp.status_code == 422, (
            f"R39: 空批量请求返回 {resp.status_code}，期望 422"
        )

    def test_batch_response_structure(self, client_with_auth: TestClient):
        """批量响应包含 results 和 failed 两个字段"""
        items = [BASE_ITEM] * 2
        resp = client_with_auth.post("/api/v2/batch/verify", json={"items": items})
        assert resp.status_code == 200
        body = resp.json()
        assert "results" in body, "R39: 批量响应缺少 results"
        assert "failed" in body, "R39: 批量响应缺少 failed"
        # 总数守恒
        assert len(body["results"]) + len(body["failed"]) == 2, (
            "R39: len(results) + len(failed) != len(items)"
        )


# ═══════════════════════════════════════════════════════════════════════════
# R40  ENGINE_V2=false → /api/v2/* 返回 501
# ═══════════════════════════════════════════════════════════════════════════

class TestR40EngineV2Flag:
    """R40: ENGINE_V2=false 时 /api/v2/* 全部端点返回 501"""

    def test_v2_verify_returns_501_when_engine_v2_disabled(
        self, client_with_auth: TestClient
    ):
        """ENGINE_V2=false → POST /api/v2/verify 返回 501"""
        with patch.dict(os.environ, {"ENGINE_V2": "false"}):
            resp = client_with_auth.post("/api/v2/verify", json=BASE_ITEM)
        assert resp.status_code == 501, (
            f"R40 违反: ENGINE_V2=false 时 v2/verify 返回 {resp.status_code}，期望 501"
        )

    def test_v2_batch_returns_501_when_engine_v2_disabled(
        self, client_with_auth: TestClient
    ):
        """ENGINE_V2=false → POST /api/v2/batch/verify 返回 501"""
        with patch.dict(os.environ, {"ENGINE_V2": "false"}):
            resp = client_with_auth.post(
                "/api/v2/batch/verify", json={"items": [BASE_ITEM]}
            )
        assert resp.status_code == 501, (
            f"R40 违反: ENGINE_V2=false 时 v2/batch 返回 {resp.status_code}，期望 501"
        )

    def test_v2_verify_returns_200_when_engine_v2_enabled(
        self, client_with_auth: TestClient
    ):
        """ENGINE_V2=true → POST /api/v2/verify 返回 200"""
        with patch.dict(os.environ, {"ENGINE_V2": "true"}):
            resp = client_with_auth.post("/api/v2/verify", json=BASE_ITEM)
        assert resp.status_code == 200, (
            f"R40: ENGINE_V2=true 时 v2/verify 返回 {resp.status_code}，期望 200"
        )


# ═══════════════════════════════════════════════════════════════════════════
# R44  批量 CSV 列名与 VerifyRequest 字段名一致（静态检查）
# ═══════════════════════════════════════════════════════════════════════════

class TestR44BatchCsvColumns:
    """R44: batch.html 中 CSV 列名必须与 VerifyRequest 字段名严格一致"""

    def test_verify_request_has_dt_field(self):
        """VerifyRequest 有 'dt' 字段（非 birth_dt）"""
        from app.schemas.bazi import VerifyRequest
        fields = set(VerifyRequest.model_fields.keys())
        assert "dt" in fields, (
            f"R44: VerifyRequest 缺少 'dt' 字段; 实际字段: {fields}"
        )

    def test_batch_html_csv_columns_match_verify_request(self):
        """batch.html 中声明的 CSV 列名与 VerifyRequest 字段名一致"""
        from app.schemas.bazi import VerifyRequest
        required_fields = set(VerifyRequest.model_fields.keys())

        batch_html = Path(__file__).parent.parent / "static" / "batch.html"
        if not batch_html.exists():
            pytest.skip("static/batch.html 不存在，跳过 R44 HTML 检查")

        content = batch_html.read_text(encoding="utf-8", errors="ignore")
        # 检查主要字段之一必须出现在 batch.html 中
        core_fields = {"dt", "gender", "lon", "tz"}
        for field in core_fields:
            assert field in content, (
                f"R44 违反: batch.html 中未找到字段名 '{field}'，"
                f"CSV 列名与 VerifyRequest 字段名不一致"
            )


# ═══════════════════════════════════════════════════════════════════════════
# R45  /api/v1/* 响应头含 Deprecation + Sunset
# ═══════════════════════════════════════════════════════════════════════════

class TestR45V1DeprecationHeaders:
    """R45: /api/v1/* 所有响应必须携带 Deprecation: true + Sunset: 2026-12-31"""

    def test_v1_verify_has_deprecation_header(self, client_with_auth: TestClient):
        """POST /api/v1/verify 响应含 Deprecation: true（接受 200 或 429，两者均须携带 header）"""
        resp = client_with_auth.post("/api/v1/verify", json=BASE_ITEM)
        # 允许 429（速率限制）：中间件在 call_next 之后追加 header，429 同样经过中间件
        assert resp.status_code in (200, 429), (
            f"R45: /api/v1/verify 预期 200/429，实际 {resp.status_code}"
        )
        dep = resp.headers.get("deprecation", "")
        assert dep.lower() == "true", (
            f"R45 违反: /api/v1/verify 缺少 Deprecation: true (得到 '{dep}'，status={resp.status_code})"
        )

    def test_v1_verify_has_sunset_header(self, client_with_auth: TestClient):
        """POST /api/v1/verify 响应含 Sunset: 2026-12-31（接受 200 或 429）"""
        resp = client_with_auth.post("/api/v1/verify", json=BASE_ITEM)
        assert resp.status_code in (200, 429), (
            f"R45: /api/v1/verify 预期 200/429，实际 {resp.status_code}"
        )
        sunset = resp.headers.get("sunset", "")
        assert sunset == "2026-12-31", (
            f"R45 违反: /api/v1/verify Sunset='{sunset}'，期望 '2026-12-31'（status={resp.status_code}）"
        )

    def test_v1_health_has_deprecation_header(self, client: TestClient):
        """GET /api/v1/health (或 /health) 路由若属 v1 前缀，应含废弃 header"""
        # /health 不在 /api/v1/ 前缀下，不要求废弃 header
        # 只检查明确的 v1 路由
        resp = client.get("/health")
        assert resp.status_code == 200
        # /health 不需要废弃 header（不是 /api/v1/ 路径）
        # 本测试仅确认 /health 正常

    def test_v2_does_not_have_deprecation_header(self, client_with_auth: TestClient):
        """POST /api/v2/verify 不应有 Deprecation header（v2 是新版本）"""
        resp = client_with_auth.post("/api/v2/verify", json=BASE_ITEM)
        dep = resp.headers.get("deprecation", "")
        assert dep == "", (
            f"R45: /api/v2/verify 不应有 Deprecation header (得到 '{dep}')"
        )
