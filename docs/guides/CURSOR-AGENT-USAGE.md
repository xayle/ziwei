# Cursor 对话使用说明 — 功能 × 方案 × 验收

| 字段 | 内容 |
|------|------|
| **适用** | 浮生 c2 · 与 Cursor Agent 协作 |
| **更新** | 2026-07-12 |
| **相关** | [扩展说明](./CURSOR-FRONTEND-EXTENSIONS.md) · [**顺序执行**](../plan/FUSHENG-EXECUTION-PRIORITY.md) · [设计定案](../design/FUSHENG-DESIGN-MASTERPLAN.md) |

> **怎么用本文**：先查下表找到你要做的功能 → 复制「推荐对话」发给 Agent → 完成后用「验收命令」确认。

---

## 一、先搞懂三层能力

| 层级 | 是什么 | 何时生效 |
|------|--------|----------|
| **A. 自动规则** | `.cursor/rules/` | 每次对话默认加载（中文交流 + 前端工具链） |
| **B. 对话引用** | 你在消息里 @ 文档或说「按 XX 方案」 | Agent 会读对应设计/计划再动手 |
| **C. 编辑器扩展** | ESLint、Volar、Vitest 侧边栏等 | **你编辑并保存文件**时生效；Agent 不自动点 UI |

**结论**：正常聊天已带 **A**；要做对功能需补充 **B** 的引用；**C** 由你在 Cursor 里保存/跑 Task，Agent 用终端命令等价替代。

---

## 二、速查表（最常用）

| 你想做 | 推荐对话（复制即用） | 应引用的方案/文档 | 验收 |
|--------|----------------------|-------------------|------|
| **按编号依次开发** | 「执行 **EXECUTION-PRIORITY T0XX** …」 | `docs/plan/FUSHENG-EXECUTION-PRIORITY.md` | 该条验收命令 |
| 改档案页 / 双栏 KPI | 「按 **F5-2** 改 Profile，删 PageHead」 | INTEGRATED §5.8 · MASTERPLAN | `/profile` · 375px |
| 改八字页 / 卷二块 | 「按 **F3-9** 改八字页，Trust 用 EngineTrustPanel」 | MASTERPLAN · `NewBaziView.vue` | `npm run test` + `/new/bazi` |
| 改紫微页 / 方盘 Hero | 「按 **F5-3** 改紫微，去 gradient」 | MASTERPLAN · `FushengZiweiView.vue` | `/new/ziwei` |
| 改报告六卷 | 「按 **F4-1** 改 Report 六卷+跋」 | INTEGRATED §5.7 · `life-volume.schema.json` | `/report` + E2E |
| 改 skin 样张 | 「按 **T009/T010** 改 skin-preview.html」 | DESIGN-MASTERPLAN · `variables.css` | `rg` 门禁 + Live Server |
| 新增 fusheng 组件 | 「按前端工具链新增组件，复用 variables.css Token」 | `.cursor/rules/02-frontend-tooling.mdc` | `npm run test` + `type-check` |
| 接 API 新字段 | 「后端已加字段 X，按 schema.d.ts 接到 Y 页」 | `make sync-frontend-types` 后改 UI | `type-check` + 页面目视 |
| 修八字引擎算法 | 「按 **ENGINE-CORE-FIX-PLAN** 修 XX，跑 scorecard」 | `docs/plan/ENGINE-CORE-FIX-PLAN-2026-07-11.md` | `make scorecard` |
| 修紫微 / iztro 漂移 | 「查 **ZIWEI-IZTRO-DRIFT** Notes，跋 advisory」 | `docs/reports/ZIWEI-IZTRO-DRIFT-NOTES.md` | `make verify-iztro` |
| 写产品/设计文档 | 「按 MASTERPLAN 模板写 XX」 | `docs/design/` · mermaid | Markdown 预览 |
| 画线框 | 「更新 mockups/*.drawio」 | `docs/design/mockups/README.md` | Draw.io |
| 提交前全量检查 | 「跑 **quality-gate-frontend** 并修失败项」 | Makefile | `make quality-gate-frontend` |
| 部署 | 「按 **DEPLOYMENT-GUIDE** 说明部署到 XX」 | `docs/guides/DEPLOYMENT-GUIDE.md` | 按文档步骤 |
| 看页面效果 | （你自己）`Tasks: frontend:dev` | — | `http://localhost:5173` |
| E2E 测试 | 「为六卷报告写 Playwright 断言」 | F4-8 · `frontend/e2e/` | `npm run test:e2e` |

---

## 三、按功能模块 — 对话模板

### 3.1 档案 `/profile`

**涉及**：四 Tab、算法口径、右弼 preset、云端 Case/快照、缓存 invalidate。

| 子功能 | 怎么说 | 关键文件 |
|--------|--------|----------|
| Tab 结构 | 「Profile 保持四 Tab：基础/八字口径/紫微口径/云端」 | `ProfileView.vue`, `ProfileTabNav.vue` |
| 算法 preset | 「AlgoPresetBar 加 XX preset，变更后 invalidate fushengReport」 | `AlgoPresetBar.vue`, store |
| 流日规则 | 「zi_day_rule 只在八字 Tab，改完触发重算」 | `ProfileView.vue` |
| 云端 | 「Case/快照只在云端 Tab，侧栏只留摘要」 | `ProfileView.vue` |

**引用方案**：INTEGRATED §5.8 F5-2 · MASTERPLAN 母版 B

**示例对话**：
```
按 v3 档案设计，在紫微口径 Tab 增加 XXX 字段说明；
改口径后必须 invalidate 缓存。改完跑 frontend:test。
```

---

### 3.2 八字 `/new/bazi`

**涉及**：四层语法 L1–L4、Trust、刑冲/流日、AnalysisPanel 折叠。

| 子功能 | 怎么说 | 关键组件 |
|--------|--------|----------|
| Trust 层 | 「missing/provenance 只走 useEngineTrustDisplay，禁止页面内联解析」 | `EngineTrustPanel`, `buildEngineTrustDisplay.ts` |
| 结构表 | 「L2 用 BaziReferenceTable + BaziStructuralRelations」 | `NewBaziView.vue` |
| 流日 | 「L3 加/改 BaziLiuriTodayCard」 | 同上 |
| 断语分层 | 「AnalysisPanel 启发式默认折叠，加 PatternTierBadge」 | `AnalysisPanel.vue` |

**引用方案**：INTEGRATED §5.6 F3 · MASTERPLAN · `buildEngineTrustDisplay.ts`

**示例对话**：
```
按 v3 四层语法调整八字页区块顺序：摘要 → 结构 → Trust → 解释。
Trust 数据只用 buildEngineTrustDisplay。完成后 type-check + test。
```

---

### 3.3 紫微 `/new/ziwei` 与时间轴

| 子功能 | 怎么说 | 关键组件 |
|--------|--------|----------|
| 本命方盘 | 「FushengZiweiPlate + Trust + 飞星」 | `FushengZiweiView.vue` |
| 十二宫解释 | 「structured 用 PalaceAnalysisGrid」 | `PalaceAnalysisGrid.vue` |
| 格局 tier | 「classical/engine/heuristic 用 PatternTierBadge」 | `PatternTierBadge.vue` |
| Phase B 联动 | 「实现 useZiweiOverlayState：方盘 ↔ 时间轴共享日期/叠宫」 | v3 §9 Phase B |

**引用方案**：INTEGRATED §5.8 F5-3–F5-4 · `docs/design/ziwei/`

**示例对话**：
```
继续 Phase B：实现 useZiweiOverlayState，方盘选宫后时间轴同步高亮。
参考 v3 §6.4。写 composable 单测。
```

---

### 3.4 报告 `/report` 与 PDF

| 子功能 | 怎么说 | 关键组件 |
|--------|--------|----------|
| 六卷卷目 | 「按 F4-1 改六卷+跋，接 buildLifeVolumes」 | `ReportView.vue`, `VolumeSection.vue` |
| 跋 advisory | 「F4-9 展示 iztro + wenmo，degraded 必显」 | `ColophonFootnote.vue` |
| PDF 打印 | 「report-print.css 六卷不截断卷目」 | `assets/report-print.css` |
| 契约 | 「对齐 life-volume.schema.json」 | `frontend/src/types/life-volume.ts` |

**示例对话**：
```
执行 EXECUTION-PRIORITY T036：Report 卷目改六卷+跋，删旧章名。
加 Playwright 断言卷五推断默认折叠。
```

---

### 3.5 后端引擎（八字 / 紫微）

| 子功能 | 怎么说 | 验收 |
|--------|--------|------|
| 算法修复 | 「按 ENGINE-CORE-FIX-PLAN 修 {方法名}」 | `make scorecard` |
| 回归 case | 「对齐 ground_truth_cases.json 中 ZIPxx」 | `make test` / scorecard |
| iztro 双轨 | 「verify-iztro-hour 失败 case 排查」 | `make verify-iztro-hour` |
| OpenAPI 变更 | 「改 schema 后 sync 前端类型」 | `make sync-frontend-types` |

**引用方案**：
- `docs/plan/ENGINE-CORE-FIX-PLAN-2026-07-11.md`
- `docs/design/bazi/ENGINE-METHOD-REGISTRY.md`
- `docs/design/ziwei/ENGINE-METHOD-REGISTRY.md`

**示例对话**：
```
后端 bazi XX 方法结果与 GT 不一致，按 ENGINE-METHOD-REGISTRY 修算法，
更新 scorecard，并 sync 前端类型。
```

---

### 3.6 设计 / 规划 / 文档（不写代码）

| 子功能 | 怎么说 | 产出 |
|--------|--------|------|
| 新一页方案 | 「按 v3 结构写 {页面} 设计：IA + 四层 + 组件清单」 | `docs/design/` 新 md |
| 流程图 | 「用户旅程用 mermaid，我 Ctrl+Shift+V 预览」 | md 内 mermaid 块 |
| 线框 | 「更新 mockups/0X-xxx.drawio」 | `.drawio` 文件 |
| 排期 | 「把任务拆进 EXECUTION-PRIORITY T0XX」 | `docs/plan/FUSHENG-EXECUTION-PRIORITY.md` |
| Gap 审计 | 「对照 v3 §7 列前端未展示字段」 | 对话内表格 |

**示例对话**：
```
不写代码，按 v3 模板起草 Phase C 报告章设计，含 mermaid 和验收标准。
```

---

### 3.7 测试与质量

| 场景 | 怎么说 | 命令 / Task |
|------|--------|-------------|
| 单元测试 | 「改完跑 test，失败则修」 | `Tasks: frontend:test` |
| 类型 | 「type-check 必须通过」 | `Tasks: frontend:type-check` |
| Lint | 「eslint 零新增 warning」 | `Tasks: frontend:lint` |
| E2E | 「补 fusheng-flow / report 双轨 E2E」 | `Tasks: frontend:e2e` |
| CI 同级 | 「quality-gate-frontend 全绿」 | `make quality-gate-frontend` |
| 后端 | 「quality-gate-backend」 | `make quality-gate-backend` |

**示例对话**：
```
实现 XXX 后跑 make quality-gate-frontend，失败项全部修到通过。
```

---

## 四、实施分期 — 对话里怎么说

| 阶段 | 目标 | 你怎么开口 | 主文档 |
|------|------|------------|--------|
| **F1–F2** | 样张真源 + 视觉债务 | 「执行 T009/T015 skin 与 PageHead」 | EXECUTION-PRIORITY · MASTERPLAN |
| **F3–F4** | 六卷数据 + 报告 | 「执行 T025/T036 buildLifeVolumes」 | INTEGRATED §5.6–5.7 |
| **F5–F6** | 工作台 + 验收 | 「执行 T049/T056 E2E 六卷」 | INTEGRATED §十 |

---

## 五、@ 引用与附件技巧

在 Cursor 输入框里：

| 操作 | 效果 |
|------|------|
| `@docs/plan/FUSHENG-EXECUTION-PRIORITY.md` | Agent 按 T001–T070 执行 |
| `@docs/design/FUSHENG-DESIGN-MASTERPLAN.md` | 视觉定案 |
| `@frontend/src/components/fusheng/AnalysisPanel.vue` | 指定改这个文件 |
| `@PRODUCT.md` | 对齐品牌/产品边界 |
| `@docs/contracts/life-volume.schema.json` | 六卷形状 |
| 拖截图进对话 | UI 视觉对齐 / bug 描述 |

**推荐组合**：
```
@v3方案 @AnalysisPanel.vue
按 v3 断语分层规范，给 heuristic 层加默认折叠动画。改完 frontend:test。
```

---

## 六、你手动做 vs Agent 做

| 事项 | 谁做 | 怎么做 |
|------|------|--------|
| 保存自动格式化 | 你 | `Ctrl+S`（ESLint + Volar） |
| 浏览器看页面 | 你 | `Tasks: frontend:dev` → 打开本地 URL |
| Live Server 预览 HTML | 你 | 右键 `pdf-template-preview.html` |
| Draw.io 画布编辑 | 你 | 右键 `.drawio` → Draw.io Integration |
| 写/改代码 | Agent | 对话描述 + @ 文档 |
| 跑 test/lint/scorecard | Agent 或你 | 对话「跑 test」或 `Tasks: frontend:test` |
| Reload Window | 你 | 改 rules 后执行一次 |

---

## 七、默认已加载的规则（无需每次说）

| 规则文件 | 内容 |
|----------|------|
| `01-chinese-communication.mdc` | 用中文交流 |
| `02-frontend-tooling.mdc`（`alwaysApply: true`） | Token、Trust 单源、fusheng 组件复用、改完跑 test |

除非你要**覆盖**默认行为，否则不必每句都说「按前端工具链」——已全局生效。

---

## 八、常见误区

| 误区 | 实际情况 |
|------|----------|
| 「聊天 = 插件自动跑」 | 插件在你编辑时跑；Agent 用终端命令 |
| 「不说方案 Agent 也懂 v3」 | 大改最好 @ v3 或 Phase 清单，减少跑偏 |
| 「只开 frontend 文件夹」 | 应开仓库根 `c2/`，否则 Task/Vitest 路径错 |
| 「Trust 数据页面里拼」 | 违反规则，必须用 `useEngineTrustDisplay` |
| 「改后端不用 sync 类型」 | OpenAPI 变了必须 `make sync-frontend-types` |

---

## 九、一页纸备忘

```
┌─────────────────────────────────────────────────────────┐
│  浮生 Cursor 协作备忘                                    │
├─────────────────────────────────────────────────────────┤
│  顺序开发  → EXECUTION-PRIORITY T0XX                    │
│  前端 UI   → MASTERPLAN + 页面路径 + frontend:test      │
│  六卷报告  → life-volume.schema + F4                    │
│  Trust 层  → EngineTrustPanel + buildEngineTrustDisplay │
│  引擎算法  → ENGINE-CORE-FIX-PLAN + make scorecard      │
│  API 字段  → make sync-frontend-types                   │
│  提交前    → make quality-gate-frontend                 │
│  看效果    → Tasks: frontend:dev                        │
└─────────────────────────────────────────────────────────┘
```

---

## 十、变更记录

| 日期 | 说明 |
|------|------|
| 2026-07-12 | 初版：功能×方案×对话×验收对照表 |
