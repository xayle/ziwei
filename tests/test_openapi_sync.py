"""
D8: OpenAPI Schema 同步验证测试
验证运行时生成的 OpenAPI JSON 与关键路径/字段保持一致，防止无意破坏契约。
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# 导入 app（跳过弱密钥检查，因为测试可能不设置 SECRET_KEY）
import os
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-openapi-sync-d8")

from run import app  # noqa: E402

SNAPSHOT_PATH = Path(__file__).resolve().parent.parent / "docs" / "openapi.json"


@pytest.fixture(scope="module")
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(scope="module")
def live_schema(client: TestClient) -> dict:
    """获取运行时生成的 OpenAPI JSON"""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, f"openapi.json 返回 {resp.status_code}"
    return resp.json()


# ── 基本结构校验 ──────────────────────────────────────────────────────────────

def test_openapi_version(live_schema: dict):
    """OpenAPI 规范版本必须为 3.x.x"""
    version = live_schema.get("openapi", "")
    assert version.startswith("3."), f"expected openapi 3.x, got {version!r}"


def test_info_fields(live_schema: dict):
    """info 字段必须包含 title 和 version"""
    info = live_schema.get("info", {})
    assert "title" in info, "openapi.json 缺少 info.title"
    assert "version" in info, "openapi.json 缺少 info.version"


def test_paths_not_empty(live_schema: dict):
    """paths 不能为空"""
    paths = live_schema.get("paths", {})
    assert len(paths) > 0, "openapi.json paths 为空"


# ── 核心路径校验 ──────────────────────────────────────────────────────────────

REQUIRED_PATHS = [
    "/api/v1/verify",
    "/api/v1/bazi/full",
    "/api/v1/cases",
    "/api/v1/auth/login",
    "/api/v1/glossary",
    "/api/v1/cities",
    "/health",
]


@pytest.mark.parametrize("path", REQUIRED_PATHS)
def test_required_path_exists(live_schema: dict, path: str):
    """验证关键路由在 OpenAPI schema 中存在"""
    paths = live_schema.get("paths", {})
    assert path in paths, f"路径 {path!r} 在 openapi.json 中不存在"


# ── Sprint 5/6 新端点校验 ────────────────────────────────────────────────────

SPRINT56_PATHS = [
    "/api/v1/events/stats",
    "/api/v1/bazi/golden-cases",
    "/api/v1/classics",
    "/api/v1/bazi/liunian-report",
    "/api/v1/llm/interpret-module",
    "/api/v1/docs/concepts",
]


@pytest.mark.parametrize("path", SPRINT56_PATHS)
def test_sprint56_path_exists(live_schema: dict, path: str):
    """Sprint 5/6 新增端点必须出现在 OpenAPI schema 中"""
    paths = live_schema.get("paths", {})
    assert path in paths, f"Sprint 5/6 路径 {path!r} 未在 openapi.json 中注册"


# ── 快照对比（宽松模式） ──────────────────────────────────────────────────────

def test_snapshot_path_count(live_schema: dict):
    """路径总数必须 ≥ 快照（只增不减原则）"""
    if not SNAPSHOT_PATH.exists():
        pytest.skip("docs/openapi.json 快照不存在，跳过对比")
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    live_count = len(live_schema.get("paths", {}))
    snap_count = len(snapshot.get("paths", {}))
    assert live_count >= snap_count, (
        f"路径数量退化：live={live_count} < snapshot={snap_count}，"
        "可能意外删除了端点，请检查 run.py include_router 注册"
    )


def test_snapshot_no_missing_paths(live_schema: dict):
    """快照中出现的所有路径在当前 schema 中必须仍然存在"""
    if not SNAPSHOT_PATH.exists():
        pytest.skip("docs/openapi.json 快照不存在，跳过对比")
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    live_paths = set(live_schema.get("paths", {}).keys())
    snap_paths = set(snapshot.get("paths", {}).keys())
    missing = snap_paths - live_paths
    assert not missing, f"快照中存在但当前已消失的路径：{sorted(missing)}"
