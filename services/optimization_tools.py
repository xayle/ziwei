"""
Phase 2 优化工具 - 批量操作、缓存、分页优化
"""
import json
import time
import logging
from typing import Optional, List, Dict, Any, Type, TypeVar
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from sqlmodel import Session, select
from sqlalchemy import update, insert, delete

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BulkOperationOptimizer:
    """批量操作优化工具"""
    
    @staticmethod
    def bulk_insert(session: Session, model_class: Type[T], records: List[Dict[str, Any]]) -> int:
        """
        高效的批量插入
        
        Args:
            session: SQLModel Session
            model_class: 数据模型类
            records: 记录列表
            
        Returns:
            插入的记录数
        """
        if not records:
            return 0
        
        try:
            # 使用 bulk_insert_mappings 进行高效批量插入
            session.bulk_insert_mappings(model_class, records)  # type: ignore[arg-type]
            session.commit()
            logger.info(f"✅ 批量插入成功: {len(records)} 条 {model_class.__tablename__} 记录")  # type: ignore[attr-defined]
            return len(records)
        except Exception as e:
            session.rollback()
            logger.error(f"❌ 批量插入失败: {str(e)}")
            raise
    
    @staticmethod
    def bulk_update(session: Session, model_class: Type[T], updates: Dict[str, Any], 
                   filter_criteria: Dict[str, Any]) -> int:
        """
        高效的批量更新
        
        Args:
            session: SQLModel Session
            model_class: 数据模型类
            updates: 更新的字段字典
            filter_criteria: 过滤条件字典
            
        Returns:
            更新的记录数
        """
        try:
            stmt = update(model_class)
            
            # 应用过滤条件
            for key, value in filter_criteria.items():
                if hasattr(model_class, key):
                    stmt = stmt.where(getattr(model_class, key) == value)
            
            # 应用更新
            stmt = stmt.values(**updates)
            result = session.execute(stmt)
            session.commit()
            
            rows_updated = result.rowcount  # type: ignore[attr-defined]
            logger.info(f"✅ 批量更新成功: 更新 {rows_updated} 条记录")
            return rows_updated
        except Exception as e:
            session.rollback()
            logger.error(f"❌ 批量更新失败: {str(e)}")
            raise
    
    @staticmethod
    def bulk_delete(session: Session, model_class: Type[T], 
                   filter_criteria: Dict[str, Any]) -> int:
        """
        高效的批量软删除
        
        Args:
            session: SQLModel Session
            model_class: 数据模型类
            filter_criteria: 过滤条件字典
            
        Returns:
            删除的记录数（更新为已删除）
        """
        try:
            now = datetime.now(timezone.utc)
            
            stmt = update(model_class).values(deleted_at=now)
            
            # 应用过滤条件
            for key, value in filter_criteria.items():
                if hasattr(model_class, key):
                    stmt = stmt.where(getattr(model_class, key) == value)
            
            result = session.execute(stmt)
            session.commit()
            
            rows_deleted = result.rowcount  # type: ignore[attr-defined]
            logger.info(f"✅ 批量软删除成功: 删除 {rows_deleted} 条记录")
            return rows_deleted
        except Exception as e:
            session.rollback()
            logger.error(f"❌ 批量删除失败: {str(e)}")
            raise


class PaginationOptimizer:
    """分页查询优化工具 - 使用 Keyset 分页替代 Offset/Limit"""
    
    @staticmethod
    def keyset_pagination(session: Session, model_class: Type[T], 
                         last_id: int = 0, page_size: int = 20,
                         order_by_field: str = "id") -> List[T]:
        """
        基于主键的 Keyset 分页 - 比 OFFSET 更高效
        
        Args:
            session: SQLModel Session
            model_class: 数据模型类
            last_id: 上一页的最后一个 ID (游标)
            page_size: 每页数量
            order_by_field: 排序字段名
            
        Returns:
            当前页的记录列表
        """
        try:
            stmt = select(model_class).where(
                getattr(model_class, "id") > last_id
            ).order_by(
                getattr(model_class, order_by_field)
            ).limit(page_size)
            
            records = session.exec(stmt).all()
            logger.debug(f"✅ Keyset 分页: 获取 {len(records)} 条记录 (last_id={last_id})")
            return list(records)
        except Exception as e:
            logger.error(f"❌ Keyset 分页失败: {str(e)}")
            raise
    
    @staticmethod
    def get_next_cursor(records: List[T]) -> Optional[int]:
        """
        获取下一页的游标 (最后一条的 ID)
        
        Args:
            records: 当前页的记录列表
            
        Returns:
            最后一条记录的 ID，如果列表为空则返回 None
        """
        if records:
            last_record = records[-1]
            if hasattr(last_record, 'id'):
                return last_record.id  # type: ignore[attr-defined]
        return None


class QueryCache:
    """查询缓存 - 减少重复查询"""
    
    def __init__(self, cache_seconds: int = 300):
        """
        初始化缓存
        
        Args:
            cache_seconds: 缓存过期时间（秒）
        """
        self.cache_seconds = cache_seconds
        self._cache: Dict[str, tuple[Any, float]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """
        从缓存获取
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的值，如果不存在或过期则返回 None
        """
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self.cache_seconds:
                logger.debug(f"🔄 缓存命中: {key}")
                return value
            else:
                # 缓存过期，删除
                del self._cache[key]
                logger.debug(f"⏰ 缓存过期: {key}")
        
        return None
    
    def set(self, key: str, value: Any) -> None:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        self._cache[key] = (value, time.time())
        logger.debug(f"💾 缓存设置: {key}")
    
    def clear(self, pattern: Optional[str] = None) -> int:
        """
        清除缓存
        
        Args:
            pattern: 缓存键模式（如果为 None 则清除所有）
            
        Returns:
            清除的缓存数量
        """
        if pattern is None:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"🗑️  清除所有缓存: {count} 项")
            return count
        
        count = 0
        keys_to_delete = [k for k in self._cache.keys() if pattern in k]
        for k in keys_to_delete:
            del self._cache[k]
            count += 1
        
        logger.info(f"🗑️  清除缓存: {count} 项 (模式: {pattern})")
        return count
    
    def get_stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        return {
            "cached_items": len(self._cache),
            "cache_ttl_seconds": self.cache_seconds,
        }


class RedisCache:
    """Redis 缓存客户端 - 可选的有状态缓存"""
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        初始化 Redis 缓存
        
        Args:
            redis_url: Redis 连接 URL（如果为 None 则禁用）
        """
        self.redis_url = redis_url or "redis://localhost:6379"
        self.enabled = redis_url is not None
        self._client = None
        
        if self.enabled:
            try:
                import redis  # type: ignore
                self._client = redis.from_url(self.redis_url)
                self._client.ping()
                logger.info(f"✅ Redis 缓存已连接: {self.redis_url}")
            except Exception as e:
                logger.warning(f"⚠️  Redis 连接失败，禁用缓存: {str(e)}")
                self.enabled = False
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        从 Redis 获取
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的 JSON 数据，如果不存在则返回 None
        """
        if not self.enabled or not self._client:
            return None
        
        try:
            data = self._client.get(key)
            if data:
                logger.debug(f"🔄 Redis 缓存命中: {key}")
                return json.loads(data)
        except Exception as e:
            logger.warning(f"⚠️  Redis 读取失败: {str(e)}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        设置 Redis 缓存
        
        Args:
            key: 缓存键
            value: 缓存值（必须能 JSON 序列化）
            ttl: 过期时间（秒）
            
        Returns:
            是否成功
        """
        if not self.enabled or not self._client:
            return False
        
        try:
            self._client.setex(
                key,
                ttl,
                json.dumps(value, default=str)
            )
            logger.debug(f"💾 Redis 缓存设置: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.warning(f"⚠️  Redis 写入失败: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        删除 Redis 缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功
        """
        if not self.enabled or not self._client:
            return False
        
        try:
            self._client.delete(key)
            logger.debug(f"🗑️  Redis 缓存删除: {key}")
            return True
        except Exception as e:
            logger.warning(f"⚠️  Redis 删除失败: {str(e)}")
            return False


class PerformanceMonitor:
    """性能监控工具 - 跟踪查询和操作性能"""
    
    def __init__(self):
        self.operations: List[Dict[str, Any]] = []
    
    def record_query(self, operation_name: str, duration_ms: float, 
                    row_count: int, success: bool = True) -> None:
        """记录查询性能"""
        self.operations.append({
            "timestamp": datetime.now(timezone.utc),
            "operation": operation_name,
            "duration_ms": duration_ms,
            "row_count": row_count,
            "success": success,
        })
        
        if duration_ms > 100:  # 超过 100ms 的慢查询
            logger.warning(
                f"⚠️  慢查询检测: {operation_name} - {duration_ms:.2f}ms ({row_count} 行)"
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        if not self.operations:
            return {}
        
        total_duration = sum(op["duration_ms"] for op in self.operations)
        avg_duration = total_duration / len(self.operations)
        slow_queries = [op for op in self.operations if op["duration_ms"] > 100]
        
        return {
            "total_operations": len(self.operations),
            "total_duration_ms": total_duration,
            "average_duration_ms": avg_duration,
            "slow_queries": len(slow_queries),
            "slow_operations": [{"op": sq["operation"], "ms": sq["duration_ms"]} 
                               for sq in slow_queries[:10]]
        }
    
    def clear(self) -> None:
        """清除统计数据"""
        self.operations.clear()


# 全局实例
query_cache = QueryCache(cache_seconds=600)  # 10 分钟缓存
redis_cache = RedisCache()  # 可选的 Redis 缓存
perf_monitor = PerformanceMonitor()  # 性能监控


def optimize_query_for_relationships(session: Session, model_class: Type[T], 
                                     primary_key: Any) -> Optional[T]:
    """
    带关系加载优化的查询
    
    Example:
        user = optimize_query_for_relationships(session, User, user_id)
    """
    try:
        start_time = time.time()
        
        stmt = select(model_class).where(model_class.id == primary_key)  # type: ignore[union-attr]
        result = session.exec(stmt).first()
        
        duration_ms = (time.time() - start_time) * 1000
        perf_monitor.record_query(
            f"get_{model_class.__tablename__}",  # type: ignore[attr-defined]
            duration_ms,
            1 if result else 0,
            success=True
        )
        
        return result
    except Exception as e:
        logger.error(f"❌ 查询优化失败: {str(e)}")
        perf_monitor.record_query(
            f"get_{model_class.__tablename__}",  # type: ignore[attr-defined]
            0,
            0,
            success=False
        )
        raise
