"""
optimization_tools 完整测试
覆盖 BulkOperationOptimizer / QueryCache / optimize_query_for_relationships

使用 conftest.db_session + 现有 app 模型（User），避免定义新 table 类。
"""
import time
import pytest
from sqlmodel import Session, select

from app.models import User
from services.optimization_tools import (
    BulkOperationOptimizer,
    QueryCache,
    query_cache,
    optimize_query_for_relationships,
)
from services.permission_service import Role


# ──────────────────────────── BulkOperationOptimizer ────────────────────

def _make_user_records(n: int, prefix: str = "bulk") -> list[dict]:
    from services.auth_service import hash_password
    return [
        {
            "username": f"{prefix}_u{i}",
            "email": f"{prefix}_u{i}@test.com",
            "role": Role.VIEWER,
            "password_hash": hash_password("pw"),
            "is_active": True,
        }
        for i in range(n)
    ]


class TestBulkInsert:

    def test_insert_returns_count(self, db_session: Session):
        records = _make_user_records(3, "bi")
        n = BulkOperationOptimizer.bulk_insert(db_session, User, records)
        assert n == 3

    def test_insert_empty_returns_zero(self, db_session: Session):
        n = BulkOperationOptimizer.bulk_insert(db_session, User, [])
        assert n == 0

    def test_insert_persists_rows(self, db_session: Session):
        BulkOperationOptimizer.bulk_insert(db_session, User, _make_user_records(1, "bip"))
        rows = db_session.exec(select(User).where(User.username.startswith("bip_"))).all()
        assert len(rows) >= 1


class TestBulkUpdate:

    def test_update_rows(self, db_session: Session):
        from services.auth_service import hash_password
        u = User(username="bupd_old", email="bupd_old@t.com",
                 role=Role.VIEWER, password_hash=hash_password("pw"), is_active=True)
        db_session.add(u)
        db_session.commit()
        n = BulkOperationOptimizer.bulk_update(
            db_session, User,
            updates={"username": "bupd_new"},
            filter_criteria={"username": "bupd_old"},
        )
        assert n >= 1

    def test_update_nonexistent_returns_zero(self, db_session: Session):
        n = BulkOperationOptimizer.bulk_update(
            db_session, User,
            updates={"username": "x"},
            filter_criteria={"username": "no_such_user_xyz_9999"},
        )
        assert n == 0


class TestBulkDelete:

    def test_soft_delete_sets_deleted_at(self, db_session: Session):
        from services.auth_service import hash_password
        u = User(username="bdel_tgt", email="bdel@t.com",
                 role=Role.VIEWER, password_hash=hash_password("pw"), is_active=True)
        db_session.add(u)
        db_session.commit()
        n = BulkOperationOptimizer.bulk_delete(
            db_session, User,
            filter_criteria={"username": "bdel_tgt"},
        )
        assert n >= 1
        users = db_session.exec(select(User).where(User.username == "bdel_tgt")).all()
        assert all(u.deleted_at is not None for u in users)

    def test_delete_returns_affected_count(self, db_session: Session):
        from services.auth_service import hash_password
        for i in range(3):
            u = User(username=f"bdel_batch{i}", email=f"bdel_b{i}@t.com",
                     role=Role.VIEWER, password_hash=hash_password("pw"), is_active=True)
            db_session.add(u)
        db_session.commit()
        n = BulkOperationOptimizer.bulk_delete(
            db_session, User,
            filter_criteria={"email": "bdel_b0@t.com"},
        )
        assert n >= 1


# ──────────────────────────── QueryCache ─────────────────────────────────

class TestQueryCache:

    def test_miss_returns_none(self):
        cache = QueryCache(cache_seconds=60)
        assert cache.get("no_key") is None

    def test_set_and_get_hit(self):
        cache = QueryCache(cache_seconds=60)
        cache.set("k", [1, 2, 3])
        assert cache.get("k") == [1, 2, 3]

    def test_expired_returns_none(self):
        cache = QueryCache(cache_seconds=1)
        cache.set("exp_key", "value")
        time.sleep(1.1)
        assert cache.get("exp_key") is None

    def test_clear_all(self):
        cache = QueryCache(cache_seconds=60)
        cache.set("a", 1)
        cache.set("b", 2)
        n = cache.clear()
        assert n == 2
        assert cache.get("a") is None

    def test_clear_pattern(self):
        cache = QueryCache(cache_seconds=60)
        cache.set("user:1", "alice")
        cache.set("user:2", "bob")
        cache.set("order:1", "o1")
        n = cache.clear(pattern="user")
        assert n == 2
        assert cache.get("order:1") == "o1"

    def test_get_stats(self):
        cache = QueryCache(cache_seconds=120)
        cache.set("x", 10)
        stats = cache.get_stats()
        assert stats["cached_items"] == 1
        assert stats["cache_ttl_seconds"] == 120

    def test_global_instance_exists(self):
        assert query_cache is not None
        assert isinstance(query_cache, QueryCache)

    def test_set_overwrite(self):
        cache = QueryCache(cache_seconds=60)
        cache.set("dup", "v1")
        cache.set("dup", "v2")
        assert cache.get("dup") == "v2"


# ──────────────────────── optimize_query_for_relationships ───────────────

class TestOptimizeQueryForRelationships:

    def test_returns_existing_record(self, db_session: Session):
        from services.auth_service import hash_password
        u = User(username="oqr_find", email="oqr@t.com",
                 role=Role.VIEWER, password_hash=hash_password("pw"), is_active=True)
        db_session.add(u)
        db_session.commit()
        db_session.refresh(u)
        found = optimize_query_for_relationships(db_session, User, u.id)
        assert found is not None
        assert found.username == "oqr_find"

    def test_returns_none_for_missing(self, db_session: Session):
        result = optimize_query_for_relationships(db_session, User, 999999)
        assert result is None
