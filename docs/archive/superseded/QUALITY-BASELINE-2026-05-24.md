# 质量基线报告 — 2026-05-24

本文档记录项目在 2026-05-24 当日的测试/构建/静态分析各维度量化基线，
作为 Phase 3/5 交付物。后续 CI 流程以此为准线。

---

## 一、测试基线

### 1.1 后端 pytest

| 指标 | 值 |
|---|---|
| 收集文件数 | 全部（含 test_concurrency、test_property_bazi） |
| 通过数 | **2592** |
| 跳过数 | 2 |
| 失败数 | 0 |
| 警告数 | 12（均为第三方库，无需处理） |
| 运行时长 | ~98s |
| 运行命令 | `python -m pytest -q --tb=no` |

> 新增修复（本次）：
> - `services/ziwei_engine/__init__.py` — `aux_names` 属性兼容 `list[str]`
> - `services/ziwei_engine/forecast.py` — `_stars_in_palace` 使用 `aux_names`
> - `tests/test_normalize_rate_auth.py` — bypass 路径测试更新为 `local_bypass` 用户
> - `tests/test_coverage_boost17/18/19/22` — 修复 `_backend_status`/`_is_metrics_allowed`/`init_db`/`_static_dir` patch 目标
> - 环境修复：补装 `pytest-timeout` 和 `hypothesis`（已在 requirements-dev.txt 声明）

### 1.2 前端 Vitest

| 指标 | 值 |
|---|---|
| 测试文件数 | **42** |
| 通过数 | **398** |
| 失败数 | 0 |
| 运行时长 | ~7s |
| 运行命令 | `cd frontend && npx vitest run` |

---

## 二、构建基线

### 2.1 前端 Vite build

| 指标 | 值 |
|---|---|
| 构建命令 | `cd frontend && npm run build` |
| 输出目录 | `frontend/dist/` |
| 类型检查 | `vue-tsc --noEmit` (0 错误) |
| 当前状态 | **⚠️ 构建产物已快照到 `static/app/`，Dockerfile/deploy.ps1 尚未自动构建** |

> 待解决：Dockerfile 和 deploy.ps1 均无 `npm run build` 步骤，见第四节。

### 2.2 后端无需独立构建步骤

Python 项目无编译步骤，直接由 uvicorn 运行。

---

## 三、静态分析基线

### 3.1 前端 TypeScript（vue-tsc）

```
npx vue-tsc --noEmit
exit code: 0   — 无类型错误
```

### 3.2 前端 ESLint

- **当前状态**：`package.json` 中无 ESLint 依赖，尚未配置。
- **计划**：Batch C 添加 `eslint.config.js`（vue3 + typescript-eslint）。

### 3.3 后端 ruff

```
python -m ruff check . --statistics
Found 460 errors
  [*] 292 fixable with --fix
  主要规则：E501(行长), E302, F401(未使用导入), E702...
```

- **当前状态**：已安装 ruff，有 460 个 lint 提示（绝大多数为风格/格式问题）。
- **计划**：Batch C 添加 `pyproject.toml`，注册 ruff 配置，修复可自动修复的 292 个问题。

### 3.4 后端 pyright

| 指标 | 值 |
|---|---|
| 配置文件 | `pyrightconfig.json`（已存在）|
| 类型检查模式 | basic |
| 当前状态 | 未纳入 CI，建议 Batch C 集成 |

---

## 四、部署就绪度

| 场景 | 命令 | 前端自动构建 | 状态 |
|---|---|---|---|
| 本地开发 | `.\deploy.ps1 -Action up` | ❌ 无 | **待修复** |
| Docker 构建 | `docker build .` | ❌ 无 | **待修复** |
| Docker Compose | `docker-compose up --build` | ❌ 无 | **待修复** |

计划：在 Dockerfile 中新增 `node:20-slim` 前端构建阶段，`deploy.ps1` 添加 `npm run build` 步骤。

---

## 五、文档可信度

| 文档 | 类型 | 可信度 | 最后更新 | 说明 |
|---|---|---|---|---|
| `docs/设计.txt` | 执行日志 | ⭐⭐⭐⭐⭐ 极高 | 2026-05-24 | 154+ 轮实际执行记录，与代码完全对应 |
| `docs/计划.txt` | 路线图 | ⭐⭐⭐⭐⭐ 极高 | 2026-05-24 | Phase 1-7 结构，已执行到 Phase 5 |
| `docs/LEGACY-SPA-MIGRATION-MATRIX.md` | 现状文档 | ⭐⭐⭐⭐⭐ 极高 | 2026-05-24 | 已反映 ziwei.html compat 状态 |
| `docs/CHANGELOG.md` / `CHANGELOG.md` | 变更记录 | ⭐⭐⭐⭐ 高 | 最近提交 | 与 git log 对应 |
| `docs/README.md` | 文档入口 | ⭐⭐⭐⭐ 高 | 2026-06-15 | 当前文档索引 |
| `docs/design/api.md` | API 文档 | ⭐⭐⭐ 中 | 未同步 | 部分路由路径可能滞后于代码 |
| `docs/guides/DEPLOYMENT-GUIDE.md` | 部署指南 | ⭐⭐⭐ 中 | 未同步 | 前端构建步骤缺失，待补充 |
| `docs/openapi.json` | API Schema | ⭐⭐⭐ 中 | 构建时生成 | 需运行 `/docs` 端点导出最新版 |
| `docs/04-implementation-checklist.md` | 检查清单 | ⭐⭐ 偏低 | 旧版 | 大量条目状态未更新 |

---

## 六、回归防护措施

1. **测试门槛**：主分支 PR/push 应通过 `python -m pytest -q --tb=no` 零失败
2. **前端门槛**：`npx vitest run` 零失败 + `vue-tsc --noEmit` 零错误
3. **标记规范**：新增测试用 `@pytest.mark.integration/slow/benchmark/auth/api/services/models/sxtwl/cnlunar`
4. **测试超时**：`@pytest.mark.timeout(N)` — 已有 `pytest-timeout>=2.3` 声明

---

*由代码助手自动生成 — 2026-05-24*
