# 八字 · 紫微 补全路线图（功能优先 → 设计其次）

| 字段 | 内容 |
|------|------|
| **优先级** | ① 功能补全 ② 前端设计 |
| **更新** | 2026-07-12 |
| **依据** | [v3 方案](../design/2026-07-12-fusheng-frontend-v3-trust-depth.md) · [Phase A 清单](./PHASE-A-FRONTEND-v3-CHECKLIST.md) · scorecard 24/24 |

---

## 0. 现状一句话

| 层 | 状态 | 说明 |
|----|------|------|
| **后端引擎** | ✅ 基本满配 | scorecard 24/24；`missing_fields` / `analysis_structured` 等已出 API |
| **前端展示** | 🔄 约 70% | Phase A 大部分已落地；**运限联动、部分 API 字段、E2E** 仍缺 |
| **视觉设计** | ⏳ 待 Phase B/C 后集中做 | 骨架有了，tier/响应式/PDF 打印待 polish |

**你的顺序是对的**：先把引擎已有能力**全部接到 UI**，再统一做视觉与交互设计。

---

## 第一阶段：功能补全（八字 + 紫微）

### 波次 1 — 收尾 Phase A（约 3–5 天）

> 目标：主路径 6 页「该见的都能看见」，Trust 无静默缺失。

| ID | 任务 | 现状 | 验收 |
|----|------|------|------|
| F1-01 | 报告章 `PalaceAnalysisGrid` 十二宫 | 紫微页有，报告章需核对 | 12 宫 structured 或「缺失」 |
| F1-02 | 互证章 `DualTrackTable` 固定 case | 组件有，E2E 未写 | ≥3 行 + Playwright |
| F1-03 | 档案改口径 → 全站重算 | invalidate 有，E2E 未写 | ziDayRule / 右弼 preset 断言 |
| F1-04 | `make quality-gate-frontend` | 未跑通 | CI 同级全绿 |
| F1-05 | 用神双轨 `buildYongshenDualTrackRows` | 工具函数有，Report 需核对 | Report 互证/Trust 可见 |

**推荐对话（复制即用）：**

```
@docs/plan/PHASE-A-FRONTEND-v3-CHECKLIST.md
@docs/design/2026-07-12-fusheng-frontend-v3-trust-depth.md

按路线图波次 1 收尾 Phase A：
1. 核对 Report 十二宫是否用 PalaceAnalysisGrid
2. 补 fusheng-report E2E：DualTrackTable ≥3 行
3. 补 E2E：Profile 改 zi_day_rule / 右弼 preset → 八字/紫微/报告重算
4. 跑 make quality-gate-frontend 修到全绿

Trust 只用 useEngineTrustDisplay。改完 frontend:test + e2e。
```

---

### 波次 2 — 八字深度字段（约 1 周）

> 目标：v3 §7 八字相关 API 字段 **100% 有 UI 落点**。

| API 字段 | 目标组件 | 页面 | 现状 |
|----------|----------|------|------|
| `dizhi_relations` / `kongwang` / `shensha` | `BaziStructuralRelations` | 八字/Report | ✅ 已有 |
| `liuri_liushi` | `BaziLiuriTodayCard` | 八字/Report | ✅ 已有 |
| `geju` / `yongshen` 双轨 | `DualTrackTable` + Trust | 八字/Report | 🔄 Report 核对 |
| `scoring.hidden_contrib_by_ten_god` | `BaziReferenceTable` 或独立 `HiddenStemContrib` | 八字 | 🔄 表内有，可抽组件 |
| `pillars_primary/secondary` | 副盘切换说明 | 八字 Trust | 🔄 部分有 |
| `provenance` / `missing_fields` | `EngineTrustPanel` | 全站 | ✅ 已有 |
| 大运/流年 narrative | `AnalysisPanel` | 八字 | ✅ 已有 |

| ID | 任务 | 验收 |
|----|------|------|
| F2-01 | 抽 `HiddenStemContrib.vue`（若表内展示不够清晰） | 藏干贡献十神条形/表 |
| F2-02 | 副盘 `pillars_secondary` 在 Trust 层显式对比 | 无主副盘时写「缺失」 |
| F2-03 | 流日改日期刷新（若仅 today） | 选日期 → liuri API 重拉 |
| F2-04 | Report 八字章 Trust compact 模式核对 | 打印/PDF 不丢字段 |

**推荐对话：**

```
@docs/design/2026-07-12-fusheng-frontend-v3-trust-depth.md §7
@frontend/src/views/new/NewBaziView.vue

波次 2 八字字段补全：
对照 v3 数据绑定表，列出 NewBaziView / ReportView 八字章仍未展示的 API 字段，
逐项接入（优先 HiddenStemContrib、副盘对比、流日选日期）。
禁止页面内联解析 missing。改完 test。
```

---

### 波次 3 — 紫微深度字段 + 运限（约 2 周）

> 目标：方盘、时间轴、报告 **同一套状态**；structured 十二宫全覆盖。

| API 字段 | 目标组件 | 现状 |
|----------|----------|------|
| `analysis_structured` | `PalaceAnalysisGrid` | ✅ 紫微页 |
| `patterns[].tier` / `rule_id` | `PatternTierBadge` | ✅ |
| `structural_summary` | Trust `ziweiStructural` | ✅ |
| `iztro_crosscheck` | Trust + Report 双轨表 | ✅ |
| `liuyue` / `liuri` / overlay | `FushengZiweiTimeline` | 🔄 有时间轴，未与方盘共享状态 |
| forecast / evidence | `ZiweiForecastSummary` | 🔄 部分有 |

| ID | 任务 | 验收 |
|----|------|------|
| F3-01 | `useZiweiOverlayState` composable | 方盘选宫 ↔ 时间轴高亮一致 |
| F3-02 | `TimelineDatePicker` 改日期 → overlay 刷新 | Playwright 选日期断言 |
| F3-03 | `FortuneStrip` / 完善 `YunxianSummaryStrip` | 四格运限摘要（大限/流年/流月/流日） |
| F3-04 | 飞星 Tab 与 Trust missing 联动 | 无数据显式「缺失」 |
| F3-05 | Profile 紫微「高级」折叠 20+ algo | v3 §6.2 高级 Tab 或折叠区 |
| F3-06 | 右弼 preset 后 iztro diff 提示 | AlgoPresetBar + Trust |

**推荐对话：**

```
@docs/design/2026-07-12-fusheng-frontend-v3-trust-depth.md §6.3 §6.4 §9 Phase B
@frontend/src/views/new/FushengZiweiView.vue
@frontend/src/views/new/FushengZiweiTimeline.vue

波次 3 紫微运限补全：
1. 实现 useZiweiOverlayState（方盘 ↔ 时间轴）
2. 日期选择驱动流日/叠宫刷新
3. FortuneStrip 四格运限（可基于 YunxianSummaryStrip 扩展）
4. Profile 紫微高级口径折叠区

写 composable 单测 + Playwright 时间轴用例。
```

---

### 波次 4 — 报告与互证闭环（约 1 周）

| ID | 任务 | 验收 |
|----|------|------|
| F4-01 | 互证章固定 ZIP09/21/22 + ZW03 | DualTrackTable 固定清单 |
| F4-02 | 各章 EngineTrustPanel compact/full 切换 | 用户可切换 |
| F4-03 | `classics verification_status` | 未 verified 显示「语料待核」 |
| F4-04 | PDF Trust 块打印展开 | `report-print.css` QA |

**推荐对话：**

```
@docs/reports/PDF-REPORT-CHAPTER-MAPPING.md
@frontend/src/views/ReportView.vue

波次 4 报告闭环：
互证固定双轨 case、Trust 简洁/完整切换、PDF 打印 Trust 展开。
参考 v3 Phase C。E2E + 人工 PDF 1 份。
```

---

## 第二阶段：前端设计（功能补全后再做）

> **原则**：不在字段还没接全时大改视觉，否则返工。设计阶段对齐 v3 §4、§8、mockups。

| 波次 | 内容 | 参考 |
|------|------|------|
| D1 | 四层语法区块间距、标题层级、移动 375px | v3 §3、§8 |
| D2 | tier badge 视觉（典籍/引擎/启发式）截图回归 | `PatternTierBadge`、mockups |
| D3 | 档案四 Tab 表单密度、口径变更浮条 | mockups/01-profile-tabs.drawio |
| D4 | 八字 Trust 页信息密度 | mockups/02-bazi-trust.drawio |
| D5 | 报告互证章、双栏桌面布局 | mockups/03-report-cross.drawio |
| D6 | a11y：`aria-expanded`、reduced-motion | v3 §8、PRODUCT.md |
| D7 | 品牌 Token 审计（禁紫渐变堆砌） | `variables.css`、PRODUCT 反例 |

**推荐对话（等功能波次 1–3 后再发）：**

```
@docs/design/mockups/
@PRODUCT.md
@frontend/src/assets/variables.css

功能已接完，进入设计阶段 D1–D3：
按 mockups 和 PRODUCT 反例，统一 Profile/八字/紫微 间距与层级；
375px 无横向溢出。只改 CSS/布局，不改 API 逻辑。
```

---

## 建议执行顺序（总览）

```
波次 1 Phase A 收尾 ──→ 波次 2 八字字段 ──→ 波次 3 紫微运限
         │                                      │
         └──────────────→ 波次 4 报告闭环 ←─────┘
                              │
                              ▼
                    第二阶段 D1–D7 视觉设计
```

---

## 后端还需要动吗？

**主路径八字/紫微：基本不需要。** scorecard 已满；剩余是：

- 偶发 GT / iztro 漂移 case（`make verify-iztro`）
- OpenAPI 变更后 `make sync-frontend-types`

若 UI 发现某字段 API 没有，再单独开引擎任务，参考 `ENGINE-CORE-FIX-PLAN`。

---

## 相关文档

| 文档 | 用途 |
|------|------|
| [CURSOR-AGENT-USAGE.md](../guides/CURSOR-AGENT-USAGE.md) | 对话怎么说、@ 什么 |
| [v3 信任深度方案](../design/2026-07-12-fusheng-frontend-v3-trust-depth.md) | 字段绑定、页面 spec |
| [Phase A 清单](./PHASE-A-FRONTEND-v3-CHECKLIST.md) | 任务 ID 与 Done 定义 |
| [bazi-gap-audit](../design/bazi/bazi-gap-audit.md) | 引擎已无大缺口 |
| [ziwei-gap-audit](../design/ziwei/ziwei-gap-audit.md) | 同上 |

---

## 变更记录

| 日期 | 说明 |
|------|------|
| 2026-07-12 | 初版：功能四波次 + 设计七项，对齐用户优先级 |
