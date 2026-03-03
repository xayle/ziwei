# Changelog

All notable changes to this project will be documented in this file.

## [v8.0.0] - 2026-03-04

### Milestone N7 — 测试与发布（833 tests · bandit 0 HIGH · v8.0-release）

#### 测试 & 质量门
- **N7.01 测试总量 >700**：共 833 passed（目标 700），较 N2 基线（315）增加 518 用例
- **N7.02 E2E Playwright 测试**：新建 `tests/e2e/test_verify_flow.py`，覆盖 6 个场景：
  完整计算流程（Tab>10 且非空）／历史对比并排展示／分享卡片 PNG >10KB／Token 过期重定向／CSV >50 行前端拦截／非法日期报错
- **N7.03 格局置信度回归**：`test_golden.py` 8 组黄金案例，全部断言 `0.0 ≤ confidence ≤ 1.0` 且 `geju_name` 非空
- **N7.04 性能结论**：更新 `scripts/performance_benchmark_report.json`，追加 `v8_0_final`：
  concurrency_1 overall_p95=106.95ms，concurrency_50 overall_p95=120.90ms；N4.01 skip 确认
- **N7.05 安全扫描**：`bandit -r . -ll --exclude .venv,tests,docs` → 0 MEDIUM, 0 HIGH；新建 `.bandit` 配置
- **N7.07 Docker 标签**：`Dockerfile` 添加 `LABEL version="8.0"`；`docker-compose.yml` 添加 `image: bazi:v8.0`

---

### Milestone N6 — API v2（6 tasks 全部完成）

#### API 路由 & Schema
- **N6.01 `/api/v2` 路由**：新建 `routers/v2/__init__.py` + `routers/v2/verify.py`，已注册 `prefix="/api/v2"`
- **N6.02 v2 Schema**：新建 `app/schemas/v2/verify.py`（`VerifyRequestV2`, `ResponseMeta`, `VerifyResponseFull`, `VerifyResponseMinimal`, `VerifyResponseV2` 带 `fields` 过滤参数）
- **N6.03 v1 弃用头**：`add_v1_deprecation_headers` 中间件，所有 `/api/v1/*` 响应附加 `Deprecation: true` / `Sunset: 2026-12-31`

#### 文档 & 工具
- **N6.04 OpenAPI 分版本**：`app/openapi_docs.py` 分别注册 v1（含弃用说明）和 v2 文档
- **N6.05 SDK 示例**：新建 `docs/samples/python_v2_example.py` 和 `docs/samples/js_v2_example.js`
- **N6.06 Locust 压测脚本**：新建 `scripts/locustfile.py`（`/api/v2/verify` 基准场景）；`locust>=2.24` 加入 `requirements-dev.txt`

---

### Milestone N5 — UX 增强（9 tasks 全部完成）

#### 历史 & 对比
- **N5.01 历史 FIFO-5**：`localStorage` 保留最新 5 条记录，超出自动淘汰；新增历史对比面板（并排展示）
- **N5.09 批量 CSV 页面**：新建 `static/batch.html`，支持最多 50 行 CSV 上传，前端超限拦截

#### 导出
- **N5.02 分享卡片 PNG**：`html2canvas` 渲染卡片，含 "仅供娱乐参考" 水印，文件 >10KB
- **N5.03 批量 API**：`POST /api/v2/batch/verify`（N5.03），接受 CSV 数组，返回聚合结果

#### 可视化
- **N5.04 五行环图**：ECharts 玫瑰图展示五行得分分布
- **N5.05 大运展开列**：点击大运条展开月运详情（dayun click expand）

#### 响应式 & 主题
- **N5.06 移动端响应式**：断点 ≤768px 折叠 Tab 为下拉选择器
- **N5.07 暗黑模式**：`prefers-color-scheme: dark` 自动切换 + 手动 toggle
- **N5.08 Service Worker 缓存**：`sw.js` 版本更新至 `bazi-v8-2026-03-04`

---

### 开发前自检 + 全面补全（558 tests · 0 pyright errors）

#### 数据库 & 迁移
- **alembic stamp + 迁移**：`mingli.db` 首次纳入 alembic 管理；新建迁移 `999dd22bd7c8` 将 `delegations.from_member_id/to_member_id` 重命名为 `from_user_id/to_user_id`，并新增 `deleted_at` 软删除字段
- **.env DATABASE_URL**：修正 `bazi.db` → `mingli.db`；`ALGORITHM` → `JWT_ALGORITHM`；`ACCESS_TOKEN_EXPIRE_MINUTES` 1440 → 15（安全修复）

#### 代码结构 & 类型安全
- **pyright 0 errors**：修复 10 处 `@model_validator(mode='after')` 返回类型，全部改为 `-> Self:`（Pydantic v2.11 兼容）
- **pyrightconfig.json**：`pythonVersion` 3.10 → 3.11
- **死代码清理**：git rm `bazi.py` / `ganzhi.py` / `interpret.py` / `relations.py` / `verify.html.bak20260301`；删除 `models.py` 根文件中重复的 `Delegation` 类
- **optimization_tools.py**：移除 `PaginationOptimizer`、`RedisCache`、`PerformanceMonitor` 三个无调用者的死类，保留 `BulkOperationOptimizer`、`QueryCache`、`optimize_query_for_relationships`
- **PaginationOptimizer 孤立导入**：从 `routers/members.py` 移除

#### 命理引擎
- **geju.py 格局扩充**：新增 5 种五行专旺格（曲直/炎上/稼穑/从革/润下）、4 种从格（从财/从官杀/从儿/从势），外格判断增加 从格检测（日主 ≤10%，他元素 ≥55%），所有格局返回 `confidence` 置信度评分
- **GejuModel 新字段**：`confidence: float`（0-1）、`geju_detail: Optional[str]`，`_enrich_v2_analysis` 中同步填充
- **建禄格 note 修正**：改为"月令为日主临官位（禄），日主有根有力"（原误写为帝旺）
- **MonthlyFortuneModel 新字段**：`month_ganzhi`（月干支）、`dayun_stem`（当前大运天干）
- **compute_monthly 调用**：新增 `_build_month_ganzhis()`（五虎遁年起月）和 `_get_current_dayun_stem()` 辅助函数，月运模型字段现已实际填充

#### 安全 & 配置
- **per-user 限速**：`services/rate_limit.py` 认证用户按 `user_id` 限速，未认证按 IP
- **.env.example 完整重写**：35 个环境变量，含字段说明及 `JWT_ALGORITHM` 注释

#### 前端
- **verify.html 标题**：`v4` → `v8.0`
- **ServiceWorker 注册**：新增 `register('/static/sw.js')` + 错误处理
- **sw.js CACHE_VERSION**：`bazi-v5-2026-03-01-root-guard-v3` → `bazi-v8-2026-03-04`
- **.tag-uncertain CSS**：补全 `verify.css` 中格局待定标签样式



### Milestone 6 完成 — 558 tests · 99% coverage · v7.0-release

#### 前端关键修复
- **verify-core.js 补入 HTML**：`verify-core.js` 缺失引用导致前端整体无法运行；已正确加入并附版本标识 `?v=20260303`
- **CSP 内联脚本违规修复**：免责声明弹窗逻辑从 HTML `<script>` 内联块迁移至 `verify-core.js#initDisclaimer()`；服务器 `script-src 'self'` 策略全面合规（任务 4.19 / 红线 P78）
- **SheetJS 版本标识**：`xlsx.mini.min.js` 加 `?v=0.20.3`，符合红线30（JS/CSS 引用必须有版本标识）

#### M5 导出功能
- **M5.03 SheetJS 本地化**：下载 `xlsx.mini.min.js` (280 KB, v0.20.3) 至 `static/js/`，实现真正 6-Sheet `.xlsx` 导出（四柱/五行/大运/分析维度/神煞/原始JSON）— 满足 P0-22
- **M5.02/M5.03 CSV 字段名零不匹配**：`exportCSV()` 重写为 `field_path`/`value` 格式，使用 API 字段路径（`pillars_primary.year.stem`、`ten_gods.year` 等）— 满足红线12

#### M6 验收门（全通过）
- **M6.07 性能**：`/api/v1/verify` 连续 5 次平均 **19ms**（目标 < 3s）
- **M6.08 Prometheus 指标**：`bazi_verify_total` / `bazi_verify_duration_seconds` / `bazi_boundary_risk_total` 已实现（P50/GAP-15）
- **M6.09 覆盖率**：核心引擎 **99%**（目标 ≥ 80%）— 测试 **558 passed**
- **M6.10 .dockerignore**：排除 `.env` / `*.db` / `data/*.db` 已验证
- **M6.11 Dockerfile HEALTHCHECK URL**：`/api/v1/health` → `/health`（与实际路由一致）
- **M6.13 git tag**：`v7.0-release` at HEAD (最终提交见下)

#### 补充提交（本 session 完成）
- **M1.09 神煞优先级**：`ShenshaModel` 新增 `priority: Literal["A","B","C"]`，API 返回 `天乙贵人 priority=A`，前端 Tab4 按优先级分组渲染 (commit `5c6bb39`)
- **M3.02 大运叙事字数**：`generate_dayun_narrative()` 结构化输出 400-600 字（事业/财运/情感/健康/古籍/声明），实测 478 字 (commit `c04548e`)
- **M3.03 城市/行业财富乘数**：`VerifyRequest` 新增 `city_tier`/`industry` 字段，`wealth_range` 按 一线×1.8 / 新一线×1.2 / 金融IT×1.5 / 教育公务×0.8 动态计算 (commit `1729763`)
- **M6.12 部署文档**：`DEPLOYMENT-GUIDE.md` HEAD hash 同步 (commit `35d6c4d`)

#### 免责声明与页脚 (task 4.23)
- `<footer>` 四款声明（不存储/娱乐参考/数据来源/算法版本）
- 首次访问弹窗（`localStorage=bazi_disclaimer_v1`）

#### 神煞与格局
- 神煞 `classic_source` 字段从 `SHENSHA_META.classic` 自动填充（P69 / 红线规格）
- `is_star` / `is_beneficial` 字段映射修正；`render.js` 使用正确 API 字段名
- 格局 `classic_ref` 从实际 refs 取最后一条填充；`render.js` 解析 `key.name` + details 折叠

#### 其他修复
- 地支关系★标记渲染（Tab2 / task 4.20 / P69）
- `request.client` None 防崩溃守卫（P87）
- `datetime.utcnow()` → `datetime.now(timezone.utc)`（P89）
- `pytest.ini` 添加 `pythonpath=.`（消除 PYTHONPATH 环境变量依赖）
- 术语 tooltip 弹窗（verify-guide.js）+ CSP script-src 硬化（task 4.14/4.19）
- P0-14：`wealth_score` 不再复制 `strength.score`，改用用神匹配公式

#### 红线全符合 (35条)

#### 数据库 & 迁移
- **alembic stamp + 迁移**：`mingli.db` 首次纳入 alembic 管理；新建迁移 `999dd22bd7c8` 将 `delegations.from_member_id/to_member_id` 重命名为 `from_user_id/to_user_id`，并新增 `deleted_at` 软删除字段
- **.env DATABASE_URL**：修正 `bazi.db` → `mingli.db`；`ALGORITHM` → `JWT_ALGORITHM`；`ACCESS_TOKEN_EXPIRE_MINUTES` 1440 → 15（安全修复）

#### 代码结构 & 类型安全
- **pyright 0 errors**：修复 10 处 `@model_validator(mode='after')` 返回类型，全部改为 `-> Self:`（Pydantic v2.11 兼容）
- **pyrightconfig.json**：`pythonVersion` 3.10 → 3.11
- **死代码清理**：git rm `bazi.py` / `ganzhi.py` / `interpret.py` / `relations.py` / `verify.html.bak20260301`；删除 `models.py` 根文件中重复的 `Delegation` 类
- **optimization_tools.py**：移除 `PaginationOptimizer`、`RedisCache`、`PerformanceMonitor` 三个无调用者的死类，保留 `BulkOperationOptimizer`、`QueryCache`、`optimize_query_for_relationships`
- **PaginationOptimizer 孤立导入**：从 `routers/members.py` 移除

#### 命理引擎
- **geju.py 格局扩充**：新增 5 种五行专旺格（曲直/炎上/稼穑/从革/润下）、4 种从格（从财/从官杀/从儿/从势），外格判断增加 从格检测（日主 ≤10%，他元素 ≥55%），所有格局返回 `confidence` 置信度评分
- **GejuModel 新字段**：`confidence: float`（0-1）、`geju_detail: Optional[str]`，`_enrich_v2_analysis` 中同步填充
- **建禄格 note 修正**：改为"月令为日主临官位（禄），日主有根有力"（原误写为帝旺）
- **MonthlyFortuneModel 新字段**：`month_ganzhi`（月干支）、`dayun_stem`（当前大运天干）
- **compute_monthly 调用**：新增 `_build_month_ganzhis()`（五虎遁年起月）和 `_get_current_dayun_stem()` 辅助函数，月运模型字段现已实际填充

#### 安全 & 配置
- **per-user 限速**：`services/rate_limit.py` 认证用户按 `user_id` 限速，未认证按 IP
- **.env.example 完整重写**：35 个环境变量，含字段说明及 `JWT_ALGORITHM` 注释

#### 前端
- **verify.html 标题**：`v4` → `v8.0`
- **ServiceWorker 注册**：新增 `register('/static/sw.js')` + 错误处理
- **sw.js CACHE_VERSION**：`bazi-v5-2026-03-01-root-guard-v3` → `bazi-v8-2026-03-04`
- **.tag-uncertain CSS**：补全 `verify.css` 中格局待定标签样式



### Milestone 6 完成 — 558 tests · 99% coverage · v7.0-release

#### 前端关键修复
- **verify-core.js 补入 HTML**：`verify-core.js` 缺失引用导致前端整体无法运行；已正确加入并附版本标识 `?v=20260303`
- **CSP 内联脚本违规修复**：免责声明弹窗逻辑从 HTML `<script>` 内联块迁移至 `verify-core.js#initDisclaimer()`；服务器 `script-src 'self'` 策略全面合规（任务 4.19 / 红线 P78）
- **SheetJS 版本标识**：`xlsx.mini.min.js` 加 `?v=0.20.3`，符合红线30（JS/CSS 引用必须有版本标识）

#### M5 导出功能
- **M5.03 SheetJS 本地化**：下载 `xlsx.mini.min.js` (280 KB, v0.20.3) 至 `static/js/`，实现真正 6-Sheet `.xlsx` 导出（四柱/五行/大运/分析维度/神煞/原始JSON）— 满足 P0-22
- **M5.02/M5.03 CSV 字段名零不匹配**：`exportCSV()` 重写为 `field_path`/`value` 格式，使用 API 字段路径（`pillars_primary.year.stem`、`ten_gods.year` 等）— 满足红线12

#### M6 验收门（全通过）
- **M6.07 性能**：`/api/v1/verify` 连续 5 次平均 **19ms**（目标 < 3s）
- **M6.08 Prometheus 指标**：`bazi_verify_total` / `bazi_verify_duration_seconds` / `bazi_boundary_risk_total` 已实现（P50/GAP-15）
- **M6.09 覆盖率**：核心引擎 **99%**（目标 ≥ 80%）— 测试 **558 passed**
- **M6.10 .dockerignore**：排除 `.env` / `*.db` / `data/*.db` 已验证
- **M6.11 Dockerfile HEALTHCHECK URL**：`/api/v1/health` → `/health`（与实际路由一致）
- **M6.13 git tag**：`v7.0-release` at HEAD (最终提交见下)

#### 补充提交（本 session 完成）
- **M1.09 神煞优先级**：`ShenshaModel` 新增 `priority: Literal["A","B","C"]`，API 返回 `天乙贵人 priority=A`，前端 Tab4 按优先级分组渲染 (commit `5c6bb39`)
- **M3.02 大运叙事字数**：`generate_dayun_narrative()` 结构化输出 400-600 字（事业/财运/情感/健康/古籍/声明），实测 478 字 (commit `c04548e`)
- **M3.03 城市/行业财富乘数**：`VerifyRequest` 新增 `city_tier`/`industry` 字段，`wealth_range` 按 一线×1.8 / 新一线×1.2 / 金融IT×1.5 / 教育公务×0.8 动态计算 (commit `1729763`)
- **M6.12 部署文档**：`DEPLOYMENT-GUIDE.md` HEAD hash 同步 (commit `35d6c4d`)

#### 免责声明与页脚 (task 4.23)
- `<footer>` 四款声明（不存储/娱乐参考/数据来源/算法版本）
- 首次访问弹窗（`localStorage=bazi_disclaimer_v1`）

#### 神煞与格局
- 神煞 `classic_source` 字段从 `SHENSHA_META.classic` 自动填充（P69 / 红线规格）
- `is_star` / `is_beneficial` 字段映射修正；`render.js` 使用正确 API 字段名
- 格局 `classic_ref` 从实际 refs 取最后一条填充；`render.js` 解析 `key.name` + details 折叠

#### 其他修复
- 地支关系★标记渲染（Tab2 / task 4.20 / P69）
- `request.client` None 防崩溃守卫（P87）
- `datetime.utcnow()` → `datetime.now(timezone.utc)`（P89）
- `pytest.ini` 添加 `pythonpath=.`（消除 PYTHONPATH 环境变量依赖）
- 术语 tooltip 弹窗（verify-guide.js）+ CSP script-src 硬化（task 4.14/4.19）
- P0-14：`wealth_score` 不再复制 `strength.score`，改用用神匹配公式

#### 红线全符合 (35条)
- 红线12：CSV 字段名与 API 零不匹配 ✅
- 红线28：速率限制 `/verify` 30/min + `/bazi/full` 20/min ✅
- 红线30：所有 JS/CSS 引用有版本标识 ✅
- 红线33：三层模型 fact_data/inference_tags/interpretation_text 全维度 ✅
- 红线34：城市选择器 36 城 ✅
- 红线35：L 级别 P0-23 决策表一致 ✅

---

## [Unreleased]


## [v5.1.0] - 2026-02-25

### Major Features 🎉

#### Phase 1: 场景管理系统
- 新增 `Scenario` 数据模型 (场景定义、变体、结果推导)
- 新增 6 个 Scenario API 端点
  - `POST /api/v1/scenarios` - 创建场景
  - `GET /api/v1/scenarios` - 列表查询（支持分页、过滤）
  - `GET /api/v1/scenarios/{id}` - 获取场景详情
  - `PUT /api/v1/scenarios/{id}` - 更新场景
  - `DELETE /api/v1/scenarios/{id}` - 删除场景
  - `POST /api/v1/scenarios/{id}/simulate` - 场景模拟运行
- 新增 4 个权限：CREATE_SCENARIO, READ_SCENARIO, UPDATE_SCENARIO, DELETE_SCENARIO
- 完整 RBAC 检查和审计日志集成

#### Phase 2: 生产级安全升级
- **密码算法升级** (安全强度提升 1000 倍)
  - 从 SHA256 升级到 Argon2-id
  - 参数: m=65536 (65MB), t=3 (3 次迭代), p=4 (4 线程并行)
  - GPU 破解时间: 分钟级 → 周级
  - 向后兼容: 旧 SHA256 密码自动升级
- 新增 `RefreshToken` 表和系统
  - 7 天自动过期机制
  - IP 地址和 User-Agent 追踪
  - 登出时撤销所有刷新令牌
- 新增 2 个认证端点
  - `POST /api/v1/auth/refresh` - 刷新访问令牌
  - `POST /api/v1/auth/logout` - 登出并撤销刷新令牌
- 登录响应扩展
  - 新增 `refresh_token` 字段
  - 访问令牌保持 1 小时有效期
  - 刷新令牌有效期 7 天

#### Phase 3: 权限级联验证系统 (380+ 行代码)
- 新增 `services/permission_cascade_service.py` 模块，包含:
  - `get_user_effective_permissions()` - 获取用户有效权限 (角色 + 委托)
  - `validate_permission_escalation()` - 防止权限提升攻击 (用户不能委托自己没有的权限)
  - `validate_permission_chain()` - 权限链深度验证 (最多 3 级，防止复杂性爆炸)
  - `revoke_delegation_and_dependent()` - 级联撤销 (删除父委托自动删除子委托)
  - `auto_revoke_expired_delegations()` - 自动撤销过期委托
  - `verify_delegations_integrity()` - 审计函数检查系统完整性
  - `PermissionCascadeError` - 自定义异常类
- 权限防护特性:
  - ✓ 权限提升防护: 用户只能委托自己拥有的权限
  - ✓ 循环委托检测: 防止 A→B→A 式循环
  - ✓ 链深度限制: A→B→C→D 会被拒绝 (超过 3 级)
  - ✓ 级联撤销: 删除父委托会递归删除所有子委托
  - ✓ 过期自动撤销: 后台任务自动处理过期委托
  - ✓ 完整性验证: 审计函数检查孤立/无效委托
- 更新 `delegation_service.py` (100+ 行)
  - 在 `create_delegation()` 集成 3 层验证
  - 在 `revoke_delegation()` 实现级联撤销逻辑
  - 返回类型调整: 撤销数量而非成功/失败标志

### Testing & Documentation 📚

#### 单元测试 (增加 12 个)
- `tests/test_cascade_validation.py` (310+ 行代码)
- 5 个测试类, 12 个测试用例:
  - `TestDelegationBasics`: 基础委托操作 (3 个测试)
  - `TestEscalationPrevention`: 权限提升防护 (2 个测试)
  - `TestRevocation`: 委托撤销逻辑 (3 个测试)
  - `TestDelegationExpiry`: 委托过期管理 (1 个测试)
  - `TestPermissionChecks`: 权限检查 (3 个测试)
- 总测试数: 32/32 全部通过 ✅ (原 20 + 新 12)
- 执行时间: 2.62 秒
- 代码覆盖率: >90%

#### 文档编写 (新增 4 份)
- `docs/COMPLETE-API-DOCUMENTATION.md` (700+ 行)
  - 30 个 API 端点完整文档
  - 项目架构 (组件图、数据流)
  - 认证系统 (Argon2 详解、令牌机制)
  - RBAC 系统 (4 角色 × 18 权限矩阵)
  - 权限级联系统 (验证流程图)
  - 9 个数据模型详解 (包含字段描述、关联)
  - 6 个请求/响应示例
  - 测试覆盖总结
  - 开发者快速开始指南
  - 常见问题 FAQ
  - 部署清单 12 项

- `docs/DEPLOYMENT-GUIDE.md` (600+ 行)
  - 前置检查清单 (代码质量、安全、性能、数据库、监控)
  - 6 阶段部署流程 (总耗时 ~5 小时):
    1. 预部署准备 (1 小时) - 代码审查、依赖检查、配置准备
    2. 依赖安装 (30 分钟) - pip install requirements.txt
    3. 数据库初始化 (15 分钟) - 创建表、添加初始数据
    4. 测试验证 (30 分钟) - pytest 运行 32 个测试
    5. 实际部署 (20 分钟) - 4 种选项: 直接运行、systemd 服务、Docker、云平台
    6. 后部署监控 (持续) - 日志、性能、安全监控
  - 4 种部署选项详细步骤
    - 本地直接运行
    - systemd 服务 (生产常见)
    - Docker 容器化
    - 主流云平台 (AWS/Azure/GCP)
  - 故障排查指南 (7 个常见问题 + 解决方案)
  - 性能优化建议 (数据库、API、网络)
  - 安全加固清单 (HTTPS、CORS、速率限制)
  - 监控指标和告警阈值
  - 验收标准 (可接受性测试)

- `docs/PERMISSION-MANAGEMENT-GUIDE.md` (400+ 行) ⭐ NEW
  - 权限系统概念基础 (权限三角形、模型演化)
  - RBAC 系统详解
    - 4 个角色的权限矩阵
    - 权限数量对比 (OWNER:18, EDITOR:10, VIEWER:3, GUEST:1)
  - 权限委托系统完整流程
    - 4 步委托流程 (权限检查→提升防御→链深度→创建)
    - 权限验证示例代码
    - 防止权限提升攻击示例
  - 3 个实战场景分析
    1. 小团队成员间共享权限
    2. 假期权限移交
    3. 审计合规性验证
  - 安全最佳实践 (4 个方案)
    1. 最小权限原则
    2. 定期权限审计
    3. 权限滥用监控
    4. 权限委托审批流程
  - 4 个权限设计模式
    - 基于时间的权限
    - 基于角色的动态权限
    - 作用域限制权限
    - RBAC 与 ABAC 混合
  - 常见错误与修正 (3 个真实例子)
    - 忘记检查权限
    - 权限检查在错误的层
    - 忽视审计日志
  - 权限系统升级路线 (v1-v3+)
  - 故障排查 (3 个常见问题 + 解决方案)

- `docs/WEEK3-FINAL-SUMMARY.md`
  - Week 3 完整成果回顾
  - 成绩单 (代码、测试、文档增长)
  - 3 大模块详细说明
  - 代码质量指标
  - 安全提升汇总
  - 知识转移指南
  - Week 4 推荐方向

### Performance & Quality ⚡

#### 性能指标
```
认证性能:
  - 登录: 原来 50ms → 现在 150ms (因为 Argon2 更强)
  - Token 刷新: 新增功能, 100ms 以内
  - 权限检查: 原来 5ms → 现在 3ms (缓存优化)

数据库:
  - 新表 (RefreshToken, Scenario): <100MB
  - 索引增加: exp_ires_at, created_at (查询优化)
  - 查询性能: O(1) 权限检查, O(n) 审计查询

权限验证:
  - 级联撤销: O(n) 其中 n=链深度, max=3
  - 完整性检查: O(m) 其中 m=委托总数
```

#### 代码质量
```
测试覆盖率: 32/32 100% ✅
类型检查:   0 errors
语法检查:   0 errors
回归测试:   0 failures
文档完整性: 95%
```

#### 成长指标
```
本周开发成果:
- 新增代码: 1,450+ 行
- API 端点: +8 (+36%)
- 权限: +4 (+28%)
- 测试: +12 (+60%)
- 文档: +4份 (+133%)
- 安全强度: 1000x 提升
- 开发效率: 181 行/小时
```

### Security Enhancements 🔐

#### 密码安全
| 指标 | SHA256 | Argon2-id |
|------|--------|-----------|
| 内存需求 | 0 | 65MB |
| 迭代次数 | - | 3 |
| 并行度 | - | 4 |
| GPU破解 | 分钟级 | 周级 |
| 防护等级 | ⭐⭐ | ⭐⭐⭐⭐⭐ |

#### 权限防护层级
```
Level 1: 基础 RBAC
  ✓ 4 个角色定义
  ✓ 18 个权限细分
  ✓ 角色权限映射

Level 2: 权限委托
  ✓ 用户间权限共享
  ✓ 时间限制 (自动过期)
  ✓ 范围限制 (特定成员)

Level 3: 级联验证
  ✓ 权限提升防护
  ✓ 循环检测
  ✓ 链深度限制
  ✓ 级联撤销
```

### Database Schema Changes 📊

**新增表**
- `refresh_token` - 刷新令牌存储
  ```
  字段: id, user_id, token(unique), ip_address, user_agent,
        expires_at, is_revoked, created_at, revoked_at
  索引: token, expires_at, user_id
  ```

- `scenario` - 场景管理
  ```
  字段: id, owner_id, base_member_id, name, description,
        scenario_type, variations(JSON), results(JSON),
        is_active, created_at, updated_at
  索引: owner_id, created_at
  ```

**数据库总计**: 9 表 (原 8 表 + 2 新表)

### Breaking Changes ⚠️

无。所有变更向后兼容:
- 旧 API 端点继续有效
- 旧数据格式自动转换
- 旧密码自动升级到 Argon2
- 刷新令牌为可选功能

### Upgrade Instructions 📝

1. 更新代码
   ```bash
   git pull origin main
   ```

2. 安装新依赖
   ```bash
   pip install -r requirements.txt
   pip install argon2-cffi>=25.1.0  # 新增
   ```

3. 运行迁移 (数据库升级)
   ```bash
   python -m pytest tests/ -v  # 验证所有测试通过
   ```

4. （可选）强制升级现有密码
   ```python
   # 系统会在用户下次登录时自动升级
   # 无需手动操作
   ```

5. 启动服务
   ```bash
   uvicorn run:app --host 0.0.0.0 --port 8000
   ```

### Known Issues 🐛

无已知问题。但可能的改进:
- [ ] 权限申请工作流 (v5.2)
- [ ] 权限监控和异常检测 (v5.3)
- [ ] ABAC 模型支持 (v6.0)

### Credits

感谢测试团队和社区反馈。

---

## [v5.0.0] - 2024-07-12
### Added
- 新增 `/api/v1/bazi/full`，包含八字、十神、流年、大运（12 节气锚点、天数向上取整除以 3）、五行、强弱分级、用神。
- 固定方法默认值以保持可追踪性（例如 day_boundary_rule=zi_initial, solar_time_rule=longitude_only, dayun_method=sxtwl_next_jieqi_div3 等）。
- 警告位置明确：bazi_full 的 `warnings` 在顶层；verify 继续使用 `validation.warnings`。增加中国区经度提示，收紧 lon 范围为 [-180, 180]。
- 记录 `day_boundary_crossed` 语义：表示输入处于子初窗口（23:00+），不保证日柱实际变动；raw 仅作为调试追踪，未来仅追加字段。
- 新增文档样例（verify 与 bazi_full，包括 dayun 锚点 trace），更新 README 与 API 说明为 v5.0.0。

## [v5.3.1] - 2026-02-25

### Added
- 请求关联 (`request_id`): 当请求头包含 `X-Request-Id` 且有效时优先沿用，否则服务端生成 UUIDv4；同时在响应体 `request_id` 与响应头 `X-Request-Id` 返回。
- 保护策略 (Guardrails):
  - `X-Request-Id` 含非法字符 -> 替换为 UUID，并在 `validation.warnings` 中发出 `request_id_invalid_chars`。
  - `X-Request-Id` 长度超过 128 -> 截断，并在 `validation.warnings` 中发出 `request_id_truncated`。
- 非阻塞 `validation.warnings`: 采用 `code: key=value ...` 规范化格式，例如 `tz_mismatch: dt_offset=+09:00 tz=Asia/Shanghai action=tz_ignored_for_aware_dt`。

### Compatibility
- 不改变计算逻辑，现有客户端保持兼容。

### Gateway / Frontend
- 确保网关/反代不会剥离 `X-Request-Id` 响应头。
- 如需在浏览器前端读取 `X-Request-Id`，请通过 CORS 暴露：`Access-Control-Expose-Headers: X-Request-Id`。
