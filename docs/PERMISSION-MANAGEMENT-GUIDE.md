# 权限管理最佳实践指南

## 📚 概念基础

### 权限三角形

```
    用户(User)
    /        \
 权限 ---- 资源
(Permission) (Resource)
```

- **用户**: 系统中的账户
- **权限**: 可执行的操作
- **资源**: 操作的对象

### 权限模型演化

| 阶段 | 模型 | 特点 | 应用 |
|------|------|------|------|
| v1 | 硬编码权限 | 权限在代码中 | 小项目 ❌ |
| v2 | ACL列表 | 直接分配权限 | 中等项目 ⚠️ |
| v3 | **RBAC** | 角色归类权限 | **本项目** ✅ |
| v4+ | ABAC | 属性决定权限 | 大企业 |

---

## 🎯 RBAC系统详解

### 我们的4个角色

```
权限数量: OWNER(18) > EDITOR(10) > VIEWER(3) > GUEST(1)

OWNER
├─ 成员管理: CREATE, READ, UPDATE, DELETE ✓
├─ 事件管理: CREATE, READ, UPDATE, DELETE ✓
├─ 场景管理: CREATE, READ, UPDATE, DELETE ✓
├─ 权限委托: DELEGATE, REVOKE ✓
├─ 系统管理: MANAGE_USERS, VIEW_AUDIT ✓
└─ 审计权限: VIEW_AUDIT_LOG ✓

EDITOR
├─ 成员管理: READ, UPDATE ✓
├─ 事件管理: CREATE, READ, UPDATE, DELETE ✓
├─ 场景管理: CREATE, READ, UPDATE, DELETE ✓
├─ 权限委托: ❌ (无权委托)
├─ 系统管理: ❌
└─ 审计权限: ❌

VIEWER
├─ 成员管理: READ ✓
├─ 事件管理: READ ✓
├─ 场景管理: READ ✓
└─ 其他: ❌ (全部无权)

GUEST
├─ 成员管理: READ ✓ (仅自己的)
└─ 其他: ❌
```

---

## 🔐 权限委托系统

### 委托流程

```
Step 1: 权限持有者 (OWNER)
         ├─ 检查: 我有这个权限吗?
         └─ 结果: ✓ 有权限

Step 2: 权限提升防御
         ├─ 检查: 接收者的角色等级?
         ├─ 检查: 是否有循环委托?
         └─ 结果: ✓ 通过检查

Step 3: 链深度验证
         ├─ 当前深度: A→B (1级)
         ├─ 最大深度: 3级
         └─ 结果: ✓ 未超上限

Step 4: 创建委托
         ├─ 设置过期时间: +30天
         ├─ 记录审计日志
         └─ 结果: ✅ 委托成功
```

### 委托权限验证示例

```python
# 场景: OWNER想委托CREATE_MEMBER给EDITOR

from services.delegation_service import create_delegation

create_delegation(
    session=db_session,
    from_user_id=1,       # OWNER
    to_user_id=2,         # EDITOR
    permission_type="create_member",
    member_scope=None,    # 不限制特定成员
    expires_days=30,
    audit_user_id=1       # 操作日志
)

# 内部检查流程:
# 1. OWNER有CREATE_MEMBER吗? ✅ YES (角色权限)
# 2. EDITOR是已活跃用户吗? ✅ YES
# 3. 有循环委托吗? ✅ NO
# 4. 链深度 ≤ 3? ✅ YES
# ➜ 委托创建成功，记录审计日志
```

### 防止权限提升攻击

```python
# ❌ 攻击尝试 1: EDITOR尝试委托DELETE_MEMBER

create_delegation(
    from_user_id=2,           # EDITOR
    to_user_id=3,             # 另一个用户
    permission_type="delete_member"  # ❌ EDITOR没有这个权限
)
# 结果: ❌ PermissionDelegationError
#        "Cannot delegate permission: DELETE_MEMBER"

# ❌ 攻击尝试 2: 循环委托A→B→A

# 假设已存在: EDITOR(2) ← OWNER(1)
create_delegation(
    from_user_id=2,
    to_user_id=1,             # ❌ 尝试循环回去
    permission_type="create_member"
)
# 结果: ❌ PermissionCascadeError
#        "Circular delegation detected"

# ❌ 攻击尝试 3: 超过链深度限制

# A→B→C→D 链 (4级, 超过最大3级)
# 结果: ❌ PermissionCascadeError
#        "Permission chain too deep (max: 3 levels)"
```

---

## 💡 实战场景

### 场景1: 小团队成员间共享权限

**背景**: 3个成员的非营利组织，需要灵活分享权限

```python
# 初始状态:
# 创建者(user_id=1): OWNER
# 志愿者A(user_id=2): VIEWER
# 志愿者B(user_id=3): GUEST

# 需求: 允许志愿者A创建成员信息

# 解决方案: 委托CREATE_MEMBER权限
create_delegation(
    from_user_id=1,       # 创建者(OWNER)
    to_user_id=2,         # 志愿者A
    permission_type="create_member",
    expires_days=90       # 3个月的临时权限
)

# 结果: 志愿者A现在可以创建成员
# 3个月后自动失效，无需手动撤销
```

### 场景2: 假期权限移交

**背景**: 项目经理休假，需要移交权限

```python
# 场景:
# 项目经理 (user_id=10): OWNER
# 代理人 (user_id=11): EDITOR
# 项目经理即将休假

# 解决方案A: 委托所有管理权限
permissions_to_delegate = [
    "create_member",
    "update_member",
    "delete_member",
    "create_event",
    "update_event",
    "delete_event",
]

for perm in permissions_to_delegate:
    create_delegation(
        from_user_id=10,
        to_user_id=11,
        permission_type=perm,
        expires_days=14      # 两周 (假期期间)
    )

# 解决方案B: 委托时指定成员范围
# 只允许代理人处理特定客户的数据

create_delegation(
    from_user_id=10,
    to_user_id=11,
    permission_type="create_event",
    member_scope=5,         # 仅限客户ID=5的成员
    expires_days=14
)

# 14天后自动失效，增强安全性
```

### 场景3: 审计合规性

**背景**: 需要验证权限使用历史

```python
# 查询所有权限委托
delegations = session.exec(
    select(Delegation)
    .where(Delegation.from_member_id == 1)
    .where(Delegation.created_at >= audit_start_date)
).all()

# 检查每个委托的审计日志
for delegation in delegations:
    logs = session.exec(
        select(AuditLog)
        .where(AuditLog.resource_type == "delegation")
        .where(AuditLog.resource_id == str(delegation.id))
    ).all()
    
    # 验证委托是否被使用
    for log in logs:
        print(f"委托ID {delegation.id}: {log.action} 于 {log.created_at}")

# 验证完整性
issues = verify_delegations_integrity(session)
if issues:
    print("发现问题:")
    for issue in issues:
        print(f"  - {issue}")
```

---

## 🛡️ 安全最佳实践

### 1. 最小权限原则

```python
# ❌ 不要这样做
# 给新用户OWNER角色 (权力过大)
new_user.role = Role.OWNER

# ✅ 这样做
# 先给VIEWER角色，按需委托权限
new_user.role = Role.VIEWER

# 只委托需要的特定权限
create_delegation(
    from_user_id=admin,
    to_user_id=new_user_id,
    permission_type="create_event",  # 仅这一个权限
    expires_days=30
)
```

### 2. 定期权限审计

```python
# 每月审计: 检查过期但未撤销的委托
from datetime import datetime, timedelta, timezone

now = datetime.now(timezone.utc)
expired_delegations = session.exec(
    select(Delegation)
    .where(Delegation.expires_at < now)
    .where(Delegation.is_active == True)
).all()

# 自动撤销过期委托
for delegation in expired_delegations:
    revoke_delegation(session, delegation.id, audit_user_id=admin_id)
    print(f"已自动撤销过期委托 ID {delegation.id}")
```

### 3. 监控权限滥用

```python
# 检查异常权限使用
# 例: VIEWER用户提升为DELETE权限

viewer = session.exec(select(User).where(User.id == viewer_id)).first()
viewer_perms = get_user_effective_permissions(session, viewer_id)

# DELETE权限不应该出现在VIEWER的权限中
if Permission.DELETE_MEMBER in viewer_perms:
    alert("危险: VIEWER用户拥有DELETE权限!")
    # 立即撤销
```

### 4. 权限委托审批流程

```python
# 在关键操作前要求审批

def create_delegation_with_approval(
    from_user_id: int,
    to_user_id: int,
    permission: str,
    approver_id: int
):
    # Step 1: 检查批准者权限
    approver = session.exec(
        select(User).where(User.id == approver_id)
    ).first()
    
    if approver.role != Role.OWNER:
        raise PermissionError("仅OWNER可批准委托")
    
    # Step 2: 创建审计记录
    audit_log = AuditLog(
        user_id=from_user_id,
        action="delegation_requested",
        resource_type="delegation",
        details={
            "to_user": to_user_id,
            "permission": permission,
            "approver": approver_id,
            "status": "pending"
        }
    )
    
    # Step 3: 发送通知(可选)
    send_approval_notification(approver_id, details)
    
    # Step 4: 创建委托(如果批准)
    if approver_confirms():
        delegation = create_delegation(...)
```

---

## 📊 权限设计模式

### 模式1: 基于时间的权限

```python
# 临时权限: 仅在特定时间有效

create_delegation(
    from_user_id=owner_id,
    to_user_id=contractor_id,
    permission_type="read_member",
    expires_days=7,           # 一周后失效
    member_scope=project_id   # 仅限项目范围
)

# 优势:
# - 自动过期，无需手动撤销
# - 防止权限泄露
# - 审计追踪完整
```

### 模式2: 基于角色的动态权限

```python
# RBAC增强: 动态调整权限

def adjust_role_for_event(user_id: int, event_type: str):
    """根据事件类型动态调整权限"""
    
    if event_type == "critical":
        # 关键事件: 升级为更高权限
        role = Role.EDITOR  # 临时升级
    else:
        # 普通事件: 保持角色
        role = user.role
    
    return get_user_effective_permissions(
        session, 
        user_id,
        member_id=event.member_id
    )
```

### 模式3: 作用域限制权限

```python
# 权限可以限制在特定成员/资源

# 场景: 允许用户A编辑客户B的成员信息
# (但不能编辑其他客户)

create_delegation(
    from_user_id=owner,
    to_user_id=user_a,
    permission_type="update_member",
    member_scope=customer_b_id   # 关键: 限制范围
)

# 检查权限时会验证范围
if can_update_member(user_id, member_id):
    # 不仅检查权限，还检查member_scope匹配
    ...
```

---

## ⚠️ 常见错误与修正

### 错误1: 忘记检查权限

```python
# ❌ 错误
@router.delete("/members/{member_id}")
def delete_member(member_id: int):
    # 直接删除，没有权限检查!
    session.delete(member)
    return 204

# ✅ 正确
@router.delete("/members/{member_id}")
def delete_member(
    member_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # Step 1: 检查权限
    user_perms = get_user_effective_permissions(
        session,
        current_user.id,
        member_scope=member_id
    )
    
    if Permission.DELETE_MEMBER not in user_perms:
        raise HTTPException(status_code=403, detail="No permission")
    
    # Step 2: 检查所有权 (可选)
    if member.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your member")
    
    # Step 3: 操作并审计
    session.delete(member)
    log_action(session, current_user.id, "delete_member", "member", str(member_id))
    
    return 204
```

### 错误2: 权限检查在错误的层

```python
# ❌ 错误 (权限检查在业务逻辑中)
def process_event(user_id, event_id):
    if not has_permission(user_id, "READ_EVENT"):  # 太晚
        # 此时已经查询数据库了
        raise PermissionError
    ...

# ✅ 正确 (权限检查在入口)
@router.get("/events/{event_id}")
def get_event(
    event_id: int,
    current_user: User = Depends(get_current_user),  # 这里检查认证
    session: Session = Depends(get_session),
):
    # 权限检查在最开头
    if not has_permission(current_user.role, Permission.READ_EVENT):
        raise HTTPException(status_code=403)
    
    # 然后才进行业务逻辑
    event = session.get(Event, event_id)
    ...
```

### 错误3: 忽视审计日志

```python
# ❌ 错误
create_delegation(from_user_id, to_user_id, perm)
# 没有审计日志记录

# ✅ 正确
create_delegation(
    from_user_id,
    to_user_id,
    perm,
    audit_user_id=admin_id  # 传入审计信息
)
# 函数内部自动记录日志
```

---

## 📈 权限系统升级路线

### 当前阶段 (v1) ✅
```
RBAC + 权限委托 + 级联验证
- 4个角色
- 18个权限
- 权限链 max 3深度
```

### 下一版本计划 (v2)
```
增强功能:
- 权限申请工作流 (申请→审批→授予)
- 时间表权限 (定时启用/禁用)
- 权限模板 (预定义权限组)
```

### 未来版本 (v3+)
```
高级功能:
- ABAC (Attribute-Based Access Control)
- 动态权限 (基于条件)
- 权限推荐引擎 (AI驱动)
```

---

## 📞 问题排查

### Q: 权限委托后用户仍无权限?

**排查步骤:**
```python
# 1. 检查委托是否生效
delegation = session.exec(
    select(Delegation)
    .where(Delegation.to_member_id == user_id)
).first()
assert delegation, "委托不存在"
assert delegation.is_active, "委托已被撤销"

# 2. 检查过期时间
assert datetime.now() < delegation.expires_at, "委托已过期"

# 3. 重新检查有效权限
perms = get_user_effective_permissions(session, user_id)
print(f"有效权限: {perms}")

# 4. 检查缓存 (如果有缓存).clear_cache(user_id)
```

### Q: 如何临时快速撤销所有权限?

```python
# 撤销某用户的所有活跃委托

delegations = session.exec(
    select(Delegation)
    .where(Delegation.to_member_id == user_id)
    .where(Delegation.is_active == True)
).all()

for delegation in delegations:
    revoke_delegation(session, delegation.id, audit_user_id=admin_id)
```

### Q: 权限级联防护是否会导致功能受限?

**答**: 不会。防护仅阻止不安全操作:
- ✅ 允许: 用户委托自己拥有的权限
- ❌ 阻止: 用户委托自己没有的权限
- ❌ 阻止: 循环委托 (A→B→A)
- ❌ 阻止: 超过3级深度

这些限制提高安全性，不影响合法用途。

---

## 📚 参考资源

| 资源 | 位置 | 用途 |
|------|------|------|
| API文档 | docs/COMPLETE-API-DOCUMENTATION.md | 端点使用 |
| 部署指南 | docs/DEPLOYMENT-GUIDE.md | 生产部署 |
| 源代码 | services/permission_cascade_service.py | 实现细节 |
| 单元测试 | tests/test_cascade_validation.py | 使用示例 |

---

**版本**: v1.0  
**最后更新**: 2026年2月25日  
**作者**: Development Team

✅ **本指南涵盖了权限管理的各个方面，从基础概念到高级实战。建议开发人员在实现权限相关功能时参考本指南。**
