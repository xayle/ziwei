# 🎯 缺陷修复执行计划

**生成日期**: 2026-02-26  
**执行目标**: Week 3 底层逻辑修复  
**修复周期**: 3天 (8小时/天)

---

## 📅 修复时间表

### 第 1 天 (2026-02-26 下午) - 第 1 优先级 (3.25小时)

**目标**: 修复所有关键段，使应用可安全上线

| 时间 | 任务 | 文件 | 工作量 |
|------|------|------|--------|
| 14:00-14:30 | #1 权限检查缺失 | `run.py`, `routers/*` | 30分钟 |
| 14:30-14:50 | #2 /auth/me 虚假 | `routers/auth.py` | 20分钟 |
| 14:50-15:35 | #3 Delegation 表 | `models.py`, `routers/delegation.py` | 45分钟 |
| 15:35-16:35 | #4 异常处理改进 | `run.py`, `services/auth_service.py` | 60分钟 |
| 16:35-17:15 | #5 RefreshToken 撤销 | `routers/auth.py`, `services/auth_service.py` | 40分钟 |
| 17:15-17:45 | 全量测试 | `pytest`, smoke tests | 30分钟 |

---

## 🔴 关键缺陷修复详情

### 缺陷 #1: 权限验证完全缺失

**状态**: ⬜ 未开始  
**文件**:
- `run.py` - 添加全局权限检查
- `routers/members.py` - 添加 `require_user` 依赖
- `routers/events.py` - 添加 `require_user` 依赖
- `routers/scenarios.py` - 添加 `require_user` 依赖
- `routers/delegation.py` - 添加 `require_user` 依赖
- `routers/audit.py` - 添加 `require_user` 依赖

**修复步骤**:
1. ✅ 在 `run.py` 中声明 `require_user` 函数（已存在）
2. ✅ 在所有需要认证的 endpoint 中添加 `user: TokenPayload = Depends(require_user)`
3. ✅ 添加权限检查逻辑（使用 `permission_cascade_service`）

**预期结果**: 无效 Token 会返回 401，无权限会返回 403

---

### 缺陷 #2: /auth/me 接口虚假

**状态**: ⬜ 未开始  
**文件**: `routers/auth.py`

**现状**:
```python
@router.get("/auth/me")
def get_current_user_info(token: str | None = None):
    return {"message": "用户信息获取需要通过require_user依赖", ...}
```

**修复后**:
```python
@router.get("/api/v1/auth/me")
def get_current_user_info(
    session: Session = Depends(get_session),
    user: TokenPayload = Depends(require_user)
):
    # 返回实际用户信息
```

**预期结果**: 返回真实用户数据 (user_id, username, email, role, etc.)

---

### 缺陷 #3: Delegation 表设计错误

**状态**: ⬜ 未开始  
**文件**: `models.py`, `routers/delegation.py` (可选)

**现状问题**:
- 字段名: `from_member_id`, `to_member_id` (暗示成员)
- 外键: 指向 `users` 表 (实际是用户)
- 无约束: 无法防止自委托 (A → A)

**修复内容**:
1. 重命名字段: `from_member_id` → `from_user_id`, `to_member_id` → `to_user_id`
2. 添加约束: `from_user_id != to_user_id`
3. 更新表备注

**预期结果**: 表结构清晰，无语义混乱

---

### 缺陷 #4: 异常处理过于宽泛

**状态**: ⬜ 未开始  
**文件**: `run.py` (verify endpoint), `services/auth_service.py`

**现状问题**:
```python
except Exception as exc:
    raise HTTPException(status_code=500, detail=str(exc))
```

**修复内容**:
1. 添加日志记录（使用 logging 模块）
2. 分类捕获异常（ValueError, IntegrityError, 等）
3. 隐藏敏感信息，返回通用错误消息

**预期结果**: 生产问题可追踪，用户不会看到内部细节

---

### 缺陷 #5: RefreshToken 自动撤销缺失

**状态**: ⬜ 未开始  
**文件**: `routers/auth.py`

**修复内容**:
1. 添加 `/auth/change-password` 端点
2. 修改密码时调用 `revoke_all_user_tokens()`
3. 用户禁用账户时也撤销所有 token

**预期结果**: 修改密码或禁用账户后，所有旧 token 立即失效

---

## 📋 修复清单

### 第 1 优先级 修复列表

- [ ] **#1.1** 在 `run.py` 中完善 `require_user` 依赖
- [ ] **#1.2** 在 `routers/members.py` 中添加认证检查
- [ ] **#1.3** 在 `routers/events.py` 中添加认证检查
- [ ] **#1.4** 在 `routers/scenarios.py` 中添加认证检查
- [ ] **#1.5** 在 `routers/delegation.py` 中添加认证检查
- [ ] **#1.6** 在 `routers/audit.py` 中添加认证检查
- [ ] **#2.1** 实现真实的 `/api/v1/auth/me` 端点
- [ ] **#3.1** 重命名 Delegation 字段（from_member_id → from_user_id）
- [ ] **#3.2** 重命名 Delegation 字段(to_member_id → to_user_id)
- [ ] **#3.3** 添加自委托防护约束
- [ ] **#4.1** 添加日志系统到 `run.py`
- [ ] **#4.2** 改进 `/verify` 端点异常处理
- [ ] **#4.3** 改进认证相关异常处理
- [ ] **#5.1** 添加 `/auth/change-password` 端点
- [ ] **#5.2** 调用 `revoke_all_user_tokens()`（修改密码时）
- [ ] **5.3** 测试 RefreshToken 撤销逻辑

### 验证步骤

- [ ] 语法检查：`python -m py_compile`
- [ ] 单元测试：`pytest tests/ -q`
- [ ] 集成测试：smoke test 脚本
- [ ] 权限测试：无 Token 访问返回 401
- [ ] 权限测试：无权限访问返回 403
- [ ] 用户接口测试：`GET /auth/me` 返回真实数据
- [ ] 密码修改测试：修改后旧 token 失效

---

## ✅ 完成标志

第 1 优先级完成条件：
- ✅ 所有 endpoint 都要求认证
- ✅ /auth/me 返回真实用户数据
- ✅ Delegation 表不允许自委托
- ✅ 异常处理隐藏内部细节
- ✅ RefreshToken 支持自动撤销
- ✅ 32/32 pytest 测试通过
- ✅ 0 个新增回归

---

## 🚀 开始执行

**开始时间**: 2026-02-26 14:00  
**预期完成**: 2026-02-26 17:45  
**检查点**: 每完成 1 个任务后运行 `pytest -q`

