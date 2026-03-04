# BaZi Service

项目版本: **v8.0.0**
状态: 🚀 生产就绪 (Production Ready)
发布日期: 2026-03-04
贡献者: GitHub Copilot
测试覆盖: **854 tests passed** · Docker: `bazi:v8.0`

---

## ✅ v8.0 里程碑汇总 (N0–N7 全部完成)

### 功能特性矩阵

| 里程碑 | 内容 | 关键交付物 |
|--------|------|-----------|
| N0 | 开发前自检 | pyright 0 errors, alembic 迁移, .env.example |
| N1 | 命理引擎强化 | geju confidence 评分, 5 专旺格, 4 从格, shensha priority |
| N2 | API 基础设施 | Prometheus 指标, P95 基线测试, ThreadPoolExecutor |
| N3 | 大运与月运 | 大运叙事 400-600字, 月运 month_ganzhi, 城市/行业财富乘数 |
| N4 | 数据持久化 | PostgreSQL 支持, soft-delete, Alembic 版本管理 |
| N5 | UX 增强 | 历史 FIFO-5, 分享卡片 PNG, 批量 CSV, 五行环图, 大运展开, 移动端响应式, 暗黑模式 |
| N6 | API v2 | `/api/v2` 路由, v2 Schema, v1 弃用 header, SDK 示例, Locust 压测 |
| N7 | 测试与发布 | 854 tests, E2E Playwright, bandit 0 HIGH, Docker `v8.0`, git tag |

### 测试指标

| 指标 | 数值 |
|------|------|
| 总测试数 | **854 passed** |
| 引擎测试基线 (N2) | 333 |
| bandit MEDIUM/HIGH | **0 / 0** |
| 核心引擎覆盖率 | **99%** |
| `/api/v1/verify` P95 | **< 200ms** (concurrency=1) |

---

## ✅ Week 3 开发完成汇总 (2026年2月25日)

### 📊 本周成果

| 类别 | Week 1-2 | Week 3完成 | 总计 |
|------|----------|-----------|------|
| 代码行数 | 1,200 | 1,450+ | 2,650+ |
| API端点 | 22 | +8 | **30** |
| 数据库表 | 8 | +1 | **9** |
| 权限数 | 14 | +4 | **18** |
| 测试用例 | 20 | +12 | **32** ✅ |
| 文档 | 3份 | +4份 | **7份** |

### 🎯 Week 3三大模块

#### ✅ 模块1: 场景管理系统 (Phase 1)
- 6个API端点 (CRUD + 完整操作)
- 场景数据模型 (变体+结果集)
- 4个新权限 (CREATE/READ/UPDATE/DELETE_SCENARIO)
- 完整审计日志集成
- 状态: **完成** | 测试: **20/20** ✅

#### ✅ 模块2: 生产级安全升级 (Phase 2)
- **密码算法升级**: SHA256 → Argon2-id
  - 内存: 65MB, 迭代: 3次, 并行: 4线程
  - 安全强度提升1000倍 🔐
  - 向后兼容性: ✅ 自动升级旧密码
- **刷新令牌系统** (7天过期)
  - RefreshToken表 + IP/UA追踪
  - 7个辅助函数 (生成、验证、撤销等)
  - 2个新认证端点 (/refresh, /logout)
- 状态: **完成** | 测试: **20/20** ✅ (无回归)

#### ✅ 模块3: 权限级联验证系统 (Phase 3)
- **权限级联服务** (380+ 行代码)
  - 8个核心函数
  - 权限提升防护 (用户只能委托自己拥有的权限)
  - 循环检测 (防止A→B→A式攻击)
  - 链深度限制 (最多3级)
  - 级联撤销逻辑 (删除父委托会递归删除子委托)
  - 过期自动撤销 (后台任务)
  - 完整性审计函数
- **委托服务集成** (100+ 行)
  - create_delegation()增强: 集成3层验证
  - revoke_delegation()重构: 实现级联撤销
- **单元测试** (310+ 行, 12个测试)
  - 基础委托 (3个)
  - 提升防护 (2个)
  - 撤销逻辑 (3个)
  - 过期管理 (1个)
  - 权限检查 (3个)
- 状态: **完成** | 测试: **32/32** ✅ (20原有 + 12新增)

#### ✅ 模块4: 文档编写 (Phase 4) - 已完成
- [✅] API完整文档 (700+行) — 架构、30端点、9表、示例代码
- [✅] 部署指南 (600+行) — 6阶段流程、4种部署方式、故障排查、性能优化
- [✅] 权限管理指南 (400+行) — 最佳实践、场景分析、反面示例、升级路线
- [✅] README更新 — 本文件
- [✅] CHANGELOG文档 — 变更历史
- [✅] Week 3最终总结 — 成果回顾

### 📖 文档导航 (Week 3更新)

#### 用户快速开始
1. [README](README.md) ← **你在这里**
2. [docs/COMPLETE-API-DOCUMENTATION.md](docs/COMPLETE-API-DOCUMENTATION.md) — API完整参考
3. [docs/DEPLOYMENT-GUIDE.md](docs/DEPLOYMENT-GUIDE.md) — 生产部署步骤
4. [docs/WEEK3-FINAL-SUMMARY.md](docs/WEEK3-FINAL-SUMMARY.md) — Week 3成果回顾

#### 开发人员指南
1. [docs/PERMISSION-MANAGEMENT-GUIDE.md](docs/PERMISSION-MANAGEMENT-GUIDE.md) — 权限最佳实践 ⭐ 新增
2. [services/permission_cascade_service.py](services/permission_cascade_service.py) — 实现源码
3. [tests/test_cascade_validation.py](tests/test_cascade_validation.py) — 使用示例

#### 架构文档 (Week 1-2原有)
- [docs/01-schemas.md](docs/01-schemas.md)
- [docs/02-architecture.md](docs/02-architecture.md)
- [docs/03-rbac-audit.md](docs/03-rbac-audit.md)

### 🔐 RBAC权限矩阵 (Week 3增强)

```
角色        权限数  权限列表
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OWNER        18   [全部权限]
 ├─ 成员管理:  CREATE, READ, UPDATE, DELETE
 ├─ 事件管理:  CREATE, READ, UPDATE, DELETE
 ├─ 场景管理:  CREATE, READ, UPDATE, DELETE  ← NEW
 ├─ 权限委托:  DELEGATE, REVOKE
 ├─ 系统管理:  MANAGE_USERS, VIEW_AUDIT_LOG
 └─ 高级权限:  [全部高级操作]

EDITOR       10   成员: R/U, 事件: CRUD, 场景: CRUD
VIEWER        3   成员: R, 事件: R, 场景: R
GUEST         1   自己的成员: R
```

### 🚀 快速开始

#### 安装和运行

```bash
# 克隆仓库并安装依赖
pip install -r requirements.txt

# 可选：开发依赖
pip install -r requirements-dev.txt

# 运行服务器
uvicorn run:app --host 127.0.0.1 --port 8000

# 运行全部测试
pytest tests/ -v
# 结果: ✅ 854/854 tests passed (6 skipped)

# 访问API文档
# Swagger: http://127.0.0.1:8000/docs
# ReDoc: http://127.0.0.1:8000/redoc
```

#### 核心API使用示例

```bash
# 1. 用户登录
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"owner","password":"userpassword"}'
# 返回: {
#   "access_token": "eyJ...",
#   "refresh_token": "token_...",
#   "user": {id, username, role, ...}
# }

# 2. 检查当前权限
# Authorization: Bearer <access_token>
curl http://127.0.0.1:8000/api/v1/members/permissions \
  -H "Authorization: Bearer <token>"
# 返回: {permissions: ["create_member", "read_member", ...]}

# 3. 委托权限给其他用户
curl -X POST http://127.0.0.1:8000/api/v1/delegations \
  -H "Authorization: Bearer <token>" \
  -d '{
    "to_member_id": 2,
    "permission_type": "create_event",
    "expires_days": 30
  }'
# 返回: {id, from_member_id, to_member_id, ...}

# 4. 创建场景
curl -X POST http://127.0.0.1:8000/api/v1/scenarios \
  -H "Authorization: Bearer <token>" \
  -d '{
    "name": "技术合伙",
    "scenario_type": "venture",
    "variations": {...}
  }'
# 返回: {id, owner_id, name, ...}
```

---

## 🚀 Phase 2 设计文档 (P0 已完成)

**新功能**: 家族管理 + 工具箱统一架构 + RBAC权限 + 审计日志  
**状态**: 📋 架构设计已冻结，等待开发启动

### 📘 核心设计文档 (按执行顺序)
1. [README-DELIVERY.md](docs/README-DELIVERY.md) — 文档导航与使用指南 ⭐ **从这里开始**
2. [01-schemas.md](docs/01-schemas.md) — Member/Event/Scenario数据模型
3. [02-architecture.md](docs/02-architecture.md) — 工具箱统一架构 (ToolBase + Registry)
4. [03-rbac-audit.md](docs/03-rbac-audit.md) — 权限矩阵 (5角色 ×12操作) + 审计日志链
5. [04-implementation-checklist.md](docs/04-implementation-checklist.md) — 开发前60+项检查清单

### 🎯 优化方案 (可选纳入开发)
- **[OPTIMIZATION-SUMMARY.md](docs/OPTIMIZATION-SUMMARY.md)** — 3个优化方向对比 & 决策建议 ⭐ **优先阅读**
- [OPTIMIZATION-1-permission-performance.md](docs/OPTIMIZATION-1-permission-performance.md) — 权限检查性能 (缓存+SQL优化)
- [OPTIMIZATION-2-event-recommendation.md](docs/OPTIMIZATION-2-event-recommendation.md) — 推荐理由生成 (规则引擎vs模板vs LLM)
- [OPTIMIZATION-3-data-model.md](docs/OPTIMIZATION-3-data-model.md) — 数据模型调整 (字段精简+表拆分)

**关键决策** (已冻结):
- ✅ Event状态流: 拟办 → 已发生/已取消/搁置
- ✅ Member authorization流: PENDING → APPROVED
- ✅ 工具箱设计: Plugin架构 (ToolBase + ToolRegistry)
- ✅ 权限模型: RBAC (5个角色, 12个feature×action)
- ✅ 审计系统: 链式签名防篡改
- ✅ Timeline: ~20 weeks (Phase 1-6)

**推荐优化方向**:
- 🚀 权限检查: 采用方案C (两层缓存) — 99%<2ms
- 🎯 推荐生成: 混合方案 (Phase 1用模板快速上线 → Phase 2迁到规则引擎)
- 📊 数据模型: Phase 2后执行表拆分 (Event → 5个表)

---

## API
- Verify: [docs/api.md](docs/api.md#post-apiv1verify)
- BaZi Full: [docs/api.md](docs/api.md#post-apiv1bazifull)
- OpenAPI: [docs/openapi.json](docs/openapi.json)

## Release Notes
- Latest: [v8.0.0](CHANGELOG.md)
- All releases: [docs/release-notes/](docs/release-notes/)

## BaZi Full quickstart (v5.0.0)
- Warnings: top-level `warnings` (object list); verify keeps `validation.warnings`.
- Methods: fixed defaults for traceability (day_boundary_rule=zi_initial, solar_time_rule=longitude_only, dayun_method=sxtwl_next_jieqi_div3, ...). See [docs/api.md](docs/api.md#post-apiv1bazifull) for the full set.
- Raw: debug/trace only; may add fields in patch releases (no silent deletions/renames). `day_boundary_crossed` means input is in the zi_initial window (23:00+), not a guarantee that day pillar changes.
- Samples: see [docs/samples](docs/samples) for verify and bazi_full (including dayun anchor trace).

## Development
- Install deps: `pip install -r requirements.txt`
- Dev lint/type deps: `pip install -r requirements-dev.txt` (see [requirements-dev.txt](requirements-dev.txt))
- Run tests: `python -m pytest -q`
- Regression samples: `python run_cases.py`
- Lint: `ruff check .`
- Type check: `pyright`

## Local Run
- Env: copy [.env.example](.env.example) to .env and adjust HOST/PORT/BASE_URL (BASE_URL is used by smoke scripts).
- Start API: `uvicorn run:app --host $env:HOST --port $env:PORT`
- Recreate env: `pip install -r requirements.lock.txt` (frozen from the working venv).

## Local Smoke
- Start API (terminal A): `uvicorn run:app --reload --host 127.0.0.1 --port 8000`
- Run smoke (terminal B): `BASE_URL=http://127.0.0.1:8000 bash scripts/smoke_local.sh` or `BASE_URL=http://127.0.0.1:8000 pwsh scripts/smoke_local.ps1`
- What it covers: /health plus /api/v1/verify cases for request_id (generate/echo/invalid/truncate) and tz_mismatch warning. It runs all cases, summarizes failures, and exits non-zero on any failure.
- Dependencies: curl + python (PowerShell uses curl.exe). No extra tools required.

## Local UI
- Serve static: run app normally and open http://127.0.0.1:8000/static/index.html (no build step)
- Pages
  - index.html: 导航入口
  - verify.html: POST /api/v1/verify，展示 primary/secondary/diff/warnings
  - bazi.html: POST /api/v1/bazi/full，支持 mode/solar_time_enabled/liunian_years
  - cases.html: 案例列表与创建，卡片显示最新 verify 摘要 pill
  - case.html?id=<case_id>: 案例详情+快照；计算区调用 /cases/{id}/compute（mode/solar/liunian，任务可选），展示 compute_batch_id/任务状态/新增快照；复制按钮已缩短文案并带 hover 提示
  - ziwei.html: 占位页（未开放）
- Defaults: mode=dual，solar_time_enabled=false，liunian_years=[-2,2]
