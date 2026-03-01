# Week 3 开发计划 - 场景模拟 + 生产优化

## 📅 Week 3 目标 (6-10工作日)

| 阶段 | 任务 | 优先级 | 时间投入 | 状态 |
|------|------|--------|---------|------|
| Day 1-2 | 场景模拟系统 | 🔴 高 | 2天 | 计划中 |
| Day 2-3 | 生产级安全 | 🔴 高 | 2天 | 计划中 |
| Day 4 | 权限级联验证 | 🟡 中 | 1天 | 计划中 |
| Day 5 | 文档和部署 | 🟡 中 | 1天 | 计划中 |

---

## 🎯 Phase 1: 场景模拟系统 (Day 1-2)

### 功能描述
允许用户模拟不同的八字场景进行what-if分析，而无需修改实际客户数据。

### 数据模型
```python
Scenario {
    id: int
    owner_id: int           # 所有者
    member_id: int          # 关联成员（可伪造参数）
    name: str              # 场景名称
    description: str       # 场景描述
    base_member_id: int    # 基础成员（用于参考）
    simulated_data: JSON   # 修改的八字数据
    scenario_type: str     # "date_change", "gender_change", "location_change", "custom"
    changes_made: dict     # 具体改动记录
    analysis_result: JSON  # 分析结果
    confidence_score: float
    created_at: datetime
    updated_at: datetime
    is_archived: bool      # 是否存档
}
```

### API端点设计

#### 1. 创建场景
```
POST /api/v1/scenarios
{
  "member_id": 5,
  "name": "改换生日后的运势",
  "description": "假设母亲改换生日为...",
  "scenario_type": "date_change",
  "simulated_data": {
    "birth_date": "1968-05-10",  # 改动的日期
    "birth_time": "14:30"
  },
  "base_member_id": 5
}
→ 返回 ScenarioResponse
```

**权限要求**: `CREATE_SCENARIO`

#### 2. 列表查询
```
GET /api/v1/scenarios           # 所有场景
GET /api/v1/scenarios?member_id=5  # 特定成员的场景
GET /api/v1/scenarios?type=date_change  # 按类型筛选
GET /api/v1/scenarios/{id}      # 场景详情
```

**权限要求**: `READ_SCENARIO`

#### 3. 更新场景
```
PUT /api/v1/scenarios/{id}
{
  "name": "新的场景名称",
  "simulated_data": { ... },
  "analysis_result": { ... }
}
```

**权限要求**: `UPDATE_SCENARIO`

#### 4. 删除/存档
```
DELETE /api/v1/scenarios/{id}           # 删除
PATCH /api/v1/scenarios/{id}/archive    # 存档
```

**权限要求**: `DELETE_SCENARIO`

#### 5. 对比分析
```
GET /api/v1/scenarios/{id}/compare
→ 返回 {
  "actual": { ... },        # 实际成员的分析
  "simulated": { ... },     # 模拟场景的分析
  "differences": [ ... ]    # 两者的差异点
}
```

#### 6. 场景列表特殊视图
```
GET /api/v1/scenarios/member/{member_id}/all  # 该成员的所有场景
GET /api/v1/scenarios/shared                  # 与我共享的场景
```

### 权限系统扩展
添加4个新权限:
```python
"CREATE_SCENARIO"    # 拥有者
"READ_SCENARIO"      # 拥有者 + 编辑者 + 查看者 + 受委托人
"UPDATE_SCENARIO"    # 拥有者 + 编辑者
"DELETE_SCENARIO"    # 拥有者
```

### 验证流程
1. ✅ 单元测试：8个新测试
2. ✅ 多用户隔离验证
3. ✅ 权限边界测试
4. ✅ curl示例测试
5. ✅ 运行完整测试套件

### 预期结果
- ✅ 6个新API端点
- ✅ 4个新权限定义
- ✅ 完整CRUD操作
- ✅ 所有测试通过 (20+ → 28+)

---

## 🔐 Phase 2: 生产级安全 (Day 2-3)

### 2.1 密码哈希升级

**当前状态**: SHA256简单哈希
**目标**: Argon2PasswordHasher (行业标准)

#### 实现步骤
```python
# services/auth_service.py 中添加

from argon2 import PasswordHasher

hasher = PasswordHasher()

def hash_password(password: str) -> str:
    """使用Argon2哈希密码"""
    return hasher.hash(password)

def verify_password(password: str, hash: str) -> bool:
    """验证密码"""
    try:
        hasher.verify(hash, password)
        return True
    except:
        return False

# 修改register和login
```

#### 迁移计划
- 新密码自动使用Argon2
- 旧密码通过login时自动升级
- 无缝向后兼容

### 2.2 刷新令牌机制

**设计**:
```python
RefreshToken {
    id: int
    user_id: int
    token: str (唯一)
    expires_at: datetime
    created_at: datetime
    is_revoked: bool
    ip_address: str
    user_agent: str
}
```

#### API端点
```
POST /api/v1/auth/refresh
{
  "refresh_token": "..."
}
→ 返回 {
  "access_token": "新的JWT",
  "refresh_token": "新的刷新令牌",
  "expires_in": 86400
}

POST /api/v1/auth/logout
→ 撤销当前刷新令牌
```

#### 安全特性
- 刷新令牌不能用于API请求
- 刷新令牌存储在数据库（可撤销）
- 每次刷新生成新的令牌对
- IP变更检测（可选告警）

### 2.3 CORS 配置

```python
# run.py中添加

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600
)
```

### 2.4 速率限制

```python
# 添加SlowAPI包
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# 在路由上使用
@router.post("/auth/register")
@limiter.limit("5/minute")
def register(...):
    ...
```

### 2.5 安全响应头

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response
```

### 验证清单
- ✅ 所有用户密码升级为Argon2
- ✅ 刷新令牌端点测试
- ✅ CORS配置生效
- ✅ 速率限制工作
- ✅ 所有安全头生效
- ✅ 回归测试通过 (20 → 20+)

---

## 🔗 Phase 3: 权限级联验证 (Day 4)

### 功能描述
确保员工的权限级联验证，防止权限提升漏洞。

### 实现

#### 验证规则
```python
def validate_permission_chain(session, delegating_user, target_user, permission):
    """
    验证权限级联链
    规则：
    1. 用户不能委托自己没有的权限
    2. 用户不能增加权限级别
    3. 已过期的权限不能转发
    """
    
    # 1. 检查委托者是否有该权限
    delegating_role = Role(delegating_user.role)
    if not has_permission(delegating_role, permission):
        raise PermissionError("Cannot delegate permission you don't have")
    
    # 2. 检查是否存在有效的委托链
    # (如果权限来自委托，检查委托是否有效)
    
    return True
```

#### 权限矩阵验证
```
权限检查层次：
1. 用户基本角色 (Role → Permissions)
2. 权限委托 (Delegation)
3. 委托链验证 (无法提升权限)
4. 成员级别范围 (member_id限制)
5. 过期时间检查 (auto-revoke)
```

### 单元测试
```python
def test_permission_escalation_prevention():
    """确保VIEWER不能委托EDITOR权限"""
    
def test_chain_validation():
    """验证权限委托链的正确性"""
    
def test_expired_delegation_revocation():
    """验证过期权限自动失效"""
```

---

## 📝 Phase 4: 文档和部署准备 (Day 5)

### 文档任务
1. ✅ API完整文档 (OpenAPI/Swagger)
2. ✅ 部署指南
3. ✅ 安全最佳实践
4. ✅ 故障排查文档
5. ✅ 权限矩阵表

### 部署清单
```
□ 环境变量配置 (.env.example)
□ Docker容器支持
□ 数据库迁移脚本
□ 日志聚合配置
□ 监控告警设置
□ CI/CD流程
```

### 成果物
- WEEK3-DEPLOYMENT-GUIDE.md
- API-SECURITY-CHECKLIST.md
- TROUBLESHOOTING.md
- deployment.yml (Docker Compose)

---

## 📊 Week 3 测试目标

| 指标 | Week 2 | Week 3 目标 | 验证方法 |
|------|--------|------------|---------|
| 单元测试 | 20 | 28+ | pytest suite |
| API端点 | 22 | 28 | curl + Swagger |
| 代码覆盖率 | ~80% | 85%+ | coverage report |
| 性能 (p95延迟) | <50ms | <100ms | load test |
| 安全审计 | ✓ | 100% | OWASP check |

---

## 🚀 Week 3 执行计划

### Day 1-2 时间表
```
09:00 - 创建Scenario模型和表
10:00 - 实现场景CRUD服务
11:00 - 创建routers/scenarios.py
12:00 - 集成到run.py
13:00 - 编写单元测试
14:00 - 权限验证和测试
15:00 - 文档和Swagger
16:00 - 部署验证
```

### Day 2-3 时间表 (安全性)
```
09:00 - Argon2集成
10:00 - RefreshToken实现
11:00 - CORS中间件
12:00 - 速率限制器
13:00 - 安全头部
14:00 - 迁移脚本
15:00 - 集成测试
16:00 - 安全审计
```

### Day 4 时间表
```
09:00 - 权限验证设计
10:00 - 级联链验证实现
11:00 - 单元测试编写
12:00 - 集成测试
13:00 - 文档编写
```

### Day 5 时间表
```
09:00 - 部署指南编写
10:00 - 完整API文档
11:00 - 安全检查清单
12:00 - Docker配置
13:00 - 性能测试
14:00 - 最终验证
```

---

## ✅ Week 3 完成条件

### 功能完成
- [ ] 场景模拟系统（6个端点）
- [ ] Argon2密码哈希
- [ ] 刷新令牌机制
- [ ] CORS和安全头
- [ ] 速率限制
- [ ] 权限级联验证

### 测试完成
- [ ] 28+ 单元测试通过
- [ ] 所有端点curl可用
- [ ] 权限边界验证
- [ ] 安全漏洞扫描 (0个critical/high)

### 文档完成
- [ ] API完整文档
- [ ] 部署指南
- [ ] 故障排查指南
- [ ] 权限矩阵表

### 系统准备
- [ ] 生产环境部署脚本
- [ ] 监控和告警
- [ ] 备份和恢复流程
- [ ] 更新日志和版本说明

---

## 📈 Week 3 成功指标

```
✅ 所有代码编程和测试完成
✅ 场景模拟系统生产就绪
✅ 密码安全升级完成
✅ API完全文档化
✅ 28+ 单元测试全部通过
✅ 零critical安全问题
✅ 部署流程自动化
```

---

## 🎯 之后的发展方向 (Week 4+)

### 短期 (Week 4)
- 前端UI框架集成 (React/Vue)
- 用户界面实现
- 客户端SDK生成

### 中期 (Week 5-6)
- 数据可视化仪表盘
- 高级分析报表
- 导入导出功能

### 长期 (Week 7+)
- 多租户支持
- 国际化 (i18n)
- 移动应用支持
- 第三方集成 (微信、支付宝等)

---

**计划制定时间**: 2026年2月25日  
**下周启动**: Week 3 Day 1  
**预期完成**: 2026年3月7日
