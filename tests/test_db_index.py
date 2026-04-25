"""
O5: 数据库查询索引测试 — EXPLAIN QUERY PLAN 断言索引确实被使用

场景：
  AuditLog 积累 10 万条后，如果无索引，WHERE user_id=42 会全表扫描（8 秒→0.01 秒）。
  本测试在内存 SQLite 中重建目标表+索引，通过 EXPLAIN QUERY PLAN 验证
  optimizer 确实选择了 INDEX SCAN 路径。

验证命令：pytest tests/test_db_index.py -v
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# 1. 辅助：建立内存测试库（仅含测试 SQL，独立于 app 状态）
# ─────────────────────────────────────────────────────────────────────────────

_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS cases (
    id         TEXT PRIMARY KEY,
    owner_id   INTEGER,
    share_token TEXT,
    share_expires_at DATETIME
);

CREATE TABLE IF NOT EXISTS snapshots (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id  TEXT,
    version  TEXT,
    data     TEXT
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER,
    action     TEXT,
    created_at DATETIME
);
"""

_CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_cases_share_token    ON cases(share_token);
CREATE INDEX IF NOT EXISTS idx_snapshots_case_id    ON snapshots(case_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id   ON audit_logs(user_id);
"""


def _make_mem_db() -> sqlite3.Connection:
    """返回已建表+索引的内存 SQLite 连接。"""
    conn = sqlite3.connect(":memory:")
    conn.executescript(_CREATE_TABLES)
    conn.executescript(_CREATE_INDEXES)
    return conn


def _explain(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[Any]:
    """返回 EXPLAIN QUERY PLAN 的所有行。"""
    rows = conn.execute(f"EXPLAIN QUERY PLAN {sql}", params).fetchall()
    return rows


def _uses_index(rows: list[Any]) -> bool:
    """判断 EXPLAIN QUERY PLAN 结果中是否含 'INDEX' 关键字。"""
    return any("INDEX" in str(row).upper() for row in rows)


# ─────────────────────────────────────────────────────────────────────────────
# 2. 索引存在性断言（PRAGMA）
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def mem_db():
    conn = _make_mem_db()
    yield conn
    conn.close()


def test_index_cases_share_token_exists(mem_db):
    """idx_cases_share_token 应存在于 cases 表"""
    rows = mem_db.execute("PRAGMA index_list(cases)").fetchall()
    names = [r[1] for r in rows]
    assert "idx_cases_share_token" in names, (
        f"cases 表索引列表 {names!r} 缺少 idx_cases_share_token"
    )


def test_index_snapshots_case_id_exists(mem_db):
    """idx_snapshots_case_id 应存在于 snapshots 表"""
    rows = mem_db.execute("PRAGMA index_list(snapshots)").fetchall()
    names = [r[1] for r in rows]
    assert "idx_snapshots_case_id" in names, (
        f"snapshots 表索引列表 {names!r} 缺少 idx_snapshots_case_id"
    )


def test_index_audit_logs_created_at_exists(mem_db):
    """idx_audit_logs_created_at 应存在于 audit_logs 表"""
    rows = mem_db.execute("PRAGMA index_list(audit_logs)").fetchall()
    names = [r[1] for r in rows]
    assert "idx_audit_logs_created_at" in names, (
        f"audit_logs 表索引列表 {names!r} 缺少 idx_audit_logs_created_at"
    )


def test_index_audit_logs_user_id_exists(mem_db):
    """idx_audit_logs_user_id 应存在于 audit_logs 表"""
    rows = mem_db.execute("PRAGMA index_list(audit_logs)").fetchall()
    names = [r[1] for r in rows]
    assert "idx_audit_logs_user_id" in names, (
        f"audit_logs 表索引列表 {names!r} 缺少 idx_audit_logs_user_id"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3. EXPLAIN QUERY PLAN 断言（有数据时 optimizer 才会走索引）
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def mem_db_with_data():
    """在内存库中插入足量数据，使 optimizer 倾向于走索引扫描。"""
    conn = _make_mem_db()

    # 插入 1000 行 audit_logs，user_id 分布稀疏（1-100）
    conn.executemany(
        "INSERT INTO audit_logs(user_id, action, created_at) VALUES(?,?,datetime('now',?))",
        [(i % 100 + 1, "verify", f"-{i} seconds") for i in range(1000)],
    )
    # 插入 500 行 snapshots
    conn.executemany(
        "INSERT INTO snapshots(case_id, version, data) VALUES(?,?,?)",
        [(f"case_{i // 5}", f"v{i}", "{}") for i in range(500)],
    )
    # 插入 200 行 cases（share_token 只有少数有值）
    conn.executemany(
        "INSERT INTO cases(id, owner_id, share_token) VALUES(?,?,?)",
        [(f"C{i:04d}", i % 20 + 1, f"tok_{i}" if i % 10 == 0 else None)
         for i in range(200)],
    )
    conn.execute("ANALYZE")   # 让统计信息更新，帮助 optimizer
    yield conn
    conn.close()


def test_explain_audit_logs_user_id_uses_index(mem_db_with_data):
    """SELECT … WHERE user_id=1 应走 idx_audit_logs_user_id"""
    rows = _explain(mem_db_with_data, "SELECT * FROM audit_logs WHERE user_id = ?", (1,))
    assert _uses_index(rows), (
        f"EXPLAIN QUERY PLAN 未使用索引，结果：{rows}"
    )


def test_explain_audit_logs_created_at_uses_index(mem_db_with_data):
    """SELECT … WHERE created_at > '…' 应走 idx_audit_logs_created_at"""
    rows = _explain(
        mem_db_with_data,
        "SELECT * FROM audit_logs WHERE created_at > datetime('now','-1 hour')",
    )
    assert _uses_index(rows), (
        f"EXPLAIN QUERY PLAN 未使用索引，结果：{rows}"
    )


def test_explain_snapshots_case_id_uses_index(mem_db_with_data):
    """SELECT … WHERE case_id='…' 应走 idx_snapshots_case_id"""
    rows = _explain(mem_db_with_data, "SELECT * FROM snapshots WHERE case_id = ?", ("case_1",))
    assert _uses_index(rows), (
        f"EXPLAIN QUERY PLAN 未使用索引，结果：{rows}"
    )


def test_explain_cases_share_token_uses_index(mem_db_with_data):
    """SELECT … WHERE share_token='…' 应走 idx_cases_share_token"""
    rows = _explain(mem_db_with_data, "SELECT * FROM cases WHERE share_token = ?", ("tok_10",))
    assert _uses_index(rows), (
        f"EXPLAIN QUERY PLAN 未使用索引，结果：{rows}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 4. 迁移文件存在性断言（确认 Alembic 版本文件已落地）
# ─────────────────────────────────────────────────────────────────────────────

def test_migration_file_exists():
    """Alembic 迁移文件 a2b3c4d5e6f7_add_indexes_and_share_token.py 应存在"""
    migration_dir = Path(__file__).resolve().parent.parent / "migrations" / "versions"
    matches = list(migration_dir.glob("a2b3c4d5e6f7_*.py"))
    assert matches, (
        f"未找到 a2b3c4d5e6f7 迁移文件，目录 {migration_dir} 中的文件：{list(migration_dir.iterdir())}"
    )


def test_migration_contains_index_creation():
    """Alembic 迁移文件应包含 create_index 调用"""
    migration_dir = Path(__file__).resolve().parent.parent / "migrations" / "versions"
    matches = list(migration_dir.glob("a2b3c4d5e6f7_*.py"))
    assert matches, "迁移文件不存在，已在上一个测试失败"
    content = matches[0].read_text(encoding="utf-8")
    assert "create_index" in content, "迁移文件中未找到 create_index 调用"
    assert "audit_logs" in content, "迁移文件中未找到 audit_logs 表索引"
