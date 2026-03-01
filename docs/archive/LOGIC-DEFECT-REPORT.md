# 🔴 底层逻辑缺陷分析报告

**生成日期**: 2026-02-26  
**版本**: v5.1.0  
**严重程度**: 混合（4 🔴 关键 + 8 🟠 高 + 6 🟡 中）

---

## 📊 缺陷汇总

| 类别 | 关键 | 高 | 中 | 总计 |
|------|------|-----|-----|------|
| 认证授权 | 2 | 2 | 1 | 5 |
| 数据库 | 1 | 2 | 0 | 3 |
| 错误处理 | 1 | 2 | 2 | 5 |
| 安全性 | 0 | 2 | 2 | 4 |
| 事务一致性 | 0 | 0 | 1 | 1 |

**总计**: 18 个缺陷

---

## 🔴 关键缺陷 (必须修复)

### 缺陷 #1: 权限验证完全缺失 (CRITICAL)

**位置**: `routers/` 所有文件  
**问题**: 除了 auth 路由外，其他所有 endpoint 都缺少权限检查

```python
# ❌ 错误示例: routers/members.py (假设存在)
@router.get("/api/v1/members/{member_id}")
def get_member(member_id: int, session: Session = Depends(get_session)):
    member = session.exec(select(Member).where(Member.id == member_id)).first()
    return member  # 任何人都能访问任何成员的信息！
```

**风险**: 
- 隐私泄露：用户A能看到用户B的成员信息
- 无权限检查，直接返回数据库记录

**修复方案**:
```python
from run import require_user
from services.permission_cascade_service import can_access_member

@router.get("/api/v1/members/{member_id}")
def get_member(
    member_id: int, 
    session: Session = Depends(get_session),
    user: TokenPayload = Depends(require_user)  # ✅ 强制认证
):
    member = session.exec(select(Member).where(Member.id == member_id)).first()
    
    # ✅ 检查权限
    if not can_access_member(session, user.user_id, member_id, "view"):
        raise HTTPException(status_code=403, detail="Access denied")
    
    return member
```

---

### 缺陷 #2: 获取当前用户信息接口虚假 (CRITICAL)

**位置**: `routers/auth.py` 第 95-104 行

```python
@router.get("/auth/me")
def get_current_user_info(token: str | None = None):
    """获取当前用户信息（需要有效的token）"""
    if not token:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    return {
        "message": "用户信息获取需要通过require_user依赖",
        "hint": "在run.py中配置此endpoint时使用require_user依赖"
    }
```

**问题**:
- 端点完全无效，只返回虚拟消息
- 不验证 token
- 不返回实际用户信息
- 用户会调用它却得不到任何结果

**修复方案**:
```python
from run import require_user

@router.get("/api/v1/auth/me")
def get_current_user_info(
    session: Session = Depends(get_session),
    user: TokenPayload = Depends(require_user)
):
    """获取当前用户信息"""
    db_user = session.exec(select(User).where(User.id == user.user_id)).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": db_user.id,
        "username": db_user.username,
        "email": db_user.email,
        "role": db_user.role,
        "is_active": db_user.is_active,
        "created_at": db_user.created_at,
    }
```

---

### 缺陷 #3: Delegation 表设计错误 (CRITICAL)

**位置**: `models.py` 第 147-161 行

```python
class Delegation(SQLModel, table=True):
    from_member_id: int = Field(foreign_key="users.id", index=True)  # ❌ 错误！
    to_member_id: int = Field(foreign_key="users.id", index=True)    # ❌ 错误！
    member_scope: Optional[int] = Field(default=None, foreign_key="members.id")
```

**问题**:
1. 表名是 `delegations`，但字段名是 `from_member_id` 和 `to_member_id`
2. 外键指向 `users` 表，但字段名暗示指向 `members`
3. 没有约束确保 `from_member_id != to_member_id`（一个用户不能向自己授予权限）
4. 表的用途不清晰

**修复方案**:
```python
class Delegation(SQLModel, table=True):
    """权限委托表 - 用户间的权限授予"""
    __tablename__: ClassVar[str] = "delegations"
    __table_args__ = (
        Index("idx_delegations_from_to", "from_user_id", "to_user_id"),
        CheckConstraint("from_user_id != to_user_id"),  # ✅ 防止自委托
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    from_user_id: int = Field(foreign_key="users.id", index=True)  # ✅ 清晰
    to_user_id: int = Field(foreign_key="users.id", index=True)    # ✅ 清晰
    permission_type: str  # "view", "edit", "share", "manage"
    member_scope: Optional[int] = Field(default=None, foreign_key="members.id")
    
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
```

---

### 缺陷 #4: 异常处理过于宽泛 (CRITICAL)

**位置**: `run.py` 第 238-245 行

```python
try:
    result = verify_full(dt, lon=lon, use_solar=body.solar_time_enabled, mode=body.mode)
except HTTPException:
    raise
except Exception as exc:  # pragma: no cover - rely on existing verify tests
    raise HTTPException(status_code=500, detail=str(exc))  # ❌ 隐藏真实错误
```

**问题**:
- `except Exception as exc` 会捕获所有异常，包括程序员不预期的
- 返回 `detail=str(exc)` 可能暴露敏感信息（内部路径、数据库错误等）
- 没有日志记录，无法调试

**修复方案**:
```python
import logging

logger = logging.getLogger(__name__)

try:
    result = verify_full(dt, lon=lon, use_solar=body.solar_time_enabled, mode=body.mode)
except HTTPException:
    raise
except ValueError as e:  # ✅ 明确捕获业务逻辑错误
    logger.warning(f"Validation error for verify: {str(e)}", extra={"request_id": req_id})
    raise HTTPException(status_code=400, detail="Invalid input")
except Exception as exc:  # ✅ 保留日志但隐藏细节
    logger.exception(f"Unexpected error in verify", extra={"request_id": req_id, "error": str(exc)})
    raise HTTPException(status_code=500, detail="Internal server error")
```

---

## 🟠 高严重性缺陷 (应该修复)

### 缺陷 #5: 认证依赖未在路由中使用 (HIGH)

**位置**: `routers/` 中大多数文件

**问题**: `require_user` 依赖在 `run.py` 中定义，但 routers 没有使用它

```python
# ❌ routers/members.py (假设)
@router.post("/api/v1/members")
def create_member(body: MemberRequest, session: Session = Depends(get_session)):
    # 没有认证检查，任何人都能创建成员
    ...
```

**修复方案**: 在所有需要认证的 endpoint 中添加 `user: TokenPayload = Depends(require_user)`

---

### 缺陷 #6: RefreshToken 自动撤销缺失 (HIGH)

**位置**: `services/auth_service.py` 第 180-200 行

```python
def revoke_all_user_tokens(session, user_id: int):
    """撤销用户的所有刷新令牌 (如修改密码时调用)"""
    # 函数存在但没被调用！
```

**问题**:
1. 当用户修改密码时，应该撤销所有旧 RefreshToken
2. 当用户禁用账户时，应该撤销所有 Token
3. 但这个函数从未被调用

**修复方案**:
```python
# routers/auth.py 中需要添加修改密码端点
@router.post("/api/v1/auth/change-password")
def change_password(
    body: ChangePasswordRequest,
    session: Session = Depends(get_session),
    user: TokenPayload = Depends(require_user)
):
    """修改密码"""
    db_user = session.exec(select(User).where(User.id == user.user_id)).first()
    
    if not verify_password(body.old_password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Old password is incorrect")
    
    # ✅ 更新密码
    db_user.password_hash = hash_password(body.new_password)
    session.add(db_user)
    
    # ✅ 撤销所有旧 Token（强制重新登录）
    revoke_all_user_tokens(session, user.user_id)
    
    session.commit()
    return {"message": "Password changed successfully"}
```

---

### 缺陷 #7: 数据库全局变量非线程安全 (HIGH)

**位置**: `db.py` 第 8-15 行

```python
_engine = None  # ❌ 全局变量，非线程安全

def get_engine():
    global _engine
    if _engine is None:  # ❌ Race condition: 多线程下可能创建多个 engine
        _engine = create_engine(...)
    return _engine
```

**问题** (在多进程/多线程场景下):
- 两个线程同时读 `_engine is None`，都为 True
- 两个线程都创建新的 engine
- 导致连接池错乱、泄漏

**修复方案**:
```python
import threading

_engine = None
_engine_lock = threading.Lock()

def get_engine():
    global _engine
    if _engine is None:
        with _engine_lock:  # ✅ 加锁确保只创建一次
            if _engine is None:  # Double-check locking
                _ensure_data_dir(settings.db_path)
                _engine = create_engine(
                    f"sqlite:///{settings.db_path}", 
                    connect_args={"check_same_thread": False}
                )
    return _engine
```

—或者使用 SQLAlchemy 5.0+ 的 create_pool_pre_ping：

```python
_engine = create_engine(
    ...,
    pool_pre_ping=True,  # ✅ 使用前检查连接
    pool_recycle=3600,    # ✅ 1小时回收连接
)
```

---

### 缺陷 #8: 事务完整性不足 (HIGH)

**位置**: `routers/auth.py` 第 57-88 行 (register)

```python
def register(body: RegisterRequest, request: Request, session: Session = Depends(get_session)):
    # ...
    new_user = User(...)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)  # ❌ 如果刷新失败呢？
    
    token_data = create_access_token(...)
    
    try:
        refresh_token = create_refresh_token_record(session, new_user.id or 0, ...)
        token_data["refresh_token"] = refresh_token
    except Exception:  # ❌ 吞掉异常
        pass
    
    return TokenResponse(**token_data)
```

**问题**:
1. User 创建成功，但 RefreshToken 创建失败
2. 用户注册了，但不能使用 refresh token 功能
3. 没有日志记录这个失败

**修复方案**:
```python
def register(body: RegisterRequest, request: Request, session: Session = Depends(get_session)):
    # ...创建用户...
    
    try:
        new_user = User(...)
        session.add(new_user)
        session.flush()  # ✅ 先 flush，获取自增 ID
        
        # 创建 RefreshToken（必须成功）
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("User-Agent") or ""
        refresh_token = create_refresh_token_record(
            session, 
            new_user.id or 0, 
            ip_address, 
            user_agent
        )
        
        session.commit()  # ✅ 一起提交，保证原子性
        
        token_data = create_access_token(new_user.id or 0, new_user.username, role=new_user.role)
        token_data["refresh_token"] = refresh_token
        
        return TokenResponse(**token_data)
    except IntegrityError as e:
        session.rollback()
        logger.error(f"Registration integrity error: {str(e)}")
        raise HTTPException(status_code=409, detail="Username or email already exists")
    except Exception as e:
        session.rollback()
        logger.exception(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Registration failed")
```

---

## 🟡 中等严重性缺陷 (建议修复)

### 缺陷 #9: JWT Token 过期时间太长 (MEDIUM)

**位置**: `services/auth_service.py` 第 12 行

```python
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # ❌ 24小时太长！
```

**问题**:
- 24小时内，Token 被盗后无法及时失效
- 没有 RefreshToken 的情况下，用户需要手动登录

**建议**:
```python
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # ✅ 15分钟
REFRESH_TOKEN_EXPIRE_DAYS = 7     # 刷新令牌保留7天
```

---

### 缺陷 #10: 缺少日志系统 (MEDIUM)

**位置**: 整个项目

**问题**: 几乎没有日志记录，出错时无法追踪

**修复方案**: 添加日志模块
```python
# services/logging_service.py
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def log_action(user_id: int, action: str, resource_type: str, resource_id: str, status: str, details: dict = None):
    """记录审计日志"""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "status": status,
        "details": details or {}
    }
    logger.info(json.dumps(log_entry))
```

---

### 缺陷 #11: 缺少速率限制 (MEDIUM)

**位置**: 所有端点

**问题**: 没有防暴力破解机制，可以无限制地尝试登录

**修复方案**: 使用 `slowapi` 库
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/api/v1/auth/login")
@limiter.limit("5/minute")  # ✅ 限制每分钟5次尝试
def login(body: LoginRequest, request: Request, session: Session = Depends(get_session)):
    ...
```

---

### 缺陷 #12: Member 表缺少验证约束 (MEDIUM)

**位置**: `models.py` 第 108-128 行

```python
class Member(SQLModel, table=True):
    owner_id: int = Field(foreign_key="users.id", index=True)
    birth_date: date
    gender: str  # ❌ 没有约束，可以输入任意值！
    birth_time_hour: Optional[int] = None  # ❌ 可以输入 25
    birth_time_minute: Optional[int] = None  # ❌ 可以输入 120
```

**修复方案**:
```python
from sqlalchemy import CheckConstraint

class Member(SQLModel, table=True):
    __table_args__ = (
        CheckConstraint("gender IN ('M', 'F', 'U')"),  # ✅ 限制性别值
        CheckConstraint("birth_time_hour >= 0 AND birth_time_hour < 24"),  # ✅ 小时范围
        CheckConstraint("birth_time_minute >= 0 AND birth_time_minute < 60"),  # ✅ 分钟范围
    )
    
    owner_id: int = Field(foreign_key="users.id", index=True)
    birth_date: date
    gender: str
    birth_time_hour: Optional[int] = None
    birth_time_minute: Optional[int] = None
    ...
```

---

### 缺陷 #13: 缺少输入验证 (MEDIUM)

**位置**: `routers/auth.py` 第 37-46 行

```python
class RegisterRequest(BaseModel):
    """注册请求"""
    username: str  # ❌ 没有验证长度、格式
    email: str     # ❌ 没有 EmailStr 验证
    password: str  # ❌ 没有强度要求
```

**修复方案**:
```python
from pydantic import BaseModel, EmailStr, Field, field_validator
import re

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr  # ✅ 自动验证 email 格式
    password: str = Field(..., min_length=8)
    
    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        # ✅ 检查用户名格式
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username can only contain alphanumeric, underscore, hyphen")
        return v
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        # ✅ 检查密码强度
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain digit")
        return v
```

---

### 缺陷 #14: Event 和 Scenario 的 JSON 字段缺少验证 (MEDIUM)

**位置**: `models.py` 第 121-142 行

```python
class Event(SQLModel, table=True):
    bazi_json: str  # ❌ 只是字符串，没有验证结构
    recommendation: Optional[str] = None  # ❌ 没有 schema
```

**风险**:
- 存储了无效的 JSON
- 查询时无法保证数据完整性

**修复方案**: 使用 Pydantic 验证
```python
from typing import Any
from pydantic import BaseModel, ValidationError

class BaziResult(BaseModel):
    """八字计算结果的数据模型"""
    pillars_primary: dict
    ten_gods: dict
    wuxing_score: float
    ...

# 保存时验证
try:
    bazi_obj = BaziResult(**parsed_json)
    event.bazi_json = bazi_obj.model_dump_json()
except ValidationError as e:
    raise HTTPException(status_code=400, detail="Invalid BaZi data")
```

---

### 缺陷 #15: 没有删除保护 (MEDIUM)

**位置**: 大多数 CRUD 操作

**问题**: 物理删除（DELETE）数据，无法恢复

**修复方案**: 改为逻辑删除 + 硬删除权限控制
```python
# models.py
class Member(SQLModel, table=True):
    deleted_at: Optional[datetime] = None  # ✅ 标记删除时间
    
# routers/members.py
@router.delete("/api/v1/members/{member_id}")
def delete_member(
    member_id: int,
    session: Session = Depends(get_session),
    user: TokenPayload = Depends(require_user)
):
    """逻辑删除成员"""
    member = session.exec(select(Member).where(Member.id == member_id)).first()
    
    if not member or member.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # ✅ 逻辑删除而非物理删除
    member.deleted_at = datetime.now(timezone.utc)
    session.add(member)
    session.commit()
    
    return {"message": "Member deleted"}

# 查询时过滤已删除的数据
@router.get("/api/v1/members")
def list_members(
    session: Session = Depends(get_session),
    user: TokenPayload = Depends(require_user)
):
    """列表不显示已删除的成员"""
    members = session.exec(
        select(Member)
        .where(Member.owner_id == user.user_id)
        .where(Member.deleted_at.is_(None))  # ✅ 过滤
    ).all()
    return members
```

---

### 缺陷 #16: 错误消息过于详细 (MEDIUM)

**位置**: `routers/auth.py` 和其他地方

```python
# ❌ 危险：向客户端暴露数据库错误信息
except IntegrityError as e:
    raise HTTPException(status_code=409, detail=str(e))  # 可能暴露表名、列名
```

**修复方案**:
```python
except IntegrityError as e:
    logger.error(f"Database integrity error: {str(e)}", exc_info=True)
    # ✅ 向用户返回通用错误信息
    if "unique constraint" in str(e).lower():
        raise HTTPException(status_code=409, detail="Resource already exists")
    else:
        raise HTTPException(status_code=400, detail="Invalid request data")
```

---

### 缺陷 #17: 缺少 CORS 配置 (MEDIUM)

**位置**: `run.py` 中没有 CORS 设置

**问题**: 前端应用无法跨域调用 API

**修复方案**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://example.com"],  # ✅ 配置允许的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 缺陷 #18: 缺少请求验证中间件 (MEDIUM)

**位置**: 整个应用

**问题**: 没有验证 Content-Type、请求大小等

**修复方案**:
```python
from fastapi.middleware import Middleware
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class RequestValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # ✅ 验证 Content-Type
        if request.method == "POST":
            content_type = request.headers.get("content-type", "")
            if "application/json" not in content_type:
                return Response("Invalid Content-Type", status_code=400)
        
        # ✅ 验证请求大小（防止超大上传）
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB
            return Response("Request too large", status_code=413)
        
        return await call_next(request)

app.add_middleware(RequestValidationMiddleware)
```

---

## 📋 修复优先级建议

### 第 1 优先级（立即修复，影响安全）

1. ✅ **#1** - 权限验证完全缺失
2. ✅ **#2** - 获取当前用户信息接口虚假  
3. ✅ **#3** - Delegation 表设计错误
4. ✅ **#4** - 异常处理过于宽泛
5. ✅ **#6** - RefreshToken 自动撤销缺失

### 第 2 优先级（本周修复）

6. **#5** - 认证依赖未在路由中使用
7. **#7** - 数据库全局变量非线程安全
8. **#8** - 事务完整性不足
9. **#12** - Member 表缺少验证约束
10. **#13** - 缺少输入验证

### 第 3 优先级（下周修复）

11. **#9** - JWT Token 过期时间太长
12. **#10** - 缺少日志系统
13. **#11** - 缺少速率限制
14. **#14** - JSON 字段缺少验证
15. **#15** - 没有删除保护
16. **#16** - 错误消息过于详细
17. **#17** - 缺少 CORS 配置
18. **#18** - 缺少请求验证中间件

---

## ✅ 修复完成度追踪

| 编号 | 缺陷 | 状态 | 修复时间 | 备注 |
|------|------|------|---------|------|
| #1 | 权限验证缺失 | ⬜ | - | - |
| #2 | 用户信息接口虚假 | ⬜ | - | - |
| #3 | Delegation 表设计 | ⬜ | - | - |
| #4 | 异常处理过宽 | ⬜ | - | - |
| #5 | 认证依赖未使用 | ⬜ | - | - |
| #6 | RefreshToken 撤销 | ⬜ | - | - |
| #7 | 全局变量非线程安全 | ⬜ | - | - |
| #8 | 事务完整性 | ⬜ | - | - |
| #9 | Token 过期时间 | ⬜ | - | - |
| #10 | 缺少日志系统 | ⬜ | - | - |
| #11 | 缺少速率限制 | ⬜ | - | - |
| #12 | Member 表验证 | ⬜ | - | - |
| #13 | 输入验证缺失 | ⬜ | - | - |
| #14 | JSON 验证缺失 | ⬜ | - | - |
| #15 | 删除保护缺失 | ⬜ | - | - |
| #16 | 错误信息过详 | ⬜ | - | - |
| #17 | CORS 配置缺失 | ⬜ | - | - |
| #18 | 请求验证缺失 | ⬜ | - | - |

---

## 📞 推荐下一步

1. **立即**: 选择第 1 优先级的 5 个关键缺陷进行修复
2. **本周**: 完成第 2 优先级的 5 个缺陷
3. **下周**: 逐步完成第 3 优先级的缺陷
4. **持续**: 添加自动化测试覆盖这些缺陷点

建议使用分支开发：
```bash
git checkout -b fix/critical-defects-week3
# 修复 #1-5
git commit -m "Fix: 5 critical logic defects"
git push origin fix/critical-defects-week3
```

---

**报告生成**: 2026-02-26  
**下次审计**: 建议在修复所有第 1 优先级缺陷后进行

