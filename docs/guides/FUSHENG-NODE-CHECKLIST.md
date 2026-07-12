# 浮生 · 开发节点注意事项与工具清单

| 字段 | 内容 |
|------|------|
| **版本** | node-checklist-1.0 |
| **日期** | 2026-07-12 |
| **用途** | 开工前必读 — 每个节点「注意什么、用什么工具、怎么验收」 |
| **主入口** | [**`../FUSHENG-DEV-HANDBOOK.md`**](../FUSHENG-DEV-HANDBOOK.md) ⭐ 规矩·命令·插件已并入 |
| **执行蓝图** | [INTEGRATED-DEV-PLAN](../plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md) |
| **顺序清单** | [EXECUTION-REMAINING](../plan/FUSHENG-EXECUTION-REMAINING.md)（**当前主执行**） |
| **全量清单** | [EXECUTION-PRIORITY](../plan/FUSHENG-EXECUTION-PRIORITY.md) |
| **八字紫微打磨** | [BAZI-ZIWEI-POLISH-CHECKLIST](../plan/FUSHENG-BAZI-ZIWEI-POLISH-CHECKLIST.md) |
| **前端开发** | [**FUSHENG-FRONTEND-DEV**](./FUSHENG-FRONTEND-DEV.md)（环境 §3 · F 节点 §10） |
| **插件详解** | [CURSOR-FRONTEND-EXTENSIONS](./CURSOR-FRONTEND-EXTENSIONS.md) · [CURSOR-AGENT-USAGE](./CURSOR-AGENT-USAGE.md) |

> **⚠️ 环境、插件、Tasks、三门禁、PR 命令已并入 [`FUSHENG-DEV-HANDBOOK.md`](../FUSHENG-DEV-HANDBOOK.md)。** 下文节点表仍可作 F0–F6 参考；日常实操以 HANDBOOK 为准。

---

## 一、开工前：环境与插件（一次性）

### 1.1 仓库与环境

| 步骤 | 注意 | 命令 / 操作 |
|------|------|-------------|
| 打开根目录 | **必须**开 `c2/` 根，不要只开 `frontend/` | Cursor → Open Folder → `c2` |
| 信任工作区 | 不信任时扩展/Task 可能失效 | 弹窗选 **Trust Workspace** |
| 后端依赖 | Python 3.11+，虚拟环境按 README | `pip install -r requirements.txt` |
| 前端依赖 | Node 18+ | `cd frontend && npm ci` |
| Playwright 浏览器 | E2E 前必装 | `cd frontend && npm run install:e2e` |

### 1.2 Cursor / VS Code 推荐扩展（21 个）

来源：`.vscode/extensions.json`。弹窗 **Install All** 后 **Reload Window**。

| 分类 | 扩展 ID | 节点用途 |
|------|---------|----------|
| **前端核心** | `Vue.volar` | 所有 F 阶段改 `.vue` |
| | `dbaeumer.vscode-eslint` | 保存自动 fix；PR 前 lint |
| **设计 / Token** | `kamikillerto.vscode-colorize` | F1/F2 改 `variables.css` 色块预览 |
| | `naumovs.color-highlight` | 同上 |
| | `phoenisx.cssvar` | 输入 `var(--brand-` 补全 Token |
| | `pranaygp.vscode-css-peek` | 从 class 跳到 `fusheng-page.css` |
| **设计 / 样张** | `ms-vscode.live-server` | F1-6 预览 `skin-preview.html`、PDF 样稿 |
| | `hediet.vscode-drawio` | F1 线框 `docs/design/mockups/*.drawio` |
| | `jock.svg` | Logo / 矢量资源 |
| **规划 / 文档** | `yzhang.markdown-all-in-one` | 写方案、`Ctrl+Shift+V` 预览 |
| | `bierner.markdown-mermaid` | 流程图渲染 |
| | `DavidAnson.vscode-markdownlint` | 保存时 md 规范检查 |
| | `Gruntfuggly.todo-tree` | 扫 `DESIGN:` / `TODO:` / `FIXME:` |
| **测试** | `vitest.explorer` | F3–F6 单测侧边栏 |
| | `ms-playwright.playwright` | F6 E2E 调试、Trace |
| **体验** | `usernamehw.errorlens` | 行内 TS/ESLint 错误 |
| | `yoavbls.pretty-ts-errors` | 复杂类型可读化 |
| **辅助** | `PKief.material-icon-theme` | 文件树区分类型 |
| | `formulahendry.auto-rename-tag` | Vue 模板改标签 |
| | `oderwat.indent-rainbow` | 检查 DOM 嵌套过深 |

**不要装**：`octref.vetur`（与 Volar 冲突）、`bradlc.vscode-tailwindcss`（项目不用 Tailwind）。

### 1.3 终端任务（Tasks）

`Ctrl+Shift+P` → **Tasks: Run Task**：

| Task | 何时用 |
|------|--------|
| `frontend:dev` | 目视任何前端节点 |
| `backend:dev` | 接 API / explain 节点 |
| `frontend:type-check` | 每 PR |
| `frontend:test` | F3 起改 utils 必跑 |
| `frontend:lint` | 每 PR |
| `frontend:e2e` | F4/F6 |
| `backend:test-fast` | P0–P1 |
| `backend:lint` | 后端 PR |

### 1.4 仓库级命令（非扩展）

```powershell
# 根目录
make scorecard              # 引擎回归（P0+）
make sync-frontend-types    # OpenAPI 变更后（W2 起强制）
make quality-gate-frontend  # 前端 CI 同级
make quality-gate-backend   # 后端 CI 同级
make verify-iztro           # 紫微 iztro 对照（P2+）

# frontend
cd frontend
npm run dev
npm run type-check && npm run lint && npm run test && npm run test:e2e && npm run build
npm run gen:types           # 从 openapi 生成 schema.d.ts
```

### 1.5 Cursor Agent 规则（自动加载）

| 规则 | 内容 |
|------|------|
| `.cursor/rules/01-chinese-communication.mdc` | 中文交流 |
| `.cursor/rules/02-frontend-tooling.mdc` | Trust 单源、Token、改完跑 test |

**对话技巧**：大改时 `@docs/plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md` + 目标文件；详见 [CURSOR-AGENT-USAGE](./CURSOR-AGENT-USAGE.md)。

---

## 二、按节点：注意事项 · 工具 · 验收

### 图：避险顺序（不可跳步）

```text
F0 文档门禁
  → F1-6 skin 真源 + F1-7 三截图
    → F2 三页视觉达标
      → F3 buildLifeVolumes
        → F4 六卷报告
          → F5 工作台
            → F6 验收收官
```

后端并行：`P0（W1–W3）→ P1 explain（W4–W8）→ P2 内容/PDF（W9–W13）→ P3 life API（W14–W16）`

---

### 节点 0 · 开工准备（Day 0）

| 维度 | 内容 |
|------|------|
| **目标** | 环境、扩展、契约可读 |
| **注意** | 三套真源（MASTERPLAN / skin-preview / 代码）仍分裂 — **禁止**直接开 Report 大重构 |
| **必读** | `DEVELOPMENT.md` · `INTEGRATED §〇–§三` · `FE-BE-DECISIONS` · `RISK-ALERT §一` |
| **插件** | 扩展 Install All · Todo Tree 扫遗留 TODO |
| **验收** | `frontend:dev` + `backend:dev` 能打开 `/` 和 `/new/bazi` |

---

### 节点 F0 · 文档与门禁（W1，2–3 天）

| ID | 注意 | 工具 | 验收 |
|----|------|------|------|
| F0-1 | 只认 INTEGRATED 为执行权威；勿扩写已归档文档 | Markdown 预览 | 引用链无死链 |
| F0-2 | QUICKSTART 30 分钟路径 | — | 新人能跟跑 |
| F0-3 | 15 题 FE-BE 已决议，**不得**再开新接口争论 | `FE-BE-DECISIONS.md` | Q1–Q15 有负责人 |
| F0-4 | `life-volume.ts` 对齐 `life-volume.schema.json` | `gen:types` 或手写 | type-check 过 |
| F0-5 | **R-01~R-05** 写入 PR 自检习惯 | RISK-ALERT | 团队知晓三门禁 |

**节点出口**：契约 JSON 双方读过；FE-BE 无开放题。

---

### 节点 F1 · 设计真源（W1–W2）

| ID | 注意 | 插件 / 工具 | 验收 |
|----|------|-------------|------|
| F1-6 | **最高优先级** — 重写 `skin-preview.html`：去 Inter/Noto、去绿黄 alert、去 gradient；hex/字体与 `variables.css` + MASTERPLAN **逐字一致** | Live Server · colorize · cssvar | 与 MASTERPLAN §二色板对照表全匹配 |
| F1-7 | 冻结三截图：`targets/bazi.png` · `ziwei.png` · `report-toc.png` | 浏览器截图 · Playwright screenshot（F6 预埋） | 设计负责人签字；**防丑五问**初验 |
| F1-1 | skin §09 六卷 + §10 字体 A/B 页 | Live Server | 卷目 IA 与 INTEGRATED F4 表一致 |
| F1-2/3 | 补 `handbook-report-layout.md` · `handbook-ziwei-layout.md` | Draw.io · Markdown | 像素目标可评审 |
| F1-4/5 | ZhiSong 子集 `public/fonts/`；**S0.5 签字前不得标 S2「字体完成」** | 浏览器 Network 查 font 加载 | display 栈实载 |

**严禁**：
- 用旧 skin-preview（Inter/alert）作验收标准
- 未 F1-6 就合并 F4 Report 重构（翻车概率 >80%）

**节点出口**：三套真源中 skin-preview 与 MASTERPLAN 对齐；三截图冻结。

---

### 节点 F2 · 视觉债务清理（W2–W3）

| 注意 | 涉及文件 | 插件 | 验收 |
|------|----------|------|------|
| 删 **PageHead** — 壳有篇题则内页无大标题 | `FushengZiweiView`, `ProfileView`, `FushengZiweiTimeline`, extensions/* | Volar · CSS Peek | R-01 首屏无叠 4–5 层 |
| 去 **linear-gradient** 方盘/进度条 | `FushengZiweiPlate`, `ProfileReadinessCard`, `FlowProgress` | colorize | R-02 无铜金渐变 |
| 去 `--trust-ok-bg` 等语义色铺底 | `variables.css` | cssvar | 纸面仅两级 `#f5f0e6`→`#fffaf5` |
| skeleton 改暖灰 | `variables.css` | — | 无冷灰 `#e2e8f0` |
| 扩展页统一 `fs-card` | `ExtensionHubView` 等 | — | 可砍美化，不可留 PageHead |

**三门禁（三页必过）**：八字 `/new/bazi` · 紫微 `/new/ziwei` · 报告卷目壳 `/report`

```powershell
rg "linear-gradient|PageHead|#334155|-ok-bg" frontend/src
# 白名单外应为 0
```

**防丑五问**（全「是」才可进 F3）：
1. 首屏只有一个视觉主角？
2. 只有纸 + 内容白两级底？
3. 铜色只在 1 CTA + KPI + active 导航？
4. 首屏是数字/盘面而非大段叙述？
5. 遮住中文标题后仍能认出浮生？

**节点出口**：M1「能看」达标；375px 三页无页级横滚。

---

### 节点 F3 · 六卷数据层（W3–W5）

| 新建 / 改造 | 注意 | 工具 | 验收 |
|-------------|------|------|------|
| `buildLifeVolumes.ts` | **Adapter** 输出 life-volume@1.0；W16 前不依赖 GET API | Vitest · type-check | fixture 对齐 schema |
| `VolumeSection.vue` | 卷节通用；`layer` 用 fact/cite/inference | Volar | 单测空态/缺失态 |
| `ColophonFootnote.vue` | 跋 ≤3 行可展开 | — | 不抢首屏 |
| `ReadingGuide.vue` | 卷首导读 | — | 对接 explain `reading`（W8） |
| `useReadingProgress.ts` | 续读 **localStorage**；不扩 snapshot API（Q13） | — | 刷新后恢复卷位 |
| `api/explain.ts` | batch 封装 ≤4 sections | backend:dev | mock 可跑 |
| `buildBaziModuleCards` | 7 域 · 80 字截断 · layer 区分 | Vitest | 深读无卷五域卡 |
| `NewBaziView` | 卷二 relations+shensha **独立块** | 浏览器 `/new/bazi` | `relations_summary` 可见 |

**内容宪法**：
- 无 `classic_id` + verified → **禁止**「典籍依据」
- `interpretation_text` 不得当首屏主内容

**并行后端**：P0 Gate · C1 schema 共签会（W3）

**节点出口**：`buildLifeVolumes` 单测绿；八字页无卷五域卡。

---

### 节点 F4 · 报告重构（W5–W8，核心）

| ID | 注意 | 工具 | 验收 |
|----|------|------|------|
| F4-1 | 删 11 章 → **卷首+六卷+跋**；先卷目壳再填内容 | Volar · Draw.io report 线框 | 无「四维分析」 |
| F4-2 | 拆 `ReportChapterNav` + `ReportBody`；ReportView <500 行目标 | indent-rainbow | 可维护 |
| F4-3 | 接 `explain/batch`；cite 仅 verified | `api/explain.ts` · backend P1 | 卷一/二/五有 layer |
| F4-4 | 卷六折叠；**关** `loadDayunNarratives` 自动加载（Q8） | Vitest | mount 不调 LLM |
| F4-5/9 | 跋 iztro + **wenmo advisory**；degraded **必显** | EngineTrustPanel 模式 | ZW18 case 目视 |
| F4-6 | disclaimer 展示 | — | 卷首或跋可见 |
| F4-7 | `report-print.css` 六卷 | Live Server pdf-template | 打印 Trust 展开 |
| F4-8 | E2E 更新 | Playwright | 六卷 DOM 存在 |
| F4-10 | 卷四 stars 用 `star_profiles` **reference** 层，不标典籍 | — | 无假 cite |

**请求预算（Q9）**：报告页 ≤4 HTTP（bundle + 2× batch + ziwei 或并入 bundle）

**六卷映射**（不得自创卷名）：

| id | 标签 |
|----|------|
| preface | 卷首 |
| vol1 | 卷一·命之根 |
| vol2 | 卷二·业之象 |
| vol3 | 卷三·运之波 |
| vol4 | 卷四·宫之图 |
| vol5 | 卷五·事之理 |
| vol6 | 卷六·问书 |
| colophon | 跋·校勘 |

**节点出口**：**U2 试读** · **M2 能读** · **M3 能信**（15 分钟建档→报告，跋看懂 missing）

---

### 节点 F5 · 工作台对齐（W8–W11）

| 页面 | 注意 | 验收 |
|------|------|------|
| `NewHomeView` | 母版 B + ReadingGuide + 续读 | 卷首导读可见 |
| `ProfileView` | 双栏；无 PageHead | 四 Tab 口径清晰 |
| `FushengZiweiView` | 方盘 Hero；trust 横幅 | 对齐 handbook-ziwei |
| `FushengZiweiTimeline` | 卷三叙事主战场 | 运限分节 |
| trust degraded | 统一横幅组件（Q10：200 非 403） | ZW18 目视 |

**可砍**：扩展页美化（INTEGRATED §十一）

**节点出口**：主路径五页视觉统一；续读断点可用。

---

### 节点 F6 · 测试 / a11y / 性能（W12–W14）

| 项 | 注意 | 工具 | 验收 |
|----|------|------|------|
| Vitest | `buildLifeVolumes` fixture · layer 映射 | Vitest Explorer | 全绿 |
| Playwright | 六卷 · 折叠 · 375px · degraded · 空档案 | Playwright Trace | `test:e2e` 绿 |
| Screenshot | 三页基线 vs F1-7 targets | Playwright screenshot | diff 可接受 |
| a11y | 朱批色弱双编码 · aria · 键盘 | 手动 + axe（可选） | WCAG AA 可读 |
| perf | waterfall p95 记录 | DevTools Network | 报告 ≤4 请求 |
| OpenAPI | `gen:types` CI | `make sync-frontend-types` | PR 无 drift |

**节点出口**：INTEGRATED **§十** 产品 11 项全勾 · **M4 能传** · **M5 能辩**

---

### 节点 P0 · 后端信任与契约（W1–W3）

| ID | 注意 | 验收 |
|----|------|------|
| P0-02 | OpenAPI CI 阻断 drift | PR 跑 `export_openapi` |
| P0-06 | content_policy 拒 unverified cite | pytest |
| P0-07 | ChartSnapshot 只算一次 | 单测 |
| P0-08 | disclaimer 全覆盖 full/explain | schema 有字段 |
| P0-04/01 | trust_level · ZW18 裁决 | `test_zw18_trust` |
| P0-11 | 文墨 WM01–03 **advisory only** | 跋脚注，非 canonical |
| P0-12 | 资料导入可复现 | `test_import_desktop_content` |

**注意**：iztro/文墨 结果 **不得**覆盖引擎 canonical（PRODUCT.md 双轨原则）

**节点出口**：P0 Gate · 契约冻结会（W2）

---

### 节点 P1 · Explain Service（W4–W8）

| 注意 | 文件 | 验收 |
|------|------|------|
| batch ≤4 sections | `routers/explain.py` | 24 黄金 fixture |
| Compute 瘦身：默认无长 `interpretation_text` | bazi/ziwei full | W8 起生效（Q4） |
| MVP-20 verified 典籍 | `data/classics.json` | W8 齐 20 条（Q15） |
| star_profiles = reference 非 cite | P1-11 | 卷四不标典籍 |
| colophon wenmo 字段 | P1-13 | F4-9 可接 |
| Redis quota | 有公测则本阶段必完成 | — |

**节点出口**：explain/batch W8 前可用；MVP-20 齐。

---

### 节点 P2 · 内容 + PDF（W9–W13）

| 注意 | 验收 |
|------|------|
| verified 20%→35%；校勘 **8h/周** | cite 资格增加 |
| PDF 消费 explain | U4 PDF 内测（W12） |
| iztro horoscope 对照脚本 | advisory only |
| `evidence_chain.source_page` verified 必填（Q6） | W12 前 FE 可展示页码 |

---

### 节点 P3 · Read Model（W14–W16）

| 注意 | 验收 |
|------|------|
| `GET /life/volumes/{case_id}` | life-volume@1.0（Q1 W16） |
| FE 切 `api/life.ts` 弃 adapter | U5 |
| snippets / GTM | **W15+** 才做，打磨期禁止 |

---

## 三、跨节点门禁（每次合并 PR）

### 3.1 预警码 R-01~R-05

| 码 | 触发则 | 处理 |
|----|--------|------|
| R-01 | 首屏叠 4–5 层标题 | 删 PageHead |
| R-02 | 绿黄 alert / 三层暖色嵌套 | F2 减法 |
| R-03 | Inter/Noto 样张 | F1-6 |
| R-04 | 首屏 >80 字 interpretation | 折叠/下移 |
| R-05 | 11 章 Report / gradient 按钮 | F4/F2 |

### 3.2 阶段切换条件

| 从 → 到 | 必须满足 |
|---------|----------|
| F1 → F3 | F1-6 + F1-7 + F2 三页三门禁 |
| F3 → F4 大改 | `buildLifeVolumes` 单测绿 + schema 共签 |
| F4 → F5 | 六卷 DOM 存在 + batch 可跑 |
| 打磨期 → W15 | §十 全勾 + M3 |

### 3.3 打磨期禁止清单

锁卷 · snippets · 埋点漏斗 · 灵体四人格 · K 线首版 · 六爻大全科 · 社区合缘 · App 双端 · 出海 · 文墨全文进产品 · narrative 标典籍

---

## 四、按角色：节点 × 插件速查

| 角色 | 常驻插件 | 关键节点 |
|------|----------|----------|
| **前端** | Volar · ESLint · Vitest · Playwright · Error Lens | F2–F6 |
| **设计** | colorize · cssvar · Live Server · Draw.io | F1-6/7 · F2 防丑五问 |
| **后端** | Ruff（Python）· 终端 pytest | P0–P1 |
| **校勘** | Markdown · Todo Tree | P1 MVP-20 · P2 35% |
| **PM** | Markdown Mermaid · Todo Tree | 每周对 INTEGRATED §六 |
| **全员** | Markdown 预览 · Material Icons | F0 契约共读 |

---

## 五、战略里程碑对照（产品 KPI）

| 代号 | 周次 | 节点 | 标准 |
|------|------|------|------|
| **M1 能看** | W2–W3 | F1-7 + F2 | 三截图 + 防丑五问 |
| **M2 能读** | W8 | F4 | 15 分钟建档→报告 |
| **M3 能信** | W8 | F4-9 + P1 | 跋看懂 missing/双轨 |
| **M4 能传** | W12 | F6 | 愿截图卷目+跋 |
| **M5 能辩** | W14 | 引擎+跋 | vs ChatGPT 1 处口径 |

**M3 = 挤进窄赛道「可核对辑录」的最低条件。**

---

## 六、文档阅读顺序（按节点）

```text
开工     → 本文 §一 + QUICKSTART
F0       → FE-BE-DECISIONS + contracts/*.json
F1/F2    → DESIGN-MASTERPLAN + RISK-ALERT + skin-preview
F3/F4    → INTEGRATED §五 + life-volume.schema + explain-section-map
F4 跋    → PRODUCT.md 双轨 + ZW03/iztro 报告
F5       → handbook-bazi/ziwei-layout
F6       → INTEGRATED §十
战略对齐 → MARKET-ENTRY-STRATEGY（做什么不做什么）
后端     → BACKEND-MASTER-PLAN
```

---

## 七、修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| node-checklist-1.0 | 2026-07-12 | 初版：F0–F6 / P0–P3 / W1–W16 节点 + 21 扩展 + 门禁 |
