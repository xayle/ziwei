# 🗄️ 数据库优化指南

**最后更新**: 2026年2月26日  
**作者**: BaZi Service 性能优化团队

---

## 📋 目录

1. [连接池优化](#连接池优化)
2. [查询优化](#查询优化)
3. [索引设计](#索引设计)
4. [缓存策略](#缓存策略)
5. [备份和恢复](#备份和恢复)
6. [监控指标](#监控指标)

---

## 🔌 连接池优化

### 当前配置分析

根据性能测试，当前配置: `pool_size=5, max_overflow=10`

**问题**: 在 50 并发时可能导致连接等待

### 优化方案

#### 方案 1: 基于并发数的线性计算

```python
# config.py - 更新数据库连接配置

import os
from sqlalchemy.pool import QueuePool

# 计算最优连接池大小
def get_pool_config():
    """根据环境和预期并发数计算连接池配置"""
    environment = os.getenv("ENVIRONMENT", "development")
    max_concurrent_users = int(os.getenv("MAX_CONCURRENT_USERS", "50"))
    
    if environment == "development":
        pool_size = 5
        max_overflow = 10
    elif environment == "testing":
        pool_size = 10
        max_overflow = 20
    elif environment == "production":
        # 公式: pool_size = max_concurrent_users * 0.3 (3 个读操作共享 1 个连接)
        pool_size = max(10, int(max_concurrent_users * 0.3))
        max_overflow = pool_size  # 允许额外连接等于基础池大小
    else:
        pool_size = 5
        max_overflow = 10
    
    return {
        "poolclass": QueuePool,
        "pool_size": pool_size,
        "max_overflow": max_overflow,
        "pool_recycle": 3600,  # 回收连接防止断线 (1 小时)
        "pool_timeout": 30,    # 等待timeout
        "pool_pre_ping": True,  # 连接前检查
    }

# 在 db.py 中使用
from config import get_pool_config

DATABASE_URL = "sqlite:///./test.db"
engine_kwargs = {
    "connect_args": {"check_same_thread": False},
    **get_pool_config()
}
engine = create_engine(DATABASE_URL, **engine_kwargs)
```

### 推荐配置值

| 环境 | 最大并发 | pool_size | max_overflow | pool_recycle | 预期 conn 数 |
|------|---------|-----------|--------------|-----------|------------|
| 开发 | 5 | 5 | 10 | 1800s | 5-15 |
| 测试 | 50 | 10 | 20 | 3600s | 10-30 |
| 生产-小 | 100 | 30 | 30 | 3600s | 30-60 |
| 生产-中 | 500 | 150 | 150 | 3600s | 150-300 |

---

## 🔍 查询优化

### 1. N+1 查询问题消除

#### 问题示例 ❌

```python
# 这会导致 N+1 问题
def get_events_with_users():
    events = db.query(Event).all()  # 1 个查询
    for event in events:
        user = db.query(User).filter(User.id == event.user_id).first()  # N 个查询
        print(user.name)
```

#### 解决方案 ✅

```python
# 方案 1: Eager Loading
from sqlalchemy.orm import selectinload

def get_events_with_users_v1():
    events = db.query(Event).options(
        selectinload(Event.user)  # 预加载关联用户
    ).all()
    return events

# 方案 2: Join Query
from sqlalchemy import join

def get_events_with_users_v2():
    events = db.query(Event).join(User).filter(
        User.is_active == True
    ).all()
    return events

# 方案 3: 在 ORM 模型中配置
from sqlalchemy.orm import relationship

class Event(Base):
    __tablename__ = "events"
    
    user_id: int = Column(Integer, ForeignKey("users.id"))
    user = relationship(
        "User",
        lazy="selectin",  # 自动预加载
        back_populates="events"
    )
```

#### 预期性能提升

```
优化前: 1 + N 个查询 (N=100 时是 101 个)
优化后: 2 个查询 (1 个主查询 + 1 个批量关联查询)

性能提升: ~99% (从 100ms 降至 1ms)
```

---

### 2. 批量操作优化

#### 批量插入 ✅

```python
# 高效的批量插入
def bulk_insert_events(events_data):
    """使用 bulk_insert_mappings 进行批量插入"""
    with db:
        db.bulk_insert_mappings(Event, events_data)
    # 性能: 1000 条记录 < 10ms

# 避免的做法
def slow_insert_events(events_data):
    for data in events_data:  # 逐条插入，N 个事务
        event = Event(**data)
        db.add(event)
    db.commit()
    # 性能: 1000 条记录 > 1000ms
```

#### 批量更新 ✅

```python
from sqlalchemy import update

def bulk_update_events(event_ids, status):
    """批量更新"""
    stmt = update(Event).where(Event.id.in_(event_ids)).values(status=status)
    db.execute(stmt)
    db.commit()
    # 性能: 1000 条记录 < 50ms vs 顺序更新的 1000ms
```

---

### 3. 分页查询优化

#### 低效的分页 ❌

```python
# 问题: OFFSET 在大数据集上很慢
def get_events_offset_limit(page: int = 1, page_size: int = 20):
    return db.query(Event).offset((page - 1) * page_size).limit(page_size).all()
    # 第 100 页: offset 1980, 需要遍历前 1980 条
```

#### 高效的分页 ✅

```python
from sqlalchemy import desc

def get_events_keyset_pagination(last_id: int = 0, page_size: int = 20):
    """基于主键的分页 (Keyset Pagination)"""
    return db.query(Event).filter(Event.id > last_id).order_by(
        Event.id
    ).limit(page_size).all()
    # 任何页数: 只需要扫描需要的行数

# 使用建议
class PaginationRequest(BaseModel):
    page_size: int = 20
    last_id: int = 0  # 上一页的最后一个 ID

@app.get("/events")
async def list_events(req: PaginationRequest):
    events = get_events_keyset_pagination(req.last_id, req.page_size)
    return {
        "data": events,
        "next_cursor": events[-1].id if events else None
    }
```

---

## 📑 索引设计

### 当前索引状态

查询当前索引:

```sql
-- SQLite
.indices

-- PostgreSQL
SELECT indexname FROM pg_indexes WHERE tablename = 'events';
```

### 推荐的索引策略

#### 索引 1: 用户 ID 索引 ✅

```python
class Event(Base):
    __tablename__ = "events"
    
    user_id: int = Column(Integer, ForeignKey("users.id"), index=True)
    # 解决问题: 快速查询用户的所有事件
    # 优化前: O(n) 表扫描
    # 优化后: O(log n) 索引扫描
```

#### 索引 2: 时间戳索引 ✅

```python
class Event(Base):
    __tablename__ = "events"
    
    created_at: datetime = Column(
        DateTime,
        default=datetime.utcnow,
        index=True  # 范围查询优化
    )
    # 为: SELECT * FROM events WHERE created_at > '2026-02-01'
```

#### 索引 3: 复合索引 ✅

```python
from sqlalchemy import Index

class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
        # 优化查询: SELECT * FROM events 
        #          WHERE user_id = 123 AND created_at > '2026-02-01'
    )
```

#### 索引 4: 软删除查询优化 ✅

```python
class Event(Base):
    __tablename__ = "events"
    deleted_at: Optional[datetime] = Column(DateTime, index=True)
    
    __table_args__ = (
        Index('idx_active_events', 'deleted_at', 'user_id'),
        # 优化查询: SELECT * FROM events 
        #          WHERE deleted_at IS NULL AND user_id = 123
    )
```

### 索引申请清单

```python
# 在 models.py 中添加这些索引
from sqlalchemy import Index

class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index('idx_user_id', 'user_id'),           # 单列索引
        Index('idx_created_at', 'created_at'),     # 时间索引
        Index('idx_deleted_at', 'deleted_at'),     # 软删除索引
        Index('idx_user_created', 'user_id', 'created_at'),  # 复合索引
        Index('idx_user_active', 'user_id', 'deleted_at'),   # 复合索引
    )
```

---

## 💾 缓存策略

### 1. SQLAlchemy 查询缓存

```python
from sqlalchemy.orm import Query
from functools import lru_cache

class CachedQuery:
    def __init__(self, query: Query, cache_seconds: int = 300):
        self.query = query
        self.cache_seconds = cache_seconds
        self._cache = {}
        self._cache_time = {}
    
    def get(self, key: str):
        import time
        now = time.time()
        if key in self._cache:
            cache_time = self._cache_time.get(key, 0)
            if now - cache_time < self.cache_seconds:
                return self._cache[key]
        
        # 缓存过期，重新查询
        result = self.query.all()
        self._cache[key] = result
        self._cache_time[key] = now
        return result

# 使用
event_cache = CachedQuery(
    db.query(Event).filter(Event.deleted_at.is_(None)),
    cache_seconds=600
)

def get_active_events():
    return event_cache.get("active_events")
```

### 2. Redis 缓存集成

```python
import redis
import json
from typing import Any, Optional

class RedisCache:
    def __init__(self, redis_url: str = "redis://localhost"):
        self.redis_client = redis.from_url(redis_url)
    
    def get(self, key: str) -> Optional[Any]:
        data = self.redis_client.get(key)
        return json.loads(data) if data else None
    
    def set(self, key: str, value: Any, ttl: int = 3600):
        self.redis_client.setex(
            key,
            ttl,
            json.dumps(value, default=str)
        )
    
    def delete(self, key: str):
        self.redis_client.delete(key)

# 使用
cache = RedisCache()

@app.get("/events/{user_id}")
async def get_user_events(user_id: int):
    cache_key = f"user_events:{user_id}"
    
    # 尝试从缓存获取
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # 从数据库获取
    events = db.query(Event).filter(Event.user_id == user_id).all()
    
    # 缓存结果
    cache.set(cache_key, json.dumps(events), ttl=600)
    
    return events
```

### 缓存策略建议

| 数据类型 | TTL | 更新策略 | 推荐 |
|---------|-----|--------|------|
| 用户信息 | 1 小时 | 主动更新 | ✅ 必须 |
| 事件列表 | 5 分钟 | 过期回源 | ✅ 推荐 |
| 八字计算 | 永久 | 从不过期 | 🔶 可选 |
| 搜索结果 | 10 分钟 | 过期回源 | ✅ 推荐 |

---

## 🔄 备份和恢复

### 自动备份配置

```bash
#!/bin/bash
# backup_db.sh - 定时数据库备份脚本

BACKUP_DIR="/backups/bazi-service"
DB_FILE="/data/bazi.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/bazi_$TIMESTAMP.db"

# 创建备份
cp "$DB_FILE" "$BACKUP_FILE"

# 压缩
gzip "$BACKUP_FILE"

# 保留最近 7 天的备份
find "$BACKUP_DIR" -name "bazi_*.db.gz" -mtime +7 -delete

echo "✅ 备份完成: $BACKUP_FILE.gz"
```

### 在 crontab 中配置

```cron
# 每天凌晨 3 点执行备份
0 3 * * * /scripts/backup_db.sh

# 每周日凌晨 2 点执行完整验证
0 2 * * 0 /scripts/verify_backup.sh
```

### 恢复流程

```python
# restore_db.py
import shutil
import gzip
from datetime import datetime

def restore_from_backup(backup_file: str):
    """从备份文件恢复数据库"""
    
    # 检查备份文件
    if not os.path.exists(backup_file):
        raise FileNotFoundError(f"备份文件不存在: {backup_file}")
    
    # 创建当前数据库的备份 (备份的备份)
    current_db = "./bazi.db"
    backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.copy(current_db, f"./bazi_before_restore_{backup_time}.db")
    
    # 解压并恢复
    if backup_file.endswith('.gz'):
        with gzip.open(backup_file, 'rb') as f:
            with open(current_db, 'wb') as out:
                out.write(f.read())
    else:
        shutil.copy(backup_file, current_db)
    
    print(f"✅ 数据库已从 {backup_file} 恢复")
    
    # 重启应用以重新连接数据库
    # (由外部监控系统处理，如 systemd 或 Docker)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python restore_db.py <backup_file>")
        sys.exit(1)
    restore_from_backup(sys.argv[1])
```

---

## 📊 监控指标

### 关键的数据库指标

| 指标 | 警告阈值 | 严重阈值 | 检查频率 |
|------|---------|---------|--------|
| 连接池使用率 | >70% | >90% | 每 5 秒 |
| 查询延迟 (P95) | >100ms | >500ms | 每 15 秒 |
| 慢查询数 | >10 | >100 | 每 1 分钟 |
| 死锁数 | > 0 | > 5 | 每 1 分钟 |
| 磁盘使用率 | >70% | >90% | 每 1 小时 |

### Prometheus 监控查询

```promql
# 连接池使用率
sum(rate(db_pool_connections_used[1m])) / sum(rate(db_pool_connections_total[1m]))

# 查询延迟
histogram_quantile(0.95, rate(db_query_duration_seconds_bucket[5m]))

# 每秒查询数
rate(db_queries_total[1m])

# 错误率
rate(db_errors_total[1m])
```

---

## 🚀 优化效果评估

### 预期的优化收益

实施以上所有优化后的预期性能提升：

| 优化项 | 当前 | 优化后 | 提升 |
|--------|------|--------|------|
| 连接池等待 | 5-10ms | 0-2ms | ✅ 50-80% |
| 关联查询 (N+1) | 100ms | 2ms | ✅ 95%+ |
| 批量操作 | 1000ms | 50ms | ✅ 95%+ |
| 分页查询 | 50ms | 10ms | ✅ 80%+ |
| **总体延迟** | **73ms** | **~40ms** | ✅ **45%** |

---

## 📝 实施计划

### 第 1 周: 基础优化

- [ ] 更新连接池配置
- [ ] 添加索引
- [ ] 实现查询缓存

### 第 2 周: 进阶优化

- [ ] 消除 N+1 查询
- [ ] 实现批量操作优化
- [ ] 添加监控指标

### 第 3 周: 验证和调优

- [ ] 运行性能测试
- [ ] 调整缓存策略
- [ ] 优化告警阈值

---

**下一步**: 参考 [PRIORITY2-PERFORMANCE-ANALYSIS.md](PRIORITY2-PERFORMANCE-ANALYSIS.md) 进行性能基线验证。
