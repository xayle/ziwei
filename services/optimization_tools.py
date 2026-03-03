"""
Phase 2 优化工具 - 批量操作、缓存、查询优化

保留类:
  BulkOperationOptimizer  — 批量 insert/update/soft-delete
  QueryCache              — 轻量级内存缓存（routers/members.py、routers/events.py 使用）
  optimize_query_for_relationships — 带性能采样的单条查询

已移除（无使用者）:
  PaginationOptimizer, RedisCache, PerformanceMonitor
"""
import time
import logging
from typing import Optional, List, Dict, Any, Type, TypeVar
from datetime import datetime, timezone
from sqlmodel import Session, select
from sqlalchemy import update

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BulkOperationOptimizer:
    """批量操作优化工具"""

    @staticmethod
    def bulk_insert(session: Session, model_class: Type[T], records: List[Dict[str, Any]]) -> int:
        """高效批量插入；返回插入行数。"""
        if not records:
            return 0
        try:
            session.bulk_insert_mappings(model_class, records)  # type: ignore[arg-type]
            session.commit()
            logger.info("batch_insert OK: %d rows → %s", len(records), getattr(model_class, "__tablename__", "?"))
            return len(records)
        except Exception as e:
            session.rollback()
            logger.error("batch_insert FAIL: %s", e)
            raise

    @staticmethod
    def bulk_update(
        session: Session,
        model_class: Type[T],
        updates: Dict[str, Any],
        filter_criteria: Dict[str, Any],
    ) -> int:
        """高效批量更新；返回更新行数。"""
        try:
            stmt = update(model_class)  # type: ignore[arg-type]
            for key, value in filter_criteria.items():
                if hasattr(model_class, key):
                    stmt = stmt.where(getattr(model_class, key) == value)
            stmt = stmt.values(**updates)
            result = session.execute(stmt)
            session.commit()
            rows = result.rowcount  # type: ignore[attr-defined]
            logger.info("batch_update OK: %d rows", rows)
            return rows
        except Exception as e:
            session.rollback()
            logger.error("batch_update FAIL: %s", e)
            raise

    @staticmethod
    def bulk_delete(
        session: Session,
        model_class: Type[T],
        filter_criteria: Dict[str, Any],
    ) -> int:
        """软删除（设 deleted_at）；返回受影响行数。"""
        try:
            now = datetime.now(timezone.utc)
            stmt = update(model_class).values(deleted_at=now)  # type: ignore[arg-type]
            for key, value in filter_criteria.items():
                if hasattr(model_class, key):
                    stmt = stmt.where(getattr(model_class, key) == value)
            result = session.execute(stmt)
            session.commit()
            rows = result.rowcount  # type: ignore[attr-defined]
            logger.info("batch_soft_delete OK: %d rows", rows)
            return rows
        except Exception as e:
            session.rollback()
            logger.error("batch_soft_delete FAIL: %s", e)
            raise


class QueryCache:
    """轻量级内存查询缓存（TTL 过期，非线程安全）。"""

    def __init__(self, cache_seconds: int = 300):
        self.cache_seconds = cache_seconds
        self._cache: Dict[str, tuple[Any, float]] = {}

    def get(self, key: str) -> Optional[Any]:
        """命中且未过期则返回缓存值，否则返回 None。"""
        if key in self._cache:
            value, ts = self._cache[key]
            if time.time() - ts < self.cache_seconds:
                return value
            del self._cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """写入缓存。"""
        self._cache[key] = (value, time.time())

    def clear(self, pattern: Optional[str] = None) -> int:
        """清除全部或带指定 pattern 的条目；返回清除数。"""
        if pattern is None:
            count = len(self._cache)
            self._cache.clear()
            return count
        keys = [k for k in self._cache if pattern in k]
        for k in keys:
            del self._cache[k]
        return len(keys)

    def get_stats(self) -> Dict[str, int]:
        return {"cached_items": len(self._cache), "cache_ttl_seconds": self.cache_seconds}


# 全局实例（router 直接使用）
query_cache = QueryCache(cache_seconds=600)


def optimize_query_for_relationships(session: Session, model_class: Type[T], primary_key: Any) -> Optional[T]:
    """
    按主键单条查询，附带耗时日志。

    Example::
        user = optimize_query_for_relationships(session, User, user_id)
    """
    t0 = time.time()
    try:
        stmt = select(model_class).where(model_class.id == primary_key)  # type: ignore[union-attr]
        result = session.exec(stmt).first()
        ms = (time.time() - t0) * 1000
        if ms > 100:
            logger.warning("slow_query: %s pk=%s %.1fms", getattr(model_class, "__tablename__", "?"), primary_key, ms)
        return result
    except Exception as e:
        logger.error("query FAIL: %s", e)
        raise

