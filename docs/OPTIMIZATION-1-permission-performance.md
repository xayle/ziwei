# 性能优化方案：权限检查 (v1.0)

## 问题诊断

当前方案的瓶颈：
```
每个API调用 → has_permission() → 查DB (FK check + delegate lookup)
                          ↓
             filter_results_by_role() → 逐项扫描results

问题: 1000个results需要过滤 → 1000次比较 → 可能>1000ms ❌
```

---

## 🎯 方案A: 缓存权限决策 (推荐，20% 代码改动)

### 核心思想
将权限决策缓存在**Redis**或**内存**中，5分钟过期。

### 实现
```python
# middleware/authorization_cached.py
from functools import lru_cache
import hashlib
from datetime import datetime, timedelta

class PermissionCache:
    """权限决策缓存"""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache = {}
        self.ttl = ttl_seconds
    
    def _cache_key(self, user_id: str, resource_type: str, 
                  action: str, resource_owner_id: str) -> str:
        """生成缓存key"""
        key = f"{user_id}:{resource_type}:{action}:{resource_owner_id}"
        return hashlib.md5(key.encode()).hexdigest()
    
    async def get_permission(self, user_id: str, role: str,
                            resource_type: str, action: str,
                            resource_owner_id: str) -> bool:
        """获取缓存的权限决策"""
        cache_key = self._cache_key(user_id, resource_type, action, resource_owner_id)
        
        # 1. 检查缓存
        if cache_key in self.cache:
            cached_result, expiry = self.cache[cache_key]
            if datetime.now() < expiry:
                return cached_result  # ✓ 命中，<1ms
            else:
                del self.cache[cache_key]  # 过期，清除
        
        # 2. 计算权限（调用原来的has_permission逻辑）
        result = await self._compute_permission(
            user_id, role, resource_type, action, resource_owner_id
        )
        
        # 3. 缓存结果
        expiry = datetime.now() + timedelta(seconds=self.ttl)
        self.cache[cache_key] = (result, expiry)
        
        return result
    
    async def _compute_permission(self, user_id, role, ...):
        """原来的has_permission逻辑"""
        # ADMIN总是允许
        if role == "ADMIN":
            return True
        
        # OWNER权限检查
        if role == "OWNER":
            if resource_owner_id == user_id:
                return True
            # 检查delegate (从DB查询)
            if await self._is_delegate_for(user_id, resource_owner_id):
                return action in ["create", "read", "update"]
            return False
        
        # ... 其他角色
        return False
    
    def invalidate(self, user_id: str = None):
        """失效缓存"""
        if user_id:
            # 失效该用户所有权限缓存
            keys_to_delete = [k for k in self.cache.keys() 
                            if k.startswith(user_id)]
            for k in keys_to_delete:
                del self.cache[k]
        else:
            # 清空所有缓存
            self.cache.clear()

# 全局缓存实例
permission_cache = PermissionCache(ttl_seconds=300)

# 使用方式
@router.post("/api/v1/events")
async def create_event(request: Request):
    auth = request.state.auth_context
    
    # 使用缓存权限检查（而不是直接调用has_permission）
    has_perm = await permission_cache.get_permission(
        auth.user_id, 
        auth.role,
        "event", 
        "create",
        auth.user_id  # 新创建的event所有者总是当前用户
    )
    
    if not has_perm:
        raise HTTPException(status_code=403)
    
    # ... 创建event
```

### 性能提升
```
┌─ 缓存命中: <1ms (99% case)
├─ 缓存失效要查DB: ~50ms (1% case)
└─ 总平均延迟: <2ms ✓
```

### 注意事项
```yaml
何时失效缓存:
  - 用户授权发生变化时 (DELEGATE新增/撤销)
  - 用户角色变更时 (OWNER → ADMIN)
  - Member关系变更时 (FAMILY_MEMBER删除)

实现方式:
  # 选项1: 同步失效
  async def grant_delegation(...):
      delegation = await create_delegation(...)
      permission_cache.invalidate(delegator_id)  # 立即失效
      return delegation
  
  # 选项2: 异步失效 (不阻塞主流程)
  async def grant_delegation(...):
      delegation = await create_delegation(...)
      background_task(permission_cache.invalidate, delegator_id)
      return delegation
```

---

## 🎯 方案B: SQL层面过滤 (推荐用于大数据集)

### 核心思想
不在Python中过滤，直接在SQL WHERE子句中实现权限检查。

### 实现
```python
# repositories/event_repository.py
class EventRepository:
    
    async def find_accessible(self, user_id: str, role: str, 
                            limit: int = 100) -> List[Event]:
        """
        找出用户可访问的所有events
        (不用Python过滤，直接用SQL)
        """
        
        if role == "ADMIN":
            # ADMIN可见所有event
            query = "SELECT * FROM events LIMIT :limit"
            params = {"limit": limit}
        
        elif role == "OWNER":
            # OWNER可见:
            # 1. 自己的event
            # 2. 自己被delegate的人的event
            query = """
                SELECT e.* FROM events e
                WHERE e.owner_id = :user_id
                   OR e.owner_id IN (
                       SELECT owner_id FROM delegations 
                       WHERE delegate_id = :user_id 
                       AND status = 'APPROVED'
                   )
                LIMIT :limit
            """
            params = {"user_id": user_id, "limit": limit}
        
        elif role == "FAMILY_MEMBER":
            # FAMILY_MEMBER可见:
            # 1. 自己的event
            # 2. 直系家族成员的event (if APPROVED)
            query = """
                SELECT e.* FROM events e
                WHERE e.owner_id = :user_id
                   OR e.owner_id IN (
                       SELECT DISTINCT owner_id FROM members m
                       WHERE m.owner_id IN (
                           SELECT owner_id FROM members m2
                           WHERE m2.member_id = (
                               SELECT member_id FROM members 
                               WHERE owner_id = :user_id AND relationship = 'SELF'
                           )
                           AND relationship IN ('SPOUSE', 'CHILD', 'PARENT')
                       )
                       AND m.authorization.status = 'APPROVED'
                   )
                LIMIT :limit
            """
            params = {"user_id": user_id, "limit": limit}
        
        else:  # GUEST,DELEGATE等
            query = "SELECT * FROM events WHERE 1=0"  # 无权限
            params = {}
        
        result = await self.db.fetch(query, params)
        return [Event(**row) for row in result]
```

### 性能对比
```
方案A (Python过滤):
  1. SELECT * FROM events         → 返回1000行 (~10ms)
  2. Python: filter_results_by_role()  → 遍历1000行 (~50ms)
  總計: ~60ms

方案B (SQL WHERE):
  SELECT * FROM events WHERE...   → 直接返回10行 (~5ms)
  總計: ~5ms ✓ (12x加速)
```

### 缺点
- SQL复杂度高 (多层subquery)
- 维护成本高 (权限规则变更要改SQL)

**建议**: 对于结果集很大的查询(>100条)用方案B，小集合用方案A。

---

## 🎯 方案C: 两层检查 (综合方案，推荐)

### 架构
```
┌─ API端点
│
├─ Layer 1: 快速路径 (99% case)
│   └─ 如果resource_owner == user_id → ✓ 直接通过 (<1ms)
│
├─ Layer 2: 缓存 
│   └─ 检查permission_cache → ✓ 命中 (<1ms)
│
└─ Layer 3: DB查询
    └─ 检查delegate/family关系 → (~50ms)
```

### 代码
```python
@require_permission_fast("event", "read")
async def get_event(event_id: str, request: Request):
    """
    @require_permission_fast 装饰器试图快速判断，
    如果失败才进入完整权限检查
    """
    auth = request.state.auth_context
    event = await event_repo.get(event_id)
    
    # 快速路径
    if event.owner_id == auth.user_id:
        return event  # ✓ <1ms
    
    # 缓存路径
    cached_perm = await permission_cache.get_permission(...)
    if not cached_perm:
        raise HTTPException(status_code=403)
    
    return event
```

---

## 📊 方案对比

| 方案 | 实现成本 | 性能 | 维护难度 | 推荐场景 |
|------|--------|------|--------|--------|
| **A (缓存)** | 低 | 99%<2ms | 低 | 通用API |
| **B (SQL)** | 中 | 95%<10ms | 中 | 大结果集查询 |
| **C (两层)** | 中 | 97%<3ms | 中 | 生产推荐 ✓ |

---

## 🚀 立即行动

### Week 2-3 (实现)
```shell
□ 创建 middleware/authorization_cached.py
□ 修改所有@require_permission装饰器使用缓存
□ 添加permission_cache.invalidate()在权限变更处
□ 性能测试: 1000条results过滤时间 <5ms
```

### 基准测试脚本
```python
# tests/test_permission_performance.py
import time
from middleware.authorization_cached import permission_cache

async def test_filter_1000_results():
    # 创建1000个event
    events = [Event(event_id=i, owner_id=f"owner-{i%5}", ...) 
              for i in range(1000)]
    
    start = time.time()
    filtered = permission_cache.filter_results_by_role(
        events, "event", "FAMILY_MEMBER", "user-1"
    )
    elapsed = time.time() - start
    
    assert elapsed < 0.005, f"过滤耗时{elapsed*1000}ms, 应<5ms"
```

