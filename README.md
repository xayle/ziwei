# 浮生 · BaZi / Ziwei 引擎与产品壳

| 字段 | 内容 |
|------|------|
| **产品** | **浮生** — 档案 → 八字 / 紫微 → 六卷报告（主入口 `/static/app/`） |
| **引擎** | 八字 + 紫微 API（FastAPI）；`ENGINE_V2=true` 时四柱走 `services/bazi_engine/` |
| **状态** | **打磨 / 软可用**（主路径可真用）· **GTM 未开**（[R109 选项 A](docs/reports/R109-post-w14-decision-2026-07-12.md)） |
| **当前主题** | A 维护 + B 内容深化（life/volumes、大运呈现、典籍 verified）· 少开新面 |
| **问题清单** | [UI-FEATURE-ISSUE-INVENTORY](docs/reports/UI-FEATURE-ISSUE-INVENTORY-2026-07-14.md)（inv-1.33） |
| **人工签字包** | [HUMAN-SIGNOFF-PACKET](docs/reports/HUMAN-SIGNOFF-PACKET-2026-07-15.md) |

> 勿将本仓库理解为「已全面 Production Ready / 已授权投放」。机读门禁（scorecard / W14）绿 ≠ 对外 GTM。

### 本地入口

```bash
# 后端
./start-local.ps1 -Port 8000
# 或: uvicorn run:app --host 127.0.0.1 --port 8000 --reload

# 前端开发
cd frontend && npm run dev

# 对齐生产静态壳（改前端后务必执行）
cd frontend && npm run build   # 输出到 ../static/app/
```

- SPA：`http://127.0.0.1:8000/static/app/`
- API 文档：`http://127.0.0.1:8000/docs`
- 开发统一入口：[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

### 引擎与质量（机读）

| 文档 / 信号 | 说明 |
|-------------|------|
| [底层修复计划](docs/plan/ENGINE-CORE-FIX-PLAN-2026-07-11.md) | Phase 0–4 |
| [八字 / 紫微 Gap](docs/design/bazi/bazi-gap-audit.md) · [紫微](docs/design/ziwei/ziwei-gap-audit.md) | 缺口清单 |
| `docs/reports/scorecard-latest.json` | 目标 10.0 / 24 项 |
| `docs/reports/w14-auto-verify-latest.json` | W14 bundle |
| [A+B D1 薄卷加厚缺口](docs/reports/A-B-D1-VOLUME-THICKEN-GAPS-2026-07-19.md) | vol2 / vol6 等下一刀 |

`ENGINE_V2=true` 时 `calculate()` 走 `_calculate_v2`，四柱经 **`services/bazi_engine/pillars.py`**（sxtwl/cnlunar + `solar_time_v2`）。OpenAPI：`make export-openapi` 或 `python scripts/export_openapi.py`。

---

## 历史：v8.0 / Week 3 里程碑（归档摘要）

以下为早期 BaZi Service 阶段交付记录，**不代表当前浮生产品对外状态**。

### v8.0 功能矩阵（N0–N7，历史）

| 里程碑 | 内容 | 关键交付物 |
|--------|------|-----------|
| N0–N7 | 引擎、API、持久化、UX、测试与发布 | 见仓库 git 与 CHANGELOG |
| 紫微斗数 | 安星 / 四化 / 运限 | SPA 主入口 + 兼容页 |

### Week 3 开发完成汇总（2026-02，历史）

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

### 📖 文档导航

> 开发统一入口：**[`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)**

#### 用户快速开始
1. [README](README.md) ← **你在这里**
2. [**docs/DEVELOPMENT.md**](docs/DEVELOPMENT.md) — 开发统一入口 ⭐
3. [docs/README.md](docs/README.md) — 文档索引
4. [docs/plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md](docs/plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md) — W1–W16 执行

#### 开发人员指南
1. [docs/guides/PERMISSION-MANAGEMENT-GUIDE.md](docs/guides/PERMISSION-MANAGEMENT-GUIDE.md) — 权限最佳实践 ⭐ 新增
2. [services/permission_cascade_service.py](services/permission_cascade_service.py) — 实现源码
3. [tests/test_cascade_validation.py](tests/test_cascade_validation.py) — 使用示例

#### 架构文档 (Week 1-2原有)
- [docs/design/01-schemas.md](docs/design/01-schemas.md)
- [docs/design/02-architecture.md](docs/design/02-architecture.md)
- [docs/design/03-rbac-audit.md](docs/design/03-rbac-audit.md)

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

# 默认本地端口（若脚本自动回退请改成实际端口）
PORT=8000

# 运行服务器
uvicorn run:app --host 127.0.0.1 --port ${PORT}

# 推荐（Windows / PowerShell）：使用启动脚本自动检查 .env 与端口占用
./start-local.ps1 -Port 8000

# 默认本地地址（若脚本自动回退端口请改成实际端口）
BASE_URL=http://127.0.0.1:8000

# 运行全部测试
pytest tests/ -v
# 结果: ✅ 854/854 tests passed (6 skipped)

# 统一质量门禁
make quality-gate
make quality-gate-backend
make quality-gate-frontend

# 访问API文档
# Swagger: ${BASE_URL}/docs
# ReDoc: ${BASE_URL}/redoc
```

> 说明：若 8000 端口已被占用，`start-local.ps1` 会自动回退到下一个可用端口（最多探测 20 个端口），并在启动信息中打印实际端口。

#### 核心API使用示例

```bash
# 默认本地地址（若脚本自动回退端口请改成实际端口）
BASE_URL=http://127.0.0.1:8000

# 1. 用户登录
curl -X POST ${BASE_URL}/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"owner","password":"userpassword"}'
# 返回: {
#   "access_token": "eyJ...",
#   "refresh_token": "token_...",
#   "user": {id, username, role, ...}
# }

# 2. 检查当前权限
# Authorization: Bearer <access_token>
curl ${BASE_URL}/api/v1/members/permissions \
  -H "Authorization: Bearer <token>"
# 返回: {permissions: ["create_member", "read_member", ...]}

# 3. 委托权限给其他用户
curl -X POST ${BASE_URL}/api/v1/delegations \
  -H "Authorization: Bearer <token>" \
  -d '{
    "to_member_id": 2,
    "permission_type": "create_event",
    "expires_days": 30
  }'
# 返回: {id, from_member_id, to_member_id, ...}

# 4. 创建场景
curl -X POST ${BASE_URL}/api/v1/scenarios \
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
1. [**docs/DEVELOPMENT.md**](docs/DEVELOPMENT.md) — 开发统一入口 ⭐ **从这里开始**
2. [docs/README.md](docs/README.md) — 文档索引
2. [docs/design/01-schemas.md](docs/design/01-schemas.md) — Member/Event/Scenario 数据模型
3. [docs/design/02-architecture.md](docs/design/02-architecture.md) — 工具箱统一架构 (ToolBase + Registry)
4. [docs/design/03-rbac-audit.md](docs/design/03-rbac-audit.md) — 权限矩阵 + 审计日志链
5. [docs/design/SCHEMA-SPLIT-PLAN.md](docs/design/SCHEMA-SPLIT-PLAN.md) — schema 拆分计划

### 🎯 优化方案 (可选纳入开发)
- **[docs/reports/OPTIMIZATION-SUMMARY.md](docs/reports/OPTIMIZATION-SUMMARY.md)** — 3个优化方向对比 & 决策建议 ⭐ **优先阅读**
- [docs/reports/OPTIMIZATION-1-permission-performance.md](docs/reports/OPTIMIZATION-1-permission-performance.md) — 权限检查性能 (缓存+SQL优化)
- [docs/reports/OPTIMIZATION-2-event-recommendation.md](docs/reports/OPTIMIZATION-2-event-recommendation.md) — 推荐理由生成 (规则引擎vs模板vs LLM)
- [docs/reports/OPTIMIZATION-3-data-model.md](docs/reports/OPTIMIZATION-3-data-model.md) — 数据模型调整 (字段精简+表拆分)

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
- Verify: [docs/design/api.md](docs/design/api.md#post-apiv1verify)
- BaZi Full: [docs/design/api.md](docs/design/api.md#post-apiv1bazifull)
- OpenAPI: [docs/openapi.json](docs/openapi.json)

## Release Notes
- Latest: [v8.0.7](CHANGELOG.md)
- All releases: [docs/release-notes/](docs/release-notes/)

## BaZi Full quickstart (v5.0.0)
- Warnings: top-level `warnings` (object list); verify keeps `validation.warnings`.
- Methods: fixed defaults for traceability (day_boundary_rule=zi_initial, solar_time_rule=longitude_only, dayun_method=sxtwl_next_jieqi_div3, ...). See [docs/design/api.md](docs/design/api.md#post-apiv1bazifull) for the full set.
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
- Start API (recommended on Windows): `./start-local.ps1 -Port 8000` (auto fallback to next free port when target port is occupied)
- Recreate env: `pip install -r requirements.lock.txt` (frozen from the working venv).

## Local Smoke
- Start API (terminal A): `PORT=8000; uvicorn run:app --reload --host 127.0.0.1 --port ${PORT}`（若自动回退端口请替换）
- Run smoke (terminal B): `BASE_URL=http://127.0.0.1:8000 bash scripts/smoke_local.sh` or `BASE_URL=http://127.0.0.1:8000 pwsh scripts/smoke_local.ps1`（若自动回退端口请替换）
- What it covers: /health plus /api/v1/verify cases for request_id (generate/echo/invalid/truncate) and tz_mismatch warning. It runs all cases, summarizes failures, and exits non-zero on any failure.
- Dependencies: curl + python (PowerShell uses curl.exe). No extra tools required.

## Local UI
- Primary UI (SPA): run app normally and open `${BASE_URL}/static/app/cases` (default `http://127.0.0.1:8000/static/app/cases`; requires built frontend assets under `static/app`)
- Current main entry: `/static/app/cases`
- SPA base: `/static/app/` continues to host the active routes for login, cases, profile, bazi, ziwei, admin, report, and related pages
- Legacy compatibility entries: `/static/ziwei.html`, `/static/bazi.html`, `/static/admin.html`, `/static/batch.html`
- Root entry: `${BASE_URL}/` and `${BASE_URL}/dashboard` redirect to `/static/app/cases` when SPA assets exist; otherwise they fall back to the legacy `ziwei.html`
- Frontend dev server: `npm run dev --prefix frontend` (Vite will auto-switch from `5173` to another free port, e.g. `5174`)
- Local dev main site: `http://localhost:5173/static/app/cases`（若 `5173` 被占用，请以 Vite 实际端口为准）
- Frontend API target (optional): copy `frontend/.env.example` to `frontend/.env.local`; set `VITE_DEV_API_TARGET` to actual backend URL (e.g. auto-fallback `http://127.0.0.1:8003`) and/or set `VITE_API_BASE_URL` for direct runtime calls
- One-command sync (recommended): `npm --prefix frontend run sync:api` (or `pwsh scripts/sync_frontend_env.ps1`), auto probes `/health` on 8000-8010 and writes `frontend/.env.local`
- After changing `frontend/.env.local`, restart Vite dev server to apply env updates
- Pages
  - /static/app/cases: 当前主站入口，承载新版案例中心首页
  - /static/app/: 当前 SPA 路由基座，承载 login / cases / profile / bazi / ziwei / admin / report 等新版页面
  - /static/app/workbench: 兼容旧入口；当前统一重定向到 `/static/app/cases`
  - /verify: 兼容别名入口；优先跳转到 `/static/app/cases`，若 SPA 未构建则回退到 legacy `ziwei.html`
  - /bazi: 兼容别名入口；优先跳转到 `/static/app/bazi`，若 SPA 未构建则回退到 legacy `bazi.html`
  - /admin: 兼容别名入口；优先跳转到 `/static/app/admin`，若 SPA 未构建则回退到 legacy `admin.html`
  - /static/verify.html: 兼容跳转页，当前直接跳转到 `/static/app/cases`
  - /static/ziwei.html: legacy 紫微独立页（当前作为人工回归对照与兜底入口保留）
  - /static/bazi.html: 兼容页；默认优先跳往 `/static/app/bazi`，可通过 `?legacy=1` 停留旧版
  - /static/admin.html: 兼容页；默认优先跳往 `/static/app/admin`，可通过 `?legacy=1` 停留旧版
  - /static/batch.html: legacy 批量核验工具页（独立保留）
  - /static/index.html: 旧静态入口，当前会优先探测并跳转到 `/static/app/cases`，若新版资源不存在则回退到 `/static/ziwei.html`
- Defaults: mode=dual，solar_time_enabled=false，liunian_years=[-2,2]
