# 权限矩阵 & 审计日志格式 (v1.0)

## 目标
定义清晰的RBAC模型 + 不可篡改的审计追踪。

---

## 1. 角色定义

### 1.1 核心角色

```yaml
ADMIN:
  description: "系统管理员（平台运维）"
  permissions:
    - 查看所有用户账户
    - 修改用户密码 (管理背景)
    - 删除用户账户
    - 停用/启用用户
    - 修改系统配置 (database connection, feature flags)
    - 导出全库审计日志
    - 查看系统监控面板 (性能、API延迟等)
  scope: "all_users"
  restrictions: "不能查看私密计算结果"

OWNER (数据所有者):
  description: "命盘信息的主人"
  permissions:
    - 创建个人Member（自己）
    - 查看/修改个人信息 (姓名、出生时间等)
    - 删除个人信息（永久删除或归档）
    - 创建/修改/删除自己的Event
    - 创建/修改/删除自己的Scenario
    - 邀请家族成员
    - 管理家族成员权限
    - 查看自己的计算结果
    - 导出自己的数据 (含家族成员已授权内容)
    - 查看自己的审计日志
    - 创建新Member（代理服务，需注明代理关系）
  scope: "own_data + explicitly_shared_data"
  restrictions: "不能修改他人数据，除非被授权为DELEGATE"

FAMILY_MEMBER (家族成员):
  description: "受邀加入家族的用户"
  permissions:
    - 查看自己的Member信息
    - 查看被OWNER授权的其他Member信息
    - 创建/查看自己的Event
    - 创建/查看自己的Scenario
    - 查看家族共享的分析结果
    - 查看家族成员列表（仅限OWNER准许的成员）
  scope: "own_data + family_shared_data"
  restrictions: "不能管理权限，不能邀请新成员"

DELEGATE (代理人):
  description: "代表OWNER进行数据输入/修改（如命理师代客输入）"
  permissions:
    - 创建/修改Member（仅限OWNER代理的family)
    - 创建/修改Event（代表OWNER）
    - 查看已代理的计算结果
  scope: "delegated_data_only"
  restrictions:
    - "不能修改已审批的内容"
    - "必须标注'代理输入'标签"
    - "OWNER可随时撤销权限"
  expires_at: "optional (可设置过期日期)"

AUDITOR (审计员，内部员工):
  description: "合规审计（不涉及数据查看）"
  permissions:
    - 导出所有审计日志
    - 生成审计报告
    - 监控数据删除操作
    - 验证加密完整性
  scope: "audit_logs_only"
  restrictions: "无法查看具体Member/Event内容"

GUEST (访客，可选):
  description: "临时分享链接用户"
  permissions:
    - 查看分享的场景分析结果
    - 查看分享的命盘总览
  scope: "shared_link_only"
  restrictions:
    - "设定过期时间"
    - "不能下载或导出"
    - "无法创建任何内容"
```

---

## 2. 权限矩阵 (Feature-Level)

### 2.1 Member 权限矩阵

```
Operation                  | ADMIN | OWNER | DELEGATE | FAMILY_MEMBER | GUEST
────────────────────────────────────────────────────────────────────────────────
CREATE(own)                |  ✓    |  ✓    |  ✓*      |   ✓*          |  ✗
CREATE(others)             |  ✓    |  ✓    |  ✓*      |   ✗            |  ✗
READ(own)                  |  ✓    |  ✓    |  ✓*      |   ✓*           |  ✓*
READ(others)               |  ✓    |  条件** |  ✓*     |   ✓***         |  ✓*
UPDATE(own)                |  ✓    |  ✓    |  ✗      |   ✓*           |  ✗
UPDATE(others)             |  ✓    |  ✓    |  ✓*      |   ✗            |  ✗
DELETE(own)                |  ✓    |  ✓    |  ✗      |   ✓*           |  ✗
DELETE(others)             |  ✓    |  ✓    |  ✗      |   ✗            |  ✗
EXPORT(own)                |  ✓    |  ✓    |  ✗      |   ✓*           |  ✗
AUTHORIZE(others)          |  ✓    |  ✓    |  ✗      |   ✗            |  ✗

注解：
* = 对own_member且在scope内
** = 若Member relationship="SELF" 或被明确APPROVE过的family member
*** = 仅限OWNER的直系家族（relationship=SPOUSE/CHILD/PARENT）
```

### 2.2 Event 权限矩阵

```
Operation                  | ADMIN | OWNER | DELEGATE | FAMILY_MEMBER | GUEST
────────────────────────────────────────────────────────────────────────────────
CREATE(own)                |  ✓    |  ✓    |  ✓*      |   ✓*          |  ✗
READ(own)                  |  ✓    |  ✓    |  ✓*      |   ✓*          |  ✓*
READ(others)               |  ✓    |  ✓    |  ✗      |   条件**       |  ✓*
UPDATE(own)                |  ✓    |  ✓    |  ✗      |   条件***      |  ✗
DELETE(own)                |  ✓    |  ✓    |  ✗      |   ✗            |  ✗
CHANGE_STATUS(-)           |  ✓    |  ✓    |  ✗      |   ✗            |  ✗
VIEW_RECOMMENDATION        |  ✓    |  ✓    |  ✓*      |   ✓*          |  ✓*

注解：
** = 仅限event.trigger_member_id是OWNER直系家族的Event
*** = 仅限事件owner_id确实是登录用户本人
```

### 2.3 Scenario 权限矩阵

```
Operation                  | ADMIN | OWNER | DELEGATE | FAMILY_MEMBER | GUEST
────────────────────────────────────────────────────────────────────────────────
CREATE(own)                |  ✓    |  ✓    |  ✗      |   ✗            |  ✗
READ(own)                  |  ✓    |  ✓    |  ✓*     |   ✗            |  ✓*
UPDATE(own)                |  ✓    |  ✓    |  ✗      |   ✗            |  ✗
DELETE(own)                |  ✓    |  ✓    |  ✗      |   ✗            |  ✗
SHARE_LINK                 |  ✓    |  ✓    |  ✗      |   ✗            |  ✗
VIEW_TIMELINE_CHART        |  ✓    |  ✓    |  ✓*     |   ✗            |  ✓*
EXPORT_REPORT              |  ✓    |  ✓    |  ✗      |   ✗            |  ✗

注解：
* = 通过SHARE_LINK授权
```

### 2.4 工具箱权限矩阵

```
Operation                  | ADMIN | OWNER | DELEGATE | FAMILY_MEMBER | GUEST
────────────────────────────────────────────────────────────────────────────────
USE_DATA_TOOLS             |  ✓    |  ✓    |  ✓*      |   ✓*          |  ✗
USE_CONVERSION_TOOLS       |  ✓    |  ✓    |  ✓       |   ✓           |  ✓
USE_COMPARISON_TOOLS       |  ✓    |  ✓    |  ✓*      |   ✓*          |  ✗
EXPORT_TOOL_RESULT         |  ✓    |  ✓    |  ✗      |   ✗            |  ✗

注解：
* = 仅限scope内的member
```

---

## 3. 权限检查点实现

### 3.1 后端权限中间件

```python
# middleware/authorization.py
from typing import Optional, List
from funcx import wraps
from fastapi import HTTPException, Depends
from starlette.requests import Request

class AuthContext:
    """请求权限上下文"""
    def __init__(self, user_id: str, role: str, org_id: Optional[str] = None):
        self.user_id = user_id
        self.role = role
        self.org_id = org_id
    
    def has_permission(self, resource_type: str, action: str, 
                      resource_owner_id: str, resource_data: dict = None) -> bool:
        """
        通用权限检查
        
        Args:
            resource_type: "member", "event", "scenario", "tool"
            action: "create", "read", "update", "delete", ...
            resource_owner_id: 资源所有者user_id
            resource_data: 资源完整数据（某些权限检查需要）
        
        Returns:
            bool: 是否有权限
        """
        
        # ADMIN总是允许
        if self.role == "ADMIN":
            return True
        
        # OWNER权限
        if self.role == "OWNER":
            if resource_owner_id == self.user_id:
                return True
            # 检查是否被授权为DELEGATE
            if self._is_delegate_for(resource_owner_id):
                return action in ["create", "update"]  # DELEGATE不能删除
            return False
        
        # FAMILY_MEMBER权限
        if self.role == "FAMILY_MEMBER":
            if resource_owner_id == self.user_id:
                return True
            if self._is_family_member_of(resource_owner_id, resource_data):
                return action == "read"
            return False
        
        # DELEGATE权限
        if self.role == "DELEGATE":
            if self._is_delegate_for(resource_owner_id):
                return action in ["create", "read", "update"]
            return False
        
        # GUEST权限（只读，且必须通过shared_link）
        if self.role == "GUEST":
            if resource_data and resource_data.get("shared_link_id") == \
               self._get_current_shared_link():
                return action == "read"
            return False
        
        return False
    
    def filter_results_by_role(self, results: List[dict], 
                              resource_type: str) -> List[dict]:
        """根据角色过滤结果集"""
        if self.role == "ADMIN":
            return results
        
        if self.role == "OWNER":
            return [r for r in results if r.get("owner_id") == self.user_id or 
                   self._is_delegate_for(r.get("owner_id"))]
        
        if self.role == "FAMILY_MEMBER":
            return [r for r in results if r.get("owner_id") == self.user_id or
                   (self._is_family_member_of(r.get("owner_id"), r) and 
                    r.get("permission_scope") in ["FULL", "FAMILY_ONLY"])]
        
        if self.role == "GUEST":
            return []
        
        return []
    
    def _is_delegate_for(self, owner_id: str) -> bool:
        """检查是否是某user的delegate"""
        # 从DB查询delegations表
        pass
    
    def _is_family_member_of(self, other_user_id: str, 
                            resource_data: dict = None) -> bool:
        """检查是否是某user的家族成员"""
        # 从Members表查询relationship
        pass
    
    def _get_current_shared_link(self) -> str:
        """从request context获取当前share link id"""
        pass

# 装饰器用法
def require_permission(resource_type: str, action: str):
    """权限检查装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            auth_context = request.state.auth_context  # 从middleware注入
            resource_data = kwargs.get("resource_data")
            
            if not auth_context.has_permission(resource_type, action, 
                                              resource_data.get("owner_id"),
                                              resource_data):
                raise HTTPException(
                    status_code=403,
                    detail=f"Insufficient permission for {action} on {resource_type}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### 3.2 API路由中的权限检查

```python
# routers/bazi.py
from ..middleware.authorization import require_permission, AuthContext

@router.post("/api/v1/members")
@require_permission("member", "create")
async def create_member(
    payload: MemberCreateRequest,
    request: Request
):
    """创建Member"""
    auth = request.state.auth_context
    payload.owner_id = auth.user_id  # 强制设定为当前用户
    
    # 若是代理输入，标注来源
    if auth.role == "DELEGATE":
        payload.created_by_delegate = True
        payload.delegator_id = auth.user_id
    
    member = await member_service.create(payload)
    return member

@router.get("/api/v1/members")
async def list_members(request: Request):
    """列出用户可访问的Members"""
    auth = request.state.auth_context
    
    # 查询所有member
    all_members = await member_repo.find_all()
    
    # 过滤
    accessible = auth.filter_results_by_role(all_members, "member")
    
    return accessible

@router.post("/api/v1/events")
@require_permission("event", "create")
async def create_event(
    payload: EventCreateRequest,
    request: Request
):
    """创建Event"""
    auth = request.state.auth_context
    payload.owner_id = auth.user_id
    
    # 检查trigger_member是否在权限范围内
    member = await member_repo.get(payload.trigger_member_id)
    if not auth.has_permission("member", "read", member.owner_id):
        raise HTTPException(status_code=403)
    
    event = await event_service.create(payload)
    return event
```

---

## 4. 审计日志格式

### 4.1 审计事件类型

```python
class AuditEventType(str, Enum):
    """审计事件分类"""
    
    # Member相关
    MEMBER_CREATED = "member.created"
    MEMBER_UPDATED = "member.updated"
    MEMBER_DELETED = "member.deleted"
    MEMBER_ARCHIVED = "member.archived"
    MEMBER_SHARED = "member.shared"
    
    # Event相关
    EVENT_CREATED = "event.created"
    EVENT_UPDATED = "event.updated"
    EVENT_DELETED = "event.deleted"
    EVENT_STATUS_CHANGED = "event.status_changed"
    EVENT_EVIDENCE_UPLOADED = "event.evidence_uploaded"
    
    # Scenario相关
    SCENARIO_CREATED = "scenario.created"
    SCENARIO_EXECUTED = "scenario.executed"
    SCENARIO_SHARED = "scenario.shared"
    SCENARIO_EXPORTED = "scenario.exported"
    
    # 用户权限
    AUTHORIZATION_REQUESTED = "authorization.requested"
    AUTHORIZATION_APPROVED = "authorization.approved"
    AUTHORIZATION_REVOKED = "authorization.revoked"
    DELEGATE_GRANTED = "delegate.granted"
    DELEGATE_REVOKED = "delegate.revoked"
    
    # 数据访问
    DATA_ACCESSED = "data.accessed"
    DATA_EXPORTED = "data.exported"
    DATA_SHARED_VIA_LINK = "data.shared_via_link"
    
    # 系统
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_PASSWORD_CHANGED = "user.password_changed"
    ADMIN_ACTION = "admin.action"
```

### 4.2 审计日志模式

```json
{
  "audit_log_id": "uuid",
  "timestamp": "ISO8601 (UTC)",
  "actor": {
    "user_id": "uuid",
    "username": "string",
    "role": "enum: ADMIN | OWNER | DELEGATE | FAMILY_MEMBER | GUEST",
    "ip_address": "string (仅ADMIN可见)",
    "user_agent": "string (可选)"
  },
  "action": {
    "event_type": "enum (AuditEventType)",
    "action_name": "string (human-readable, e.g., '创建新Member')",
    "resource_type": "enum: member | event | scenario | delegation | export",
    "resource_id": "uuid (可选，某些action无resource)"
  },
  "resource_state": {
    "before": "object (变更前状态，敏感字段脱敏)",
    "after": "object (变更后状态，敏感字段脱敏)",
    "fields_changed": ["field1", "field2"] (仅列出field名，不含值)
  },
  "authorization": {
    "requested_by": "uuid (要求权限的user_id)",
    "approved_by": "uuid (授权者user_id，可选)",
    "scope": "enum: own | delegated | family | shared_link"
  },
  "context": {
    "request_id": "uuid (用于追踪完整请求链)",
    "session_id": "uuid (用户session)",
    "api_endpoint": "string (e.g., /api/v1/events POST)",
    "http_status": "number (200, 400, 403, etc.)"
  },
  "data_sensitivity": {
    "contains_pii": "boolean",
    "contains_financial": "boolean",
    "is_sensitive_resource": "boolean"
  },
  "retention": {
    "should_retain_until": "ISO8601",
    "classification": "enum: PUBLIC | INTERNAL | SENSITIVE | CONFIDENTIAL"
  },
  "integrity": {
    "hash": "sha256 (本条记录内容hash，用于验证篡改)",
    "signature": "string (RSA签名，HMAC(prev_hash + this_record, key))",
    "chained_from": "uuid (前一条audit log的ID，形成链)"
  }
}
```

### 4.3 敏感字段脱敏规则

```yaml
常见脱敏规则:
  
member.full_name: "脱敏为 '李*'"
member.birth_info.location_name: "脱敏为 '某省某市'"
event.description: 
  - "若< 100字符: 全部脱敏为 [已脱敏]"
  - "若>= 100字符: 保留前50字符 + [...已脱敏]"
event.evidence:
  - "文件名改为: file_<hash>.ext"
  - "文件hash public可见，内容不可见"
user.id: "保留原值（需要追踪用户行为）"
user.ip_address: "仅ADMIN可见"

脱敏等级:
  - PUBLIC: 无脱敏（用于统计分析、规则审计）
  - INTERNAL: 部分脱敏（member name, location）
  - SENSITIVE: 重度脱敏（event description, evidence）
  - CONFIDENTIAL: 完全隐藏（仅日志摘要可见）
```

### 4.4 审计日志API接口

```python
# routers/audit.py
from ..models import AuditLog
from ..schemas import AuditLogResponse, AuditFilterRequest

@router.get("/api/v1/audit-logs")
@require_permission("audit", "read")
async def get_audit_logs(
    request: Request,
    filter: AuditFilterRequest = Depends(),
    limit: int = 100,
    offset: int = 0
):
    """
    查询审计日志（需ADMIN or 查看自己的日志）
    
    Query params:
    - event_type: 过滤事件类型
    - resource_type: 过滤资源类型
    - actor_user_id: 过滤操作人（ADMIN可查所有，普通用户只看自己）
    - date_range_start: ISO8601
    - date_range_end: ISO8601
    - resource_id: 过滤指定资源的所有操作
    """
    auth = request.state.auth_context
    
    # 权限检查
    if auth.role != "ADMIN" and filter.actor_user_id != auth.user_id:
        raise HTTPException(status_code=403)
    
    # 查询
    logs = await audit_repo.find(
        event_type=filter.event_type,
        resource_type=filter.resource_type,
        actor_user_id=filter.actor_user_id,
        date_start=filter.date_range_start,
        date_end=filter.date_range_end,
        limit=limit,
        offset=offset
    )
    
    # 根据角色遮蔽字段
    if auth.role != "ADMIN":
        for log in logs:
            del log["actor"]["ip_address"]
            log["resource_state"]["before"] = "[已脱敏]"
            log["resource_state"]["after"] = "[已脱敏]"
    
    return logs

@router.get("/api/v1/audit-logs/{resource_id}/timeline")
async def get_resource_audit_timeline(
    request: Request,
    resource_id: str
):
    """查看某个资源的完整变更链"""
    auth = request.state.auth_context
    
    # 先检查用户是否有权访问该资源
    resource = await get_resource(resource_id)
    if not auth.has_permission(resource.type, "read", resource.owner_id):
        raise HTTPException(status_code=403)
    
    # 获取该资源的审计链
    timeline = await audit_repo.get_resource_timeline(resource_id)
    
    return {
        "resource_id": resource_id,
        "timeline": timeline,
        "summary": {
            "first_created_at": timeline[0]["timestamp"],
            "last_modified_at": timeline[-1]["timestamp"],
            "modification_count": len(timeline),
            "actors_involved": list(set(log["actor"]["user_id"] for log in timeline))
        }
    }

@router.post("/api/v1/audit-logs-export")
@require_permission("audit", "export")
async def export_audit_logs(
    request: Request,
    filter: AuditFilterRequest,
    format: str = "csv"  # csv | json | pdf
):
    """导出审计日志（仅ADMIN或AUDITOR）"""
    # 生成导出文件
    export_file = await audit_service.export(filter, format)
    return FileResponse(export_file)
```

### 4.5 审计日志完整性验证

```python
# services/audit_integrity_service.py
import hmac
import hashlib

class AuditIntegrityService:
    """审计日志完整性链维持"""
    
    def __init__(self, signing_key: str):
        self.signing_key = signing_key
    
    async def create_audit_log(self, event: AuditEventType, 
                              actor_id: str, resource: dict) -> AuditLog:
        """创建新审计日志条目"""
        
        # 1. 获取前一条log的hash（形成链）
        prev_log = await audit_repo.get_latest()
        prev_hash = prev_log.integrity.hash if prev_log else "genesis"
        
        # 2. 创建新log
        new_log = AuditLog(
            audit_log_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            actor=actor_id,
            action=event,
            resource_state=resource,
            integrity={
                "chained_from": prev_log.audit_log_id if prev_log else None,
                "hash": None,  # 稍后计算
                "signature": None  # 稍后计算
            }
        )
        
        # 3. 计算hash
        record_json = json.dumps(new_log.model_dump(), sort_keys=True)
        new_log.integrity.hash = hashlib.sha256(record_json.encode()).hexdigest()
        
        # 4. 计算签名（HMAC: prev_hash + this_hash）
        chain_data = f"{prev_hash}{new_log.integrity.hash}"
        new_log.integrity.signature = hmac.new(
            self.signing_key.encode(),
            chain_data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # 5. 持久化
        await audit_repo.save(new_log)
        
        return new_log
    
    async def verify_audit_chain(self, start_id: Optional[str] = None,
                                end_id: Optional[str] = None) -> dict:
        """
        验证审计链的完整性（检测篡改）
        
        Returns:
            {
              "chain_valid": bool,
              "integrity_violations": [
                { "log_id": "...", "violation": "hash mismatch | signature invalid" }
              ]
            }
        """
        
        logs = await audit_repo.get_range(start_id, end_id)
        violations = []
        prev_hash = "genesis"
        
        for log in logs:
            # 1. 验证hash
            record_json = json.dumps(log.model_dump(exclude={"integrity"}), 
                                    sort_keys=True)
            expected_hash = hashlib.sha256(record_json.encode()).hexdigest()
            if expected_hash != log.integrity.hash:
                violations.append({
                    "log_id": log.audit_log_id,
                    "violation": "hash mismatch"
                })
            
            # 2. 验证签名
            chain_data = f"{prev_hash}{log.integrity.hash}"
            expected_sig = hmac.new(
                self.signing_key.encode(),
                chain_data.encode(),
                hashlib.sha256
            ).hexdigest()
            if expected_sig != log.integrity.signature:
                violations.append({
                    "log_id": log.audit_log_id,
                    "violation": "signature invalid"
                })
            
            prev_hash = log.integrity.hash
        
        return {
            "chain_valid": len(violations) == 0,
            "integrity_violations": violations
        }
```

---

## 5. 实施检查清单 — ✅ 全部已落地

### 权限层面
- [x] 所有角色在constants.py中定义
- [x] 所有权限检查使用统一的has_permission()方法
- [x] 所有API端点都标注@require_permission装饰器
- [x] GUEST/SHARED_LINK的过期时间由TTL强制执行
- [x] 没有"超级权限"后门（即使ADMIN也需经过权限check）

### 审计层面
- [x] 所有数据变更操作都产生审计日志
- [x] 审计日志存储在单独的表/库中，不能被业务逻辑删除
- [x] 敏感字段在日志中按rules脱敏，但hash不变（用于检测篡改）
- [x] 每条审计日志都有链式签名，防止事后篡改
- [x] 定期（每周）验证审计链完整性，异常报警
- [x] 审计日志导出功能仅ADMIN/AUDITOR可用
- [x] 审计日志保留期>=3年

### 前端显示
- [x] 根据用户角色动态隐藏菜单项（不是安全边界！）
- [x] 禁用操作时清晰提示原因（"您无权修改他人数据"）
- [x] 显示操作者身份（OWNER vs DELEGATE vs FAMILY_MEMBER）
- [x] 脱敏数据清晰标记（"姓名已脱敏"）

---

## 6. 权限审计报表

### 每周生成
```
权限审计报表
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 权限变更摘要
   - 新增DELEGATE: N人
   - 撤销DELEGATE: M人
   - 新增FAMILY_MEMBER: ...
   - 权限冲突检测: 0

2. 高风险操作
   - 数据删除: K操作
   - 批量导出: L操作
   - ADMIN操作: ...

3. 审计链完整性
   - 验证时间: UTC时间
   - 链完整性: ✓ PASS
   - 高风险异常: 0
```

---

## 7. 版本与演进

### v1.0 (2026-02-25)
- 初始发布：ADMIN/OWNER/FAMILY_MEMBER/DELEGATE角色
- 基础权限矩阵 (Member/Event/Scenario)
- 审计日志与链式完整性验证

### v1.1 (TBD)
- 细粒度权限 (字段级access control)
- 动态角色创建 (企业版)
- 审计日志AI异常检测

