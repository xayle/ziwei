# 浮生 · 开发手册（规矩 · 命令 · 插件 · 唯一实操入口）

| 字段 | 内容 |
|------|------|
| **版本** | handbook-1.2 |
| **日期** | 2026-07-13 |
| **定位** | **日常开发只看本文** — 规矩、环境、插件、全部命令、PR 门禁 |
| **进度/问题** | [`FUSHENG-DEV-STATUS-2026-07-13.md`](FUSHENG-DEV-STATUS-2026-07-13.md) |
| **前端组件细节** | [`guides/FUSHENG-FRONTEND-DEV.md`](guides/FUSHENG-FRONTEND-DEV.md)（§组件/母版；规矩以本文为准） |
| **执行打勾** | [`plan/FUSHENG-EXECUTION-REMAINING.md`](plan/FUSHENG-EXECUTION-REMAINING.md) |

> **一句话**：算法写命盘，典籍写讲解，前端编成书；**先真源、再三页、再六卷**；合并 PR 前跑齐 §八 命令。

---

## 一、30 秒开工

```powershell
# 1. Cursor 打开仓库根 c2/ → Trust Workspace
# 2. 扩展：Install All（.vscode/extensions.json）→ Reload Window
# 3. 依赖
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
cd frontend && npm ci && npm run install:e2e

# 4. 双终端
#    Tasks → backend:dev   或  python -m uvicorn app.main:app --reload --port 8000
#    Tasks → frontend:dev  或  cd frontend && npm run dev

# 5. 浏览器
#    http://localhost:5173/static/app/  → / · /profile · /new/bazi · /report
```

---

## 二、开发规矩（必须遵守）

### 2.1 阶段纪律

| 规则 | 说明 |
|------|------|
| **避险顺序** | F0 文档 → F1 skin+截图 → F2 三页 → F3 buildLifeVolumes → F4 报告 → F5 工作台 → F6 验收 |
| **禁止跳步** | 未过 targets 截图门禁不得大改 Report；未过三门禁不得扩六卷样式 |
| **打磨期禁止** | 付费墙 · snippets · 埋点漏斗 · 暗色模式 · GTM（见 POST-W14） |
| **W14 前禁止** | 自行加 T071+ 任务；R107 未签不开增长/平台轨 |
| **单真源** | Token→`variables.css`；类型→`schema.d.ts`；六卷→`life-volume.schema.json` |

### 2.2 仓库规矩

| 规则 | 说明 |
|------|------|
| 打开根目录 | **必须** `c2/` 根，不要只开 `frontend/` |
| 信任工作区 | Cursor **Trust Workspace**，否则扩展/Tasks 失效 |
| Python | **3.11+**（CI/pre-commit 对齐）；Windows 可用 `uv python install 3.11` |
| Node | **18+**；`npm ci` 勿随意改 lock |
| OpenAPI 变更 | 必须 `export-openapi` + `gen:types` 同 PR 提交 |
| Git 提交 | 大 WIP 时分批提交；pre-commit 会 stash 未暂存文件导致 smoke 失败 |
| Windows `npm ci` | 文件锁（esbuild EPERM）时勿强跑；用 `npm install --legacy-peer-deps` 修复，或逐条 `npm run type-check/test/build` |

### 2.3 前端铁律（三门禁 + R-01~R-05）

**铁律顺序：**

```text
先统一真源 → 再打磨三页（八字/紫微/报告卷目）→ 再扩六卷
禁止：丑排版上贴卷名 · interpretation 充首屏 · 未过截图门禁就大重构 Report
```

| 预警码 | 首屏不得出现 |
|--------|--------------|
| R-01 | `PageHead` 与壳双标题；顶栏+大标题+口径叠 4–5 层 |
| R-02 | `-ok-bg` · Tailwind 绿黄 alert 铺底 · 冷灰 `#334155` |
| R-03 | Inter 全文 · 16px 圆角白卡堆叠（模板站感） |
| R-04 | >80 字 interpretation 首屏；无盘面/KPI |
| R-05 | 渐变铜金按钮 · SaaS 卡片修辞 |

**三门禁（合并 PR 必查）：**

| 门 | 规矩 |
|----|------|
| 色彩 | 纸 `#f5f0e6` + 内容白 `#fffaf5` + 铜 KPI/CTA（<8%）+ 朱左线（≤3 处） |
| 布局 | 一屏一锚 · 无旧 `PageHead` 组件 · 用 `VolumeHead` · 375px 无页级横滚 |
| 内容 | 推断默认折叠 · 卷五不在八字深读 · 卷六不自动 LLM · 无 `classic_id` 不标典籍 |

```powershell
rg "linear-gradient|PageHead|#334155|-ok-bg|四维分析" frontend/src
# 白名单外应为 0
```

**防丑五问（DS 15 格全「是」）：**

1. 首屏只有一个视觉主角？  
2. 只有纸 + 内容白两级底？  
3. 铜色只在 1 CTA + KPI + active 导航？  
4. 首屏是数字/盘面而非大段叙述？  
5. 遮住中文标题仍能认出浮生？  

签字表 → [`reports/R079-anti-slop-five-questions-2026-07-12.md`](reports/R079-anti-slop-five-questions-2026-07-12.md)

### 2.4 Cursor Agent 规矩（自动加载）

| 规则文件 | 内容 |
|----------|------|
| `.cursor/rules/01-chinese-communication.mdc` | 中文交流 |
| `.cursor/rules/02-frontend-tooling.mdc` | Trust 单源 · Token · 改完跑 test · 复用 fusheng 组件 |

**Agent 必须：**

1. 样式/Token → 读 `variables.css`；改色提醒刷新或 Live Server 预览  
2. API 类型 → `schema.d.ts`；后端 schema 变 → `sync-frontend-types`  
3. Trust 层 → 只用 `useEngineTrustDisplay` + `buildEngineTrustDisplay.ts`  
4. 组件 → 复用 `components/fusheng/*`  
5. 测试 → 改 fusheng 组件跑 `npm run test`；改主路径提 E2E  

**对话模板：**

```text
按 INTEGRATED §五 F4 改 ReportView 卷五折叠；改完跑 frontend:test 和 test:e2e fusheng-report
@docs/plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md @frontend/src/views/ReportView.vue
```

详见 [`guides/CURSOR-AGENT-USAGE.md`](guides/CURSOR-AGENT-USAGE.md) · [`guides/CURSOR-BAZI-ZIWEI-PLAYBOOK.md`](guides/CURSOR-BAZI-ZIWEI-PLAYBOOK.md)

### 2.5 内容三层（UI 唯一语义）

| Layer | 用户文案 | provenance |
|-------|----------|------------|
| `fact` | 排盘推算 | engine |
| `cite` | 典籍依据 | classical + verified `classic_id` |
| `inference` | 经验推断 | heuristic · **默认折叠** |

---

## 三、插件与扩展（完整清单）

### 3.1 一次性安装

1. 打开 `c2/` 根目录  
2. 弹窗 **Install All Workspace Recommendations**（来源 `.vscode/extensions.json`）  
3. `Ctrl+Shift+P` → **Developer: Reload Window**  
4. `cd frontend && npm ci`

### 3.2 推荐扩展（22 个）

| 分类 | 扩展 ID | 用途 |
|------|---------|------|
| **前端核心** | `Vue.volar` | `.vue` 高亮/跳转/类型 |
| | `dbaeumer.vscode-eslint` | 保存自动 fix |
| **设计/Token** | `kamikillerto.vscode-colorize` | `variables.css` 色块预览 |
| | `naumovs.color-highlight` | 行内色预览 |
| | `phoenisx.cssvar` | `var(--brand-` 补全 |
| | `pranaygp.vscode-css-peek` | class → `fusheng-page.css` |
| **设计/样张** | `ms-vscode.live-server` | 预览 `skin-preview.html` |
| | `hediet.vscode-drawio` | `docs/design/mockups/*.drawio` |
| | `jock.svg` | Logo/矢量 |
| **文档** | `yzhang.markdown-all-in-one` | md 预览/目录 |
| | `bierner.markdown-mermaid` | mermaid 图 |
| | `bpruitt-goddard.mermaid-markdown-syntax-highlighting` | mermaid 高亮 |
| | `DavidAnson.vscode-markdownlint` | 保存时 md 检查 |
| | `Gruntfuggly.todo-tree` | 扫 `TODO:` / `DESIGN:` |
| **测试** | `vitest.explorer` | 单测侧边栏 Run |
| | `ms-playwright.playwright` | E2E 调试/Trace |
| **体验** | `usernamehw.errorlens` | 行内 TS/ESLint 错误 |
| | `yoavbls.pretty-ts-errors` | 类型错误可读化 |
| **辅助** | `PKief.material-icon-theme` | 文件树图标 |
| | `formulahendry.auto-rename-tag` | Vue 标签联动 |
| | `formulahendry.auto-close-tag` | 自动闭合标签 |
| | `oderwat.indent-rainbow` | 嵌套深度可视 |

### 3.3 禁止安装

| 扩展 ID | 原因 |
|---------|------|
| `octref.vetur` | 与 Volar 冲突 |
| `bradlc.vscode-tailwindcss` | 项目不用 Tailwind |

### 3.4 保存即生效（`.vscode/settings.json`）

| 触发 | 行为 |
|------|------|
| 保存 `.vue`/`.ts` | ESLint fix + Volar 格式化 |
| 保存 `.md` | markdownlint |
| 保存 `.py` | Ruff format + fix |
| 编辑 `variables.css` | colorize 行内色块 |
| 打开 `*.spec.ts` | Vitest 侧边栏测试树 |

### 3.5 验证扩展已就绪

```powershell
# 扩展列表（应有 volar / vitest / eslint）
cursor --list-extensions | Select-String "volar|vitest|eslint|drawio"

# Tasks 菜单应有 frontend:dev / frontend:test
# 侧边栏 Vitest 图标应列出 frontend 下 spec
```

---

## 四、VS Code / Cursor Tasks

`Ctrl+Shift+P` → **Tasks: Run Task**（定义于 `.vscode/tasks.json`）：

| Task | 命令实质 | 何时用 |
|------|----------|--------|
| `frontend:dev` | `npm run dev --prefix frontend` | 任何前端目视 |
| `backend:dev` | `scripts/ops/start-local.ps1 -Port 8000 -Reload` | 接 API/explain |
| `frontend:type-check` | `npm run type-check` | **每 PR** |
| `frontend:lint` | `npm run lint` | **每 PR** |
| `frontend:test` | `npm run test` | 改 utils/组件 |
| `frontend:e2e` | `npm run test:e2e` | F4/F6/合并前 |
| `backend:test-fast` | `make test-fast` | 后端改动 |
| `backend:lint` | `make lint` | 后端 PR |
| `backend:format` | `make format` | ruff 格式化 |

**Debug**（`.vscode/launch.json`）：`Vitest: 当前文件` · `Playwright: 当前 E2E 文件`

---

## 五、命令大全

### 5.1 环境初始化（一次性）

```powershell
# 根目录
python -m pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
python scripts/auto_verify_env.py          # 环境机读检查

cd frontend
npm ci
npm run install:e2e                        # Playwright Chromium
```

### 5.2 日常开发

```powershell
# 后端（根目录）
python -m uvicorn app.main:app --reload --port 8000
# 或 Tasks → backend:dev

# 前端
cd frontend && npm run dev
# 访问 http://localhost:5173/static/app/
```

### 5.3 前端 npm 脚本（`frontend/package.json`）

| 命令 | 用途 |
|------|------|
| `npm run dev` | Vite 开发服 |
| `npm run build` | `vue-tsc` + 生产构建 → `../static/app/` |
| `npm run preview` | 预览构建产物 |
| `npm run type-check` | `vue-tsc --noEmit` |
| `npm run lint` | ESLint |
| `npm run lint:fix` | ESLint 自动修复 |
| `npm run test` | Vitest 全量 |
| `npm run test:watch` | Vitest 监听 |
| `npm run test:e2e` | Playwright 全量 |
| `npm run install:e2e` | 安装 Playwright 浏览器 |
| `npm run test:coverage` | 覆盖率 |
| `npm run ci` | type-check + lint + test + build |
| `npm run gen:types` | OpenAPI → `src/api/schema.d.ts` |
| `npm run sync:api` | `scripts/sync_frontend_env.ps1` |

### 5.4 根目录 Make（Linux/macOS/WSL）

> Windows 无 `make` 时用 §5.5 的 `python`/`npm` 等价命令。

| Make 目标 | 用途 |
|-----------|------|
| `make dev-install` | pip + pre-commit install |
| `make lint` | ruff check + format check + pyright |
| `make format` | ruff format + fix |
| `make security` | bandit |
| `make test` | pytest（忽略 e2e/legacy） |
| `make test-fast` | pytest 并行 |
| `make scorecard` | 引擎 24 项回归 |
| `make quality-gate` | 前后端质量门 |
| `make quality-gate-backend` | 后端 smoke |
| `make quality-gate-frontend` | 前端 CI 同级 |
| `make quality-gate-full` | backend + scorecard |
| `make export-openapi` | 写 `docs/openapi.json` |
| `make sync-frontend-types` | export + `npm run gen:types` |
| `make verify-iztro` | 紫微 iztro 对照 |
| `make verify-iztro-hour` | 右弼 hour 口径 |
| `make verify-horoscope-iztro` | 运限 horoscope 对照 |
| `make verify-wenmo-horoscope` | wenmo horoscope diff |
| `make verify-wenmo-bazi` | wenmo bazi diff |
| `make capture-live-targets` | 导出 live PNG |
| `make compare-live-targets` | live vs frozen targets |
| `make auto-verify-w14` | W14 自动化 bundle |
| `make auto-verify-r103` | 预警 7 项 |
| `make auto-verify-r060` | 试读路径 |
| `make auto-verify-env` | 环境检查 |
| `make generate-r108` | 发布说明生成 |
| `make verify-volume-names` | 六卷卷名契约 |
| `make import-classics` | 典籍导入 |
| `make verify-ctext` | ctext 校验 |

### 5.5 Windows 等价命令（无 make）

```powershell
# 质量门
python scripts/audit_scorecard.py
python scripts/quality_gate.py --section backend
python scripts/quality_gate.py --section frontend   # 本地有 node_modules 时跳过 npm ci
python scripts/quality_gate.py --section backend --with-scorecard

# OpenAPI
python scripts/export_openapi.py
cd frontend && npm run gen:types

# W14 / 预警 / 发布
python scripts/auto_verify_w14.py
python scripts/auto_verify_r103.py
python scripts/auto_verify_r060.py
python scripts/auto_verify_env.py
python scripts/generate_r108_release.py

# 设计截图
node scripts/capture-live-targets.mjs
node scripts/compare-live-targets.mjs

# 引擎对照
python scripts/wenmo_engine_diff.py --horoscope --write
node scripts/verify_ziwei_iztro.mjs

# 后端测试
python -m pytest -q --ignore=tests/e2e --ignore=tests/legacy
python -m pytest -q tests/test_openapi_sync.py
python -m pytest -q tests/test_explain_batch.py tests/test_fe_be_explain_sections.py
python -m pytest -q tests/test_life_volume_schema_contract.py tests/test_zw18_trust.py

# 后端 lint
ruff check . && ruff format --check .
```

### 5.6 合并 PR 前必跑（标准套餐）

```powershell
# ── 后端 ──
python scripts/audit_scorecard.py
python scripts/quality_gate.py --section backend
python -m pytest -q tests/test_openapi_sync.py tests/test_explain_batch.py tests/test_fe_be_explain_sections.py tests/test_life_volume_schema_contract.py

# ── 前端 ──
cd frontend
npm run type-check
npm run lint
npm run test
npm run test:e2e
npm run build

# ── 设计/债务扫描 ──
rg "linear-gradient|PageHead|#334155|-ok-bg" frontend/src
node scripts/compare-live-targets.mjs    # 需先 capture-live-targets 或 E2E targets spec
```

### 5.7 E2E 常用子集

```powershell
cd frontend
npm run test:e2e -- fusheng-flow              # 主路径
npm run test:e2e -- fusheng-bazi-ziwei        # 八字紫微
npm run test:e2e -- fusheng-report            # 报告+快照
npm run test:e2e -- fusheng-anti-slop         # 防丑结构
npm run test:e2e -- fusheng-trial-read        # R060 试读
npm run test:e2e -- fusheng-targets-screenshot
npm run test:e2e -- fusheng-responsive        # 375px
npm run test:e2e -- fusheng-life-volumes      # remote 数据源
```

### 5.8 pre-commit（本地提交钩子）

安装：`pre-commit install`（含于 `make dev-install`）

钩子：trailing-whitespace · eof · yaml · large-files · **ruff** · **ruff-format** · **bandit** · **pytest-smoke**（`quality_gate.py --section backend`）

**注意**：工作区有大量未暂存 WIP 时，smoke 可能失败 → 分批 `git add` 相关文件，或干净工作区再提交。

---

## 六、改什么 → 去哪（代码地图）

### 6.1 用户主路径

```text
/ 首页 → /profile 档案 → /new/bazi | /new/ziwei → /report（六卷+跋）
```

### 6.2 前端文件

| 要改什么 | 路径 |
|----------|------|
| 应用壳/导航 | `frontend/src/components/new/NewAppShell.vue` |
| 首页 | `frontend/src/views/new/NewHomeView.vue` |
| 档案 | `frontend/src/views/ProfileView.vue` |
| 八字 | `frontend/src/views/new/NewBaziView.vue` |
| 紫微 | `frontend/src/views/new/FushengZiweiView.vue` |
| 运限 | `frontend/src/views/new/FushengZiweiTimeline.vue` |
| 报告 | `frontend/src/views/ReportView.vue` |
| 页眉组件 | `frontend/src/components/fusheng/VolumeHead.vue`（禁止旧 `PageHead` 命名） |
| 六卷拼装 | `frontend/src/utils/buildLifeVolumes.ts` |
| FE-BE 适配 | `frontend/src/utils/feBeAdapter.ts` · `constants/feBeContract.ts` |
| Token/样式 | `frontend/src/assets/variables.css` · `fusheng-page.css` |
| API | `frontend/src/api/{bazi,ziwei,explain,life}.ts` |
| OpenAPI 类型 | `frontend/src/api/schema.d.ts`（`npm run gen:types` 生成） |

### 6.3 契约

| 契约 | 路径 |
|------|------|
| OpenAPI | `docs/openapi.json` |
| 六卷 schema | `docs/contracts/life-volume.schema.json` |
| explain 映射 | `docs/contracts/explain-section-map.json` |
| FE-BE 15 题 | `docs/plan/FE-BE-DECISIONS.md` |

### 6.4 环境变量

| 变量 | 作用 |
|------|------|
| `VITE_DEV_API_TARGET` | 开发 API 代理（默认 `http://127.0.0.1:8000`） |
| `VITE_USE_LIFE_VOLUMES_API=true` | 报告强制走 `GET /life/volumes` |
| `SECRET_KEY` | 后端启动必填（弱密钥会拒绝启动） |
| `LOG_LEVEL` / `LOG_FORMAT` | 结构化日志 |

---

## 七、按场景速查

| 场景 | 步骤 |
|------|------|
| **新人第一天** | §一开工 → §三装扩展 → §5.2 跑双端 → 读 [`DEVELOPMENT.md`](DEVELOPMENT.md) §三阶段 |
| **改 UI/Token** | MASTERPLAN + skin-preview → `variables.css` → Vitest → rg 三门禁 → E2E anti-slop |
| **改 API/类型** | 改 router/schema → `export_openapi` → `gen:types` → `test_openapi_sync` |
| **改报告六卷** | `buildLifeVolumes.ts` + `ReportView.vue` → `test:e2e fusheng-report` |
| **合并 PR** | §5.6 全套 |
| **W14 收官** | `auto_verify_w14` + `auto_verify_r103` + R107 签字 → [`EXECUTION-REMAINING`](plan/FUSHENG-EXECUTION-REMAINING.md) |
| **Cursor 大改** | `@INTEGRATED` + 目标文件 + 「改完跑 frontend:test」 |

---

## 八、文档分工（本文未展开部分）

| 需求 | 文档 |
|------|------|
| **本文** | 规矩 · 命令 · 插件 · PR 门禁 |
| 进度/问题总览 | [`FUSHENG-DEV-STATUS-2026-07-13.md`](FUSHENG-DEV-STATUS-2026-07-13.md) |
| 周计划 W1–W16 | [`plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md`](plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md) |
| R001–R110 打勾 | [`plan/FUSHENG-EXECUTION-REMAINING.md`](plan/FUSHENG-EXECUTION-REMAINING.md) |
| 视觉像素定案 | [`design/FUSHENG-DESIGN-MASTERPLAN.md`](design/FUSHENG-DESIGN-MASTERPLAN.md) |
| 组件/母版详解 | [`guides/FUSHENG-FRONTEND-DEV.md`](guides/FUSHENG-FRONTEND-DEV.md) |
| 后端专章 | [`plan/BACKEND-MASTER-PLAN-2026-07-12.md`](plan/BACKEND-MASTER-PLAN-2026-07-12.md) |
| 部署 | [`guides/DEPLOYMENT-GUIDE.md`](guides/DEPLOYMENT-GUIDE.md) |

**已并入本文、勿重复扩写：** `FUSHENG-NODE-CHECKLIST` · `FUSHENG-QUICKSTART` 环境节 · `CURSOR-FRONTEND-EXTENSIONS` 安装节

---

## 九、收官人工 Gate（自动化完成后）

自动化轨已闭环（pass 4）。以下 **只能人工** 完成：

| ID | 动作 | 文档 |
|----|------|------|
| **R060** | 15 分钟试读：步骤 1–5、7、10 + 签字 | [`R060-trial-read-checklist`](reports/R060-trial-read-checklist-2026-07-12.md) |
| **R079 Q5** | 防丑五问盲测 15 格正式签字 | [`R079-anti-slop`](reports/R079-anti-slop-five-questions-2026-07-12.md) |
| **R025** | life-volume schema 三方共签 | [`R025-cosign`](reports/R025-life-volume-schema-cosign-draft-2026-07-12.md) |
| **R104 #3** | 外发卷目截图给非开发者 | [`R104-m4-share`](reports/R104-m4-share-checklist-2026-07-12.md) |
| **R105** | M5 能辩产品签字 | [`R105-m5-defend`](reports/R105-m5-defend-checklist-2026-07-12.md) |
| **R107** | 负责人 W14 收官签字 | [`R107-signoff`](reports/R107-w14-signoff-draft-2026-07-12.md) |
| **R108** | PR 附 `R108-release-notes-generated.md` + 截图 | `python scripts/generate_r108_release.py` |

**试读快速路径（R060）：**

```text
/profile 建档 → /new/bazi 速览 → /new/ziwei 方盘 → /report 六卷
卷五保持折叠 → 看跋 ≤3 行 → 主观评分 step 10
```

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| handbook-1.2 | 2026-07-13 | §九 收官人工 Gate；pass 4 试读指引 |
| handbook-1.1 | 2026-07-13 | VolumeHead 重命名；Windows quality_gate；lint 清零 |
