# 八字 · 紫微 对话方案（后端 + 前端设计 + 插件）

| 字段 | 内容 |
|------|------|
| **适用** | 浮生 c2 · Cursor Agent 协作 |
| **更新** | 2026-07-12 |
| **相关** | [Agent 总览](./CURSOR-AGENT-USAGE.md) · [补全路线图](../plan/BAZI-ZIWEI-COMPLETION-ROADMAP.md) · [扩展说明](./CURSOR-FRONTEND-EXTENSIONS.md) |

> 本文按你的优先级：**先后端功能 → 再前端设计**。每条方案含 **推荐对话**、**@ 引用**、**插件/任务用法**、**验收命令**。

---

## 插件与任务速查（四条线共用）

### A. 对话里 Agent 自动做的

| 动作 | 触发说法 | 实际执行 |
|------|----------|----------|
| 跑后端测试 | 「跑 pytest / scorecard」 | 终端 `make test` / `make scorecard` |
| 跑前端测试 | 「改完 frontend:test」 | `Tasks: frontend:test` 或 `npm run test` |
| 同步 API 类型 | 「sync 前端类型」 | `make sync-frontend-types` |
| 读引擎注册表 | @ `ENGINE-METHOD-REGISTRY.md` | Agent 读文档再改代码 |

### B. 你需要在 Cursor 里用的插件

| 插件 | 何时用 | 操作 |
|------|--------|------|
| **Python + Ruff** | 改 `.py` 后 | `Ctrl+S` 自动 format/fix（settings 已配） |
| **ESLint + Volar** | 改 `.vue/.ts` 后 | `Ctrl+S` 自动 fix + 格式化 |
| **Vitest** | 看/跑单测 | 侧边栏 Testing 图标；或 `Tasks: frontend:test` |
| **Playwright** | E2E | `Tasks: frontend:e2e`；Debug → `Playwright: 当前 E2E 文件` |
| **Error Lens** | 改代码时 | 行内直接看 TS/ESLint 报错 |
| **Draw.io** | 前端设计评审 | 右键 `docs/design/mockups/*.drawio` → Open With Draw.io |
| **Mermaid + Markdown** | 看方案/写设计 | `Ctrl+Shift+V` 预览 md |
| **colorize + CSS Var** | 调前端色/Token | 编辑 `variables.css` / `.vue` 时行内色块 |
| **Live Server** | 预览 HTML 样稿 | 右键 `pdf-template-preview.html` → Live Server |
| **Todo Tree** | 扫 DESIGN/TODO | 侧边栏 Todo Tree |

### C. VS Code / Cursor Tasks（`Ctrl+Shift+P` → Tasks: Run Task）

| Task | 用途 |
|------|------|
| `backend:dev` | FastAPI 本地 8000 |
| `backend:lint` | `make lint` |
| `frontend:dev` | Vite 5173 |
| `frontend:test` | Vitest |
| `frontend:lint` | ESLint |
| `frontend:e2e` | Playwright |
| `frontend:type-check` | vue-tsc |

### D. 后端 Make 命令

| 命令 | 用途 |
|------|------|
| `make scorecard` | 八字/紫微/互证 24 项评分 |
| `make test` | pytest 核心 |
| `make verify-iztro` | 紫微 vs iztro 双轨 |
| `make verify-iztro-hour` | 右弼 hour 口径 |
| `make sync-frontend-types` | OpenAPI → `schema.d.ts` |
| `make quality-gate-backend` | 后端门禁 |
| `make quality-gate-frontend` | 前端门禁 |

---

# 第一部分：后端对话方案

> **现状**：引擎主体已完成（scorecard 24/24）。后端对话多用于 **修 case、加字段、对齐 iztro、API 透传**。

---

## 1. 八字后端 — 通用模板

```
@docs/plan/ENGINE-CORE-FIX-PLAN-2026-07-11.md
@docs/design/bazi/ENGINE-METHOD-REGISTRY.md
@docs/design/bazi/bazi-gap-audit.md
@data/ground_truth_cases.json

【任务】{具体描述，如：修 GT03 格局判定 / 补 liuri_liushi 字段}

要求：
1. 只改 services/bazi_engine/ 及相关 schema/router
2. 无法实现的字段写入 missing_fields，禁止静默占位
3. 加/改 pytest 回归
4. 跑 make scorecard + make test
5. 若 API schema 变更 → make sync-frontend-types

插件：我保存 .py 时 Ruff 会自动 format；你在终端跑测试即可。
```

**关键路径**

| 模块 | 路径 |
|------|------|
| 四柱/历法 | `services/bazi_engine/pillars.py`, `solar_time_v2.py` |
| 格局/用神 | `geju.py`, `yongshen.py`, `dual_track.py` |
| 刑冲/神煞 | `relations.py`, `shensha.py` |
| 流日流时 | `liuri.py` |
| 大运流年 | `dayun.py`, `liunian.py` |
| 评分/藏干 | `scoring.py`, `strength.py` |

---

## 2. 八字后端 — 分场景对话

### 2.1 修 golden case 回归失败

```
@data/ground_truth_cases.json
@tests/test_golden_regression.py

GT{编号} 八字结果与 engine_geju 不一致。
按 bazi-gap-audit 和 ENGINE-METHOD-REGISTRY 定位根因，
修 services/bazi_engine/{模块}.py，更新测试断言。
跑 make test 和 make scorecard，确保 B-{xx} 不降分。

插件：Error Lens 看 pytest 失败行；Ruff on save 格式化补丁。
```

### 2.2 新增/补全 API 响应字段

```
@docs/design/01-schemas.md
@docs/openapi.json
@app/schemas/bazi.py

八字 API 需要暴露 {字段名}（来自 bazi_engine/{模块}）。
补 schema + router 组装 + missing_fields 逻辑。
完成后 make sync-frontend-types，并列出 frontend 该接的组件。

插件：改 schema 后 Reload Window 让 ESLint 读到新 schema.d.ts。
```

### 2.3 流日/流时 / 子时边界

```
@docs/design/bazi/ENGINE-METHOD-REGISTRY.md
@services/bazi_engine/liuri.py
@services/bazi_engine/solar_time_v2.py

修复/增强 liuri_liushi：支持 target_date、zi_day_rule 边界。
加 test_solar_zi_boundary 类用例。
跑 make test-fast 验证。

插件：Tasks: backend:dev 启动后可用 curl/Postman 打 /api/bazi 目视。
```

### 2.4 格局/用神/双轨 recorded vs engine

```
@services/bazi_engine/dual_track.py
@services/bazi_engine/geju_payload.py
@services/bazi_engine/yongshen_payload.py

对齐 recorded_geju / engine_geju 与 dual_track_note。
Regression 以 engine 为准，recorded 仅展示。
跑 test_geju_extended + scorecard B-03/B-04。

插件：make scorecard 输出可对照 docs/reports/scorecard-latest.json。
```

### 2.5 后端门禁 / 全量验收

```
按 ENGINE-CORE-FIX-PLAN 做后端验收：
make quality-gate-backend → 失败项逐项修 → 再跑 make scorecard。
不要动 frontend，除非 sync-frontend-types 需要。

插件：Tasks: backend:lint；Python 测试面板跑 pytest。
```

---

## 3. 紫微后端 — 通用模板

```
@docs/plan/ENGINE-CORE-FIX-PLAN-2026-07-11.md
@docs/design/ziwei/ENGINE-METHOD-REGISTRY.md
@docs/design/ziwei/ziwei-gap-audit.md
@docs/reports/ZIWEI-IZTRO-DRIFT-NOTES.md

【任务】{具体描述}

要求：
1. 只改 services/ziwei_engine/ 及相关 schema/router
2. Z-01~Z-05 口径以 METHOD-REGISTRY 为准；流派用请求参数暴露
3. missing_fields / engine_warnings 必显式
4. 跑 test_ziwei_engine.py + make verify-iztro
5. API 变更 → make sync-frontend-types

插件：verify-iztro 需 node；先 make verify-iztro-install。
```

**关键路径**

| 模块 | 路径 |
|------|------|
| 命宫/五行局 | `palaces.py` |
| 主星/辅煞 | `stars_main.py`, `stars_aux.py` |
| 四化 | `transforms.py` |
| 大限流年流月 | `dayun.py`, `liunian.py` |
| 流日流时 | `liuri.py`, `flow_defaults.py` |
| 格局 | `patterns.py` |
| 结构化输出 | `analysis.py`, `structural_summary.py` |
| iztro 对照 | `iztro_crosscheck.py` |
| 飞星 | `flying.py` |

---

## 4. 紫微后端 — 分场景对话

### 4.1 iztro 双轨漂移（右弼/文昌等）

```
@docs/reports/ZIWEI-IZTRO-DRIFT-NOTES.md
@scripts/verify_ziwei_iztro.mjs

case {ZIPxx} iztro 与引擎不一致。
先 make verify-iztro-hour 复现，查 stars_aux / youbi_method。
若属口径差异 → 文档标注 + iztro_crosscheck 回显；
若属 bug → 修 ziwei_engine 并更新 drift notes。

插件：终端跑 make verify-iztro；对照 JSON 报告 ziwei-iztro-diff-latest.json。
```

### 4.2 运限参数透传（flow_* / include_flow_liuri）

```
@app/schemas/ziwei.py
@services/ziwei_engine/flow_defaults.py

确认 /api/ziwei/full 透传 flow_*、include_flow_liuri、target_date。
默认 standard 与 pro 档一致。补 test_ziwei_api.py 集成测试。
sync-frontend-types。

插件：backend:dev + frontend:dev 联调时间轴请求。
```

### 4.3 analysis_structured / patterns tier

```
@services/ziwei_engine/analysis.py
@services/ziwei_engine/patterns.py

补/修 analysis_structured 逐宫字段与 patterns[].tier、rule_id、evidence_chain。
与八字侧 provenance 结构对齐。
跑 test_ziwei_engine + scorecard Z-07/Z-10。

插件：scorecard 看 Z 项；Markdown 预览 ziwei-gap-audit §4。
```

### 4.4 安星口径变更（Z-01~Z-05）

```
@docs/design/ziwei/ENGINE-METHOD-REGISTRY.md
@docs/design/ziwei/06-宫干五虎遁.md

按注册表决策修改 {Z-0x} 默认口径。
更新 METHOD-REGISTRY 决策表、ground truth、verify-iztro。
禁止静默改口径。

插件：@ 设计文档文件夹 docs/design/ziwei/ 给 Agent 完整上下文。
```

### 4.5 紫微后端全量验收

```
make quality-gate-backend
make scorecard
make verify-iztro && make verify-iztro-hour
全部通过再 sync-frontend-types。

插件：Todo Tree 扫 FIXME；Python 扩展跑 tests/ 目录。
```

---

# 第二部分：前端设计对话方案

> **前提**：后端 API 字段已齐（或已知 missing）。前端设计 = **v3 四层语法 + mockups + Token**，先功能后视觉。

---

## 5. 八字前端设计 — 通用模板

```
@docs/design/2026-07-12-fusheng-frontend-v3-trust-depth.md §6.3 §3 §4
@docs/design/mockups/02-bazi-trust.drawio
@frontend/src/assets/variables.css
@frontend/src/views/new/NewBaziView.vue
@PRODUCT.md

【设计/实现】八字页 {具体区块}

约束：
1. 四层顺序：摘要 → 结构 → Trust → 解释（§6.3）
2. Trust 只用 useEngineTrustDisplay + EngineTrustPanel
3. heuristic 默认折叠；tier 用 PatternTierBadge
4. 缺失必明示，对齐 PRODUCT 反例
5. 改完 frontend:test + type-check

插件用法：
- 我改 .vue 后 Ctrl+S → ESLint/Volar 自动格式化
- 你改完提醒我 Tasks: frontend:dev 浏览器看 /new/bazi
- 布局大改用 Draw.io 打开 02-bazi-trust.drawio 对照
- 调色时 colorize 预览 variables.css 的 --brand-* / --layer-*
```

**v3 八字页区块清单（§6.3）**

| 序号 | 区块 | 组件 | 设计要点 |
|------|------|------|----------|
| 1 | 页头 | `PageHead` + 口径 banner | precision / 真太阳时 / zi_day_rule |
| 2 | L1 摘要 | `SummaryStrip` | 日主/强弱/格局/用神/流年 |
| 3 | L2 结构 | `BaziReferenceTable` | 六柱默认展开 |
| 4 | L2 流日 | `BaziLiuriTodayCard` | 可改日期 refresh |
| 5 | L2 关系 | `BaziStructuralRelations` | 合冲刑害/空亡/神煞 |
| 6 | L2 藏干 | `HiddenStemContrib`（待抽） | 可选折叠 |
| 7 | L3 信任 | `EngineTrustPanel` compact | missing/provenance/双轨 |
| 8 | L4 解释 | `AnalysisPanel` | heuristic 折叠 |
| 9 | 大运 | dayun 叙事摘要 | 前 3 条 |

---

## 6. 八字前端 — 分场景对话

### 6.1 四层区块顺序与间距（设计阶段 D1）

```
@v3方案 §6.3
@mockups/02-bazi-trust.drawio
@fusheng-page.css
@variables.css

只做八字页视觉层级：对齐 mockups 02 的区块顺序与间距。
不动 API 逻辑。375px 无横向溢出（表格可横滑）。
prefers-reduced-motion 折叠动画降级。

插件：
- Draw.io 打开 02-bazi-trust.drawio 边改边对照
- frontend:dev → 浏览器 DevTools 375px
- colorize 检查 --layer-heuristic-bg 等着色
```

### 6.2 Trust 层设计（missing / 双轨 / provenance）

```
@EngineTrustPanel.vue
@buildEngineTrustDisplay.ts
@v3 §7 数据绑定表

设计 Trust compact 模式：missing 警示条、provenance 表、用神双轨表。
简洁|完整切换（Phase B）。aria-label 配齐。

插件：Vitest 跑 buildEngineTrustDisplay.spec.ts
Error Lens 看 TS 类型；Pretty TS Errors 读复杂报错
```

### 6.3 BaziRelations / 流日卡片

```
@BaziStructuralRelations.vue
@BaziLiuriTodayCard.vue
@v3 §6.3 线框

关系卡片空态写「暂无关系数据」；流日支持选日期局部 refresh。
对接 liuri_liushi API，禁止 mock。

插件：frontend:dev + 改 profile 后目视
Playwright 后续补选日期断言
```

### 6.4 八字报告章（Report 内嵌）

```
@ReportView.vue
@v3 §6.6
@PDF-REPORT-CHAPTER-MAPPING.md

报告八字章复用 NewBaziView 组件子集：ReferenceTable + Relations + Liuri + Trust compact。
PDF 打印 report-print.css Trust 块展开。

插件：Live Server 或 frontend:dev 打开报告 → 浏览器打印预览 PDF
```

### 6.5 八字前端验收

```
对照 v3 §6.3 Done 定义 + mockups 02：
1. 四层顺序正确
2. Trust 无静默 missing
3. heuristic 默认折叠
4. frontend:test + make quality-gate-frontend

插件：Tasks 依次 frontend:lint → frontend:test → frontend:type-check
Vitest 侧边栏点 Run 全绿
```

---

## 7. 紫微前端设计 — 通用模板

```
@docs/design/2026-07-12-fusheng-frontend-v3-trust-depth.md §6.4 §6.5 §3
@docs/design/mockups/03-report-cross.drawio
@frontend/src/views/new/FushengZiweiView.vue
@frontend/src/views/new/FushengZiweiTimeline.vue
@frontend/src/components/fusheng/FushengZiweiPlate.vue
@PRODUCT.md

【设计/实现】紫微 {本命页/时间轴/报告章}

约束：
1. 本命 §6.4 垂直顺序；时间轴 §6.5 FortuneStrip + overlay
2. patterns 必带 PatternTierBadge；summary 不作首屏主文案
3. PalaceAnalysisGrid 展示 analysis_structured
4. iztro 双轨在 Trust + Report 互证章
5. useZiweiOverlayState 方盘↔时间轴共享（Phase B）

插件：
- frontend:dev 看 /new/ziwei 和 /new/ziwei/timeline
- Draw.io：报告互证看 03-report-cross.drawio
- Playwright：时间轴选日期、overlay 高亮
- SVG Preview：若改 plate 内 SVG 图标
```

**v3 紫微本命页区块（§6.4）**

| 序号 | 区块 | 组件 |
|------|------|------|
| 1 | 页头 | `PageHead` |
| 2 | L1 摘要 | `SummaryStrip` |
| 3 | L2 方盘 | `FushengZiweiPlate` + overlay toolbar |
| 4 | 口径 | `ZiweiAlgoSettings` + `AlgoPresetBar` |
| 5 | 飞星 | `ZiweiFlyingTab` |
| 6 | L3 信任 | `EngineTrustPanel` + iztro 表 |
| 7 | L4 格局 | `AnalysisPanel` + `PatternTierBadge` |
| 8 | L4 十二宫 | `PalaceAnalysisGrid` |
| 9 | CTA | → 时间轴 / 报告 |

**v3 时间轴页（§6.5）**

| 区块 | 组件 |
|------|------|
| 日期 | `TimelineDatePicker` |
| 四格运限 | `FortuneStrip` / `YunxianSummaryStrip` |
| 方盘 | `FushengZiweiPlate` 受控 overlay |
| forecast | `ZiweiForecastSummary` |
| Trust | `EngineTrustPanel` compact |

---

## 8. 紫微前端 — 分场景对话

### 8.1 本命方盘 + 叠宫 toolbar

```
@FushengZiweiPlate.vue
@ziweiOverlay.ts
@v3 §6.4

设计叠宫 toolbar：本命/大限/流年/流月/飞星切换视觉态。
选中宫高亮、mobile 横滑。与 overlayLayer 状态绑定。

插件：frontend:dev 375px + 桌面各截图对比
indent-rainbow 读 template 嵌套层级
```

### 8.2 格局 tier + 十二宫 Grid

```
@PalaceAnalysisGrid.vue
@PatternTierBadge.vue
@AnalysisPanel.vue

patterns 每条 classical/engine/heuristic 视觉可辨；
PalaceAnalysisGrid 前 6 宫展开，其余链到报告。
空 structured 写「缺失」。

插件：Vitest phaseAComponents.spec.ts
colorize 检查 --layer-classical-* / --layer-heuristic-* token
```

### 8.3 时间轴 + FortuneStrip + 状态同步

```
@FushengZiweiTimeline.vue
@v3 §6.5
@docs/plan/BAZI-ZIWEI-COMPLETION-ROADMAP.md 波次 3

实现 useZiweiOverlayState：本命页与时间轴共享 selectedDate、overlayLayer、选中宫。
FortuneStrip 四格 scroll-snap（mobile）。

插件：
- frontend:dev 双 tab 对比方盘与时间轴
- Playwright Debug 跑 timeline spec
- Tasks: frontend:e2e
```

### 8.4 iztro 双轨 + AlgoPresetBar

```
@DualTrackTable.vue
@AlgoPresetBar.vue
@useYoubiHourAlign.ts

右弼 preset「对齐 iztro hour」一键写入 profile + invalidate。
Trust 层 iztro diff 提示。Report 互证章固定 case。

插件：backend:dev + verify-iztro-hour 结果对照 UI
Draw.io 03-report-cross 看互证章布局
```

### 8.5 Profile 紫微口径 Tab

```
@ProfileView.vue
@mockups/01-profile-tabs.drawio
@v3 §6.2

紫微口径 Tab：year_divide/day_divide/late_zishi/亮度/右弼 + AlgoPresetBar。
高级 20+ 项折叠 + API 文档链接。改口径浮条确认。

插件：Draw.io 01-profile-tabs
E2E：改 youbi → 紫微页重算
```

### 8.6 紫微报告章 + 互证

```
@ReportView.vue
@ReportZiweiChart.vue
@mockups/03-report-cross.drawio

报告紫微章：Plate 缩略 + PalaceAnalysisGrid 全 12 宫 + Trust。
互证章 DualTrackTable ZIP09/21/22 + ZW03。

插件：Live Server 打开 pdf-template-preview.html 对照 PDF 章节
frontend:e2e 互证 ≥3 行
```

### 8.7 紫微前端验收

```
v3 §6.4/§6.5 Done + mockups：
1. summary 不在首屏当主文案
2. 12 宫 structured 或缺失
3. 方盘↔时间轴状态一致（若 Phase B 已做）
4. quality-gate-frontend 全绿

插件：全 task 链 lint → type-check → test → e2e
```

---

# 第三部分：组合工作流（后端 → 前端）

## 9. 标准接力对话（推荐顺序）

### Step 1 — 后端补字段

```
@ENGINE-METHOD-REGISTRY @bazi-gap-audit（或 ziwei-gap-audit）
补 API 字段 {X}，make scorecard + sync-frontend-types。
```

**插件**：Ruff on save · `make test` · `make scorecard`

### Step 2 — 前端接字段

```
@v3 §7 数据绑定表
把 {X} 接到 {组件}，Trust 走 useEngineTrustDisplay。
frontend:test
```

**插件**：ESLint/Volar on save · Vitest · `frontend:dev`

### Step 3 — 前端设计 polish

```
@mockups @variables.css
对齐 mockups 间距与 tier 视觉，375px QA。
```

**插件**：Draw.io · colorize · Live Server · 浏览器 DevTools

### Step 4 — 门禁

```
make quality-gate-frontend
Playwright 主路径 E2E
```

**插件**：Playwright · Tasks

---

## 10. 一页纸：复制入口

| 我要… | 发这条 |
|-------|--------|
| 修八字引擎 | §2.1 模板 + GT 编号 |
| 修紫微/iztro | §4.1 模板 + ZIP 编号 |
| 八字页设计 | §6.1 或 §6 通用模板 |
| 紫微页设计 | §8.1–8.3 |
| 报告互证设计 | §6.4 + §8.6 |
| 后端→前端接力 | §9 四步 |

**打开本文**：`cursor docs/guides/CURSOR-BAZI-ZIWEI-PLAYBOOK.md`

---

## 变更记录

| 日期 | 说明 |
|------|------|
| 2026-07-12 | 初版：八字/紫微后端 5+5 场景 + 前端设计 5+7 场景 + 插件/Task 对照 |
