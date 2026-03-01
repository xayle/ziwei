# 🚀 底层缺陷快速修复清单

## 第 1 优先级 - 立即修复（5个关键缺陷）

### ✅ 任务 1.1: 添加全局权限检查中间件

**工作量**: 30 分钟  
**涉及文件**: `run.py`, `routers/*`

```python
# run.py 中添加
from functools import wraps
from services.permission_cascade_service import can_access_resource

def check_permission(resource_type: str, permission: str = "view"):
    """装饰器：检查资源权限"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, user: TokenPayload = None, **kwargs):
            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            # 检查权限（使用 permission_cascade_service）
            resource_id = kwargs.get(f"{resource_type}_id")
            if not can_access_resource(session, user.user_id, resource_type, resource_id, permission):
                raise HTTPException(status_code=403, detail="Access denied")
            
            return await func(*args, user=user, **kwargs)
        return wrapper
    return decorator
```

---

### ✅ 任务 1.2: 实现真实的 `/auth/me` 接口

**工作量**: 20 分钟  
**涉及文件**: `routers/auth.py`

```python
@router.get("/api/v1/auth/me")
def get_current_user_info(
    session: Session = Depends(get_session),
    user: TokenPayload = Depends(require_user)
):
    """✅ 真实实现"""
    db_user = session.exec(select(User).where(User.id == user.user_id)).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "role": db_user.role,
        "is_active": db_user.is_active,
        "token_exp": user.exp,
        "token_iat": user.iat,
    }
```

---

### ✅ 任务 1.3: 修复 Delegation 表设计

**工作量**: 45 分钟  
**涉及文件**: `models.py`, `routers/delegation.py` (如果存在)

**步骤**:
1. 修改 Delegation 模型：`from_member_id` → `from_user_id`, `to_member_id` → `to_user_id`
2. 添加约束：`from_user_id != to_user_id`
3. 更新迁移脚本和依赖的查询

```python
# models.py
from sqlalchemy import CheckConstraint

class Delegation(SQLModel, table=True):
    __table_args__ = (
        Index("idx_delegations_from_to", "from_user_id", "to_user_id"),
        CheckConstraint("from_user_id != to_user_id"),
    )
    
    from_user_id: int = Field(foreign_key="users.id")
    to_user_id: int = Field(foreign_key="users.id")
    # ... 其他字段
```

---

### ✅ 任务 1.4: 改进异常处理和日志

**工作量**: 60 分钟  
**涉及文件**: `run.py`, `services/auth_service.py`, 其他关键路由

```python
import logging
from typing import Callable

logger = logging.getLogger(__name__)

# run.py 中的 /api/v1/verify 端点
@app.post("/api/v1/verify")
def api_verify(body: VerifyRequest, response: Response):
    try:
        result = verify_full(dt, lon, use_solar, mode)
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}", extra={"endpoint": "/verify"})
        raise HTTPException(status_code=400, detail="Invalid input parameters")
    except BackendUnavailable as e:
        logger.error(f"Backend unavailable: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")
    except Exception as e:
        logger.exception(f"Unexpected error in verify", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

### ✅ 任务 1.5: 添加 RefreshToken 自动撤销

**工作量**: 40 分钟  
**涉及文件**: `routers/auth.py`, `services/auth_service.py`

**添加修改密码接口**:
```python
@router.post("/api/v1/auth/change-password")
def change_password(
    body: ChangePasswordRequest,
    session: Session = Depends(get_session),
    user: TokenPayload = Depends(require_user)
):
    """修改密码并撤销所有旧 Token"""
    db_user = session.exec(select(User).where(User.id == user.user_id)).first()
    
    if not verify_password(body.old_password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid password")
    
    db_user.password_hash = hash_password(body.new_password)
    session.add(db_user)
    
    # ✅ 撤销所有旧 Token
    revoke_all_user_tokens(session, user.user_id)
    
    session.commit()
    return {"message": "Password changed successfully"}
```

**修改 logout 接口**:
```python
@router.post("/api/v1/auth/logout")
def logout(
    body: RefreshTokenRequest,
    session: Session = Depends(get_session),
    user: TokenPayload = Depends(require_user)
):
    """登出：撤销刷新令牌"""
    revoke_refresh_token(session, body.refresh_token)
    return {"message": "Logged out successfully"}
```

---

## 第 2 优先级 - 本周修复（5个高严重性缺陷）

### ⬜ 任务 2.1: 在所有路由中添加认证依赖

**工作量**: 120 分钟  
**涉及文件**: `routers/members.py`, `routers/events.py`, `routers/scenarios.py`, 等

**修复模板**:
```python
from run import require_user
from services.auth_service import TokenPayload

# 修改所有需要认证的 endpoint
@router.get("/api/v1/members/{member_id}")
def get_member(
    member_id: int,
    session: Session = Depends(get_session),
    user: TokenPayload = Depends(require_user)  # ✅ 添加这行
):
    # 验证权限
    if not can_access_member(session, user.user_id, member_id, "view"):
        raise HTTPException(status_code=403)
    # ...
```

---

### ⬜ 任务 2.2: 修复数据库线程安全问题

**工作量**: 30 分钟  
**涉及文件**: `db.py`

```python
import threading

_engine = None
_engine_lock = threading.Lock()

def get_engine():
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:  # Double-check
                _ensure_data_dir(settings.db_path)
                _engine = create_engine(
                    f"sqlite:///{settings.db_path}",
                    connect_args={"check_same_thread": False},
                    pool_pre_ping=True,
                    pool_recycle=3600,
                )
    return _engine
```

---

### ⬜ 任务 2.3: 修复事务完整性

**工作量**: 45 分钟  
**涉及文件**: `routers/auth.py`

关键修改：
- register 和 login 必须使用事务保证原子性
- 使用 try-except-rollback 模式

```python
def register(body: RegisterRequest, request: Request, session: Session = Depends(get_session)):
    try:
        new_user = User(...)
        session.add(new_user)
        session.flush()  # 获取 ID
        
        refresh_token = create_refresh_token_record(...)
        session.commit()
        
        token_data = create_access_token(...)
        token_data["refresh_token"] = refresh_token
        return TokenResponse(**token_data)
    
    except IntegrityError:
        session.rollback()
        logger.error("Integrity error in registration")
        raise HTTPException(status_code=409, detail="User already exists")
    except Exception as e:
        session.rollback()
        logger.exception("Registration failed")
        raise HTTPException(status_code=500, detail="Registration failed")
```

---

### ⬜ 任务 2.4: 添加数据验证约束

**工作量**: 60 分钟  
**涉及文件**: `models.py`

```python
from sqlalchemy import CheckConstraint

# Member 表
class Member(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint("gender IN ('M', 'F', 'U')"),
        CheckConstraint("birth_time_hour >= 0 AND birth_time_hour < 24"),
        CheckConstraint("birth_time_minute >= 0 AND birth_time_minute < 60"),
    )
    
    # Event 表
class Event(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint("confidence_score >= 0.0 AND confidence_score <= 1.0"),
        CheckConstraint("L_level >= 0 AND L_level <= 3"),
    )
```

---

### ⬜ 任务 2.5: 添加 Pydantic 输入验证

**工作量**: 50 分钟  
**涉及文件**: `routers/auth.py`, `schemas.py`

```python
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr  # ✅ 自动验证
    password: str = Field(..., min_length=8)
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Invalid username format")
        return v
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        if not (any(c.isupper() for c in v) and 
                any(c.islower() for c in v) and 
                any(c.isdigit() for c in v)):
            raise ValueError("Password must contain upper, lower, and digit")
        return v
```

---

## 第 3 优先级 - 下周修复（8个中等严重性缺陷）

### ⬜ 3.1: 调整 Token 过期时间
**文件**: `services/auth_service.py`  
**改动**: 60 * 24 → 15 分钟

### ⬜ 3.2: 添加日志系统
**文件**: 新建 `services/logging_service.py`  
**工作量**: 90 分钟

### ⬜ 3.3: 添加速率限制
**文件**: `run.py`  
**工作量**: 45 分钟

### ⬜ 3.4: 添加 JSON Schema 验证
**文件**: `services/bazi_full_service.py`  
**工作量**: 60 分钟

### ⬜ 3.5: 实现逻辑删除
**文件**: `models.py`, 所有删除的 endpoint  
**工作量**: 90 分钟

### ⬜ 3.6: 隐藏敏感错误消息
**文件**: 所有路由文件  
**工作量**: 60 分钟

### ⬜ 3.7: 添加 CORS 配置
**文件**: `run.py`  
**工作量**: 20 分钟

### ⬜ 3.8: 添加请求验证中间件
**文件**: `run.py`  
**工作量**: 50 分钟

---

## 📊 修复工作量统计

| 优先级 | 任务数 | 总工作量 |
|--------|--------|---------|
| 第 1 级 | 5 | 195 分钟 (3.25 小时) |
| 第 2 级 | 5 | 285 分钟 (4.75 小时) |
| 第 3 级 | 8 | 415 分钟 (6.92 小时) |
| **总计** | **18** | **895 分钟 (14.92 小时)** |

---

## 🎯 推荐时间表

| 时间 | 任务 | 工作量 |
|------|------|--------|
| **今日** | 1.1 - 1.5 | 3.25 小时 |
| **明日** | 2.1 - 2.5 | 4.75 小时 |
| **本周** | 3.1 - 3.8 | 6.92 小时 |

---

## ✅ 完成检查清单

### 第 1 级
- [ ] 1.1 全局权限检查中间件
- [ ] 1.2 /auth/me 真实实现
- [ ] 1.3 Delegation 表重构
- [ ] 1.4 异常处理改进
- [ ] 1.5 RefreshToken 撤销

### 第 2 级
- [ ] 2.1 路由认证依赖
- [ ] 2.2 数据库线程安全
- [ ] 2.3 事务完整性
- [ ] 2.4 数据验证约束
- [ ] 2.5 输入验证

### 第 3 级
- [ ] 3.1 Token 过期时间
- [ ] 3.2 日志系统
- [ ] 3.3 速率限制
- [ ] 3.4 JSON 验证
- [ ] 3.5 逻辑删除
- [ ] 3.6 错误消息
- [ ] 3.7 CORS 配置
- [ ] 3.8 请求验证

---

## 🧪 修复后的验证方法

### 权限验证测试
```bash
# 测试无认证访问被拒绝
curl -s http://localhost:8000/api/v1/members/1 | jq .

# 测试有认证访问成功
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"pass123"}' | jq -r .access_token)

curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/members/1 | jq .
```

### 事务一致性测试
```bash
# 同时发起多个注册请求，检查是否有重复数据
for i in {1..10}; do
  curl -s -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"testuser\",\"email\":\"test@example.com\",\"password\":\"Pass123\"}" &
done
wait

# 检查数据库中是否只有 1 条记录
sqlite3 data/mingli.db "SELECT COUNT(*) FROM users WHERE username='testuser';"
```

### 线程安全测试
```bash
# 多线程并发访问数据库
python -c "
import threading
from db import get_engine

engines = []
for i in range(10):
    t = threading.Thread(target=lambda: engines.append(get_engine()))
    t.start()
    t.join()

print(f'Created {len(set(id(e) for e in engines))} unique engines (should be 1)')
"
```

---

**更新时间**: 2026-02-26  
**下次审查**: 修复第 1 级后

