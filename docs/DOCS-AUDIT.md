# 文档审计与隔离说明

> **仓库整理真源（2026-07-13）** → [`DEV-AUDIT-2026-07-13.md`](DEV-AUDIT-2026-07-13.md) · 机读验收 → [`FUSHENG-DEV-AUTOPILOT.md`](FUSHENG-DEV-AUTOPILOT.md)

日期：2026-07-12（T009 文档收口）  
目的：区分「当前有用」与「已过时/草稿」，避免开发时误读旧口径。

**开发统一入口：** [`DEVELOPMENT.md`](DEVELOPMENT.md)

---

## 判断标准

| 类别 | 标准 |
|------|------|
| **当前有用** | 与 INTEGRATED-DEV-PLAN W1–W16 一致；可作为执行或契约来源 |
| **参考保留** | 引擎知识库、报告、运维指南 |
| **已归档** | 被 DEVELOPMENT 整合取代的多份「主执行」文档 |
| **草稿/样例** | `archive/drafts/`、`archive/deliverables/` |

---

## 一、当前有用（活跃文档）

### 执行与战略

| 文件 | 用途 |
|------|------|
| **`DEVELOPMENT.md`** | **统一入口** |
| **`DEV-READINESS.md`** | **开工前自检（T015 前）** |
| `plan/FUSHENG-EXECUTION-PRIORITY.md` | T001–T070 顺序清单 |
| `plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md` | 主执行 W1–W16 |
| `plan/FUSHENG-MARKET-ENTRY-STRATEGY.md` | 赛道与竞品 |
| `plan/BACKEND-MASTER-PLAN-2026-07-12.md` | 后端专章 |
| `plan/FE-BE-DECISIONS.md` | 协作决议 |
| `contracts/*.json` | 六卷 / explain 契约 |

### 设计与前端附录

| 文件 | 用途 |
|------|------|
| `design/FUSHENG-DESIGN-MASTERPLAN.md` | 视觉定案 |
| `guides/FUSHENG-FRONTEND-PLAN.md` | 73 条问题台账（附录） |
| `guides/FUSHENG-FRONTEND-RISK-ALERT.md` | 预警详版 |
| `guides/FUSHENG-QUICKSTART.md` | 上手 |
| `design/skin-preview.html` | 样张真源（T009） |
| `design/targets/*.md` · `*.png` | handbook 三页 + 截图门禁 |
| `guides/FUSHENG-NODE-CHECKLIST.md` | 节点 + 插件 |
| `guides/FUSHENG-SONG-DEVELOPMENT.md` | 停用 stub |

> **勿执行**：`archive/superseded/` 内 v3/SONG 全文；BOOK-GTM「合并来源」仅历史元数据。

### 引擎与 API

| 文件 | 用途 |
|------|------|
| `../PRODUCT.md` | 品牌边界 |
| `design/bazi/` · `design/ziwei/` | 引擎知识库 |
| `openapi.json` · `design/api.md` | API |
| `reports/ENGINE-CORE-PROGRESS-2026-07-11.md` | 引擎进度 |

### 后置（非打磨期执行）

| 文件 | 用途 |
|------|------|
| `plan/FUSHENG-BOOK-GTM-DEV-PLAN-2026-07-12.md` | W15+ |
| `plan/PLATFORM-EVOLUTION-ROADMAP.md` | W17+ |

---

## 二、2026-07-12 整合归档

路径：`archive/superseded/dev-consolidation-2026-07-12/`

| 原文档 | 取代 |
|--------|------|
| FUSHENG-UNIFIED-DEV-PLAN | INTEGRATED |
| PRODUCT-CORRECTION-PLAN | MARKET-ENTRY + INTEGRATED §二 |
| FUSHENG-SONG-DEVELOPMENT（全文） | DESIGN-MASTERPLAN + INTEGRATED |
| FUSHENG-FRONTEND-HANDBOOK | QUICKSTART + INTEGRATED |
| frontend v2 / v3 / v4 / DEV-GUIDE | DESIGN-MASTERPLAN |
| FUSHENG-ART-STYLE | DESIGN-MASTERPLAN |
| PRODUCT-P-ROADMAP · BAZI-ZIWEI-COMPLETION | INTEGRATED |
| PHASE-A-FRONTEND-v3-CHECKLIST | F0–F6 |
| BACKEND-ONLY · BACKEND-FOLLOWUP | BACKEND-MASTER · CONTENT-SOURCES |
| 9.5-TARGET · MASTER-9.5 · PROJECT-PLAN-v1.1 | INTEGRATED W1–W14 |

---

## 三、当前前端事实

```
/ → /profile → /new/bazi | /new/ziwei → /report
```

主设计：`design/FUSHENG-DESIGN-MASTERPLAN.md`  
主执行：**[`FUSHENG-DEV-PIPELINE.md`](FUSHENG-DEV-PIPELINE.md)**（W102 顺序 · dev_cycle）· [`FUSHENG-DEV-AUTOPILOT.md`](FUSHENG-DEV-AUTOPILOT.md)（A 表）· `plan/FUSHENG-EXECUTION-PRIORITY.md`（T001–T070 历史）· `plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md`（细节）

---

## 四、其他归档目录

| 目录 | 内容 |
|------|------|
| `archive/superseded/` | 旧 SPA 矩阵、重复 API 文档等 |
| `archive/drafts/` | txt 草稿 |
| `archive/history/` | 2026-02~04 周报 |
