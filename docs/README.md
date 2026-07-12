# 文档索引

**日常开发（全自动规矩·验收）→ [`FUSHENG-DEV-PIPELINE.md`](FUSHENG-DEV-PIPELINE.md)** ⭐ · 规矩详情 → [`FUSHENG-DEV-AUTOPILOT.md`](FUSHENG-DEV-AUTOPILOT.md) · 文档地图 → [`DEVELOPMENT.md`](DEVELOPMENT.md)

`c2` 文档入口。过时材料见 [`DOCS-AUDIT.md`](DOCS-AUDIT.md) 与 [`archive/`](archive/)。

---

## 快速导航

| 我想… | 去看 |
|--------|------|
| **全自动流水线（顺序·自检·提交）** | [**`FUSHENG-DEV-PIPELINE.md`**](FUSHENG-DEV-PIPELINE.md) ⭐⭐⭐ |
| **全自动开发权威（A 表·规矩）** | [**`FUSHENG-DEV-AUTOPILOT.md`**](FUSHENG-DEV-AUTOPILOT.md) ⭐⭐ |
| **规矩·命令（旧手册）** | [`FUSHENG-DEV-HANDBOOK.md`](FUSHENG-DEV-HANDBOOK.md) |
| **文档地图 / 周计划索引** | [**`DEVELOPMENT.md`**](DEVELOPMENT.md) |
| **当前进度与问题总览** | [**`DEV-AUDIT-2026-07-13.md`**](DEV-AUDIT-2026-07-13.md) ⭐ · [STATUS 历史快照](FUSHENG-DEV-STATUS-2026-07-13.md) |
| **W5 产品重建（R102）** | UI 差距 · 内容 · 4 周 | [`reports/R102-product-rebuild-plan-2026-07-13.md`](reports/R102-product-rebuild-plan-2026-07-13.md) |
| 前后端 W1–W16 执行 | [`plan/FUSHENG-INTEGRATED-DEV-PLAN.md`](plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md) |
| **开工前就绪自检** | [**`DEV-READINESS.md`**](DEV-READINESS.md) |
| **按编号依次开发（免对话）** | [**`plan/FUSHENG-EXECUTION-PRIORITY.md`**](plan/FUSHENG-EXECUTION-PRIORITY.md) |
| 赛道 / 竞品 / 做什么 | [`plan/FUSHENG-MARKET-ENTRY-STRATEGY.md`](plan/FUSHENG-MARKET-ENTRY-STRATEGY.md) |
| 品牌与产品边界 | [`../PRODUCT.md`](../PRODUCT.md) |
| UI 定案（色·字·布局） | [`design/FUSHENG-DESIGN-MASTERPLAN.md`](design/FUSHENG-DESIGN-MASTERPLAN.md) |
| **前端开发（唯一入口）** | [**`guides/FUSHENG-FRONTEND-DEV.md`**](guides/FUSHENG-FRONTEND-DEV.md) |
| 30 分钟跑起项目 | HANDBOOK §一 · [`guides/FUSHENG-QUICKSTART.md`](guides/FUSHENG-QUICKSTART.md) |
| **开工前：节点注意 + 插件** | HANDBOOK §二–§四 · [`guides/FUSHENG-NODE-CHECKLIST.md`](guides/FUSHENG-NODE-CHECKLIST.md) |
| 后端专章 | [`plan/BACKEND-MASTER-PLAN-2026-07-12.md`](plan/BACKEND-MASTER-PLAN-2026-07-12.md) |
| **个人档案 + 关系合盘（6 类）** | [**`plan/RELATION-COMPAT-MASTER-PLAN-2026-07-13.md`**](plan/RELATION-COMPAT-MASTER-PLAN-2026-07-13.md) ⭐ |
| **合盘样例 PDF 评审（R086）** | [`reports/R086-relation-compat-sample-pdf-review-2026-07-13.md`](reports/R086-relation-compat-sample-pdf-review-2026-07-13.md) |
| API 契约 JSON | [`contracts/`](contracts/) · [`openapi.json`](openapi.json) |
| 部署 | [`guides/DEPLOYMENT-GUIDE.md`](guides/DEPLOYMENT-GUIDE.md) |
| 引擎进度 | [`reports/ENGINE-CORE-PROGRESS-2026-07-11.md`](reports/ENGINE-CORE-PROGRESS-2026-07-11.md) |

---

## 当前产品路径

```
首页 (/) → 档案 (/profile) → 八字 (/new/bazi) | 紫微 (/new/ziwei) → 报告 (/report)
```

品牌：**浮生** · 浮生若寄，知命知心

---

## 文档分层

### 执行层（日常必读）

- [`DEV-READINESS.md`](DEV-READINESS.md) — 开工前自检
- [`DEVELOPMENT.md`](DEVELOPMENT.md) — 统一入口
- [`plan/FUSHENG-EXECUTION-PRIORITY`](plan/FUSHENG-EXECUTION-PRIORITY.md) — **顺序开发 T001–T070**
- [`plan/FUSHENG-INTEGRATED-DEV-PLAN`](plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md) — 主蓝图
- [`plan/RELATION-COMPAT-MASTER-PLAN`](plan/RELATION-COMPAT-MASTER-PLAN-2026-07-13.md) — 个人摘要 + 情侣/友人/合伙等合盘
- [`reports/R086-relation-compat-sample-pdf-review`](reports/R086-relation-compat-sample-pdf-review-2026-07-13.md) — 合盘样例 PDF 评审与 P3 差距（R086）
- [`plan/FUSHENG-MARKET-ENTRY-STRATEGY`](plan/FUSHENG-MARKET-ENTRY-STRATEGY.md) — 战略

### 设计层

- [`design/FUSHENG-DESIGN-MASTERPLAN.md`](design/FUSHENG-DESIGN-MASTERPLAN.md) — v1 暖纸定案（对照）
- [**`design/FUSHENG-ART-FOUNDATION.md`**](design/FUSHENG-ART-FOUNDATION.md) — **核心美术数据 + 章法（冻结）**
- [`design/FUSHENG-MINIMAL-GUOFENG-DESIGN.md`](design/FUSHENG-MINIMAL-GUOFENG-DESIGN.md) — 简约国风定案摘要
- [**`design/FUSHENG-BRAND-LOGO-v2.md`**](design/FUSHENG-BRAND-LOGO-v2.md) — 品牌标识 v2
- [`plan/FUSHENG-ART-EXECUTION-PLAN-2026-07-13.md`](plan/FUSHENG-ART-EXECUTION-PLAN-2026-07-13.md) — 美术落地阶段规划
- [`design/FUSHENG-SONG-DESIGN-SYSTEM-v2.md`](design/FUSHENG-SONG-DESIGN-SYSTEM-v2.md) — v2 文献（视觉路线已废止）
- [`design/FUSHENG-BRAND-COPY-v1.md`](design/FUSHENG-BRAND-COPY-v1.md) — 品牌首页六卷批语
- [`design/mockups/05-home-song-target.html`](design/mockups/05-home-song-target.html) — 首页 v2 样张
- [`design/skin-preview.html`](design/skin-preview.html)
- [`design/targets/handbook-bazi-layout.md`](design/targets/handbook-bazi-layout.md)
- [`design/SONG-AESTHETICS-REFERENCES.md`](design/SONG-AESTHETICS-REFERENCES.md)

### 引擎层

- [`design/bazi/`](design/bazi/) · [`design/ziwei/`](design/ziwei/)
- [`design/api.md`](design/api.md) · [`openapi.json`](openapi.json)

### 后置（W15+ / W17+）

- [`plan/FUSHENG-BOOK-GTM-DEV-PLAN`](plan/FUSHENG-BOOK-GTM-DEV-PLAN-2026-07-12.md)
- [`plan/PLATFORM-EVOLUTION-ROADMAP`](plan/PLATFORM-EVOLUTION-ROADMAP.md)

### 运维

- [`guides/DEPLOYMENT-GUIDE.md`](guides/DEPLOYMENT-GUIDE.md)
- [`guides/BACKEND-INTEGRATION-GUIDE.md`](guides/BACKEND-INTEGRATION-GUIDE.md)
- [`guides/CURSOR-AGENT-USAGE.md`](guides/CURSOR-AGENT-USAGE.md)

---

## 归档

2026-07-12 整合：**16 份冗余开发文档** → [`archive/superseded/dev-consolidation-2026-07-12/`](archive/superseded/dev-consolidation-2026-07-12/)

| 目录 | 内容 |
|------|------|
| [`archive/superseded/`](archive/superseded/) | 旧计划、旧 SPA 矩阵 |
| [`archive/drafts/`](archive/drafts/) | txt 草稿 |
| [`archive/history/`](archive/history/) | 阶段周报 |

详见 [`DOCS-AUDIT.md`](DOCS-AUDIT.md)。
