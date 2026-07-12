# 浮生 · 开发文档（统一入口）

| 字段 | 内容 |
|------|------|
| **版本** | dev-hub-1.3 |
| **日期** | 2026-07-13 |
| **一句话** | **算法写命盘，典籍写讲解，前端编成书；AI 只当卷六问书助手。** |
| **日常实操（规矩·命令·插件）** | [**FUSHENG-DEV-AUTOPILOT.md**](FUSHENG-DEV-AUTOPILOT.md) ⭐⭐⭐ **全自动唯一权威** |
| **规矩·命令·插件（旧）** | [`FUSHENG-DEV-HANDBOOK.md`](FUSHENG-DEV-HANDBOOK.md)（§九人工 Gate 已废止 → AUTOPILOT） |
| **开工自检** | HANDBOOK §一–§三 · [DEV-READINESS](DEV-READINESS.md)（已并入 HANDBOOK） |
| **收官自检+方案** | [**DEV-AUDIT-2026-07-13.md**](DEV-AUDIT-2026-07-13.md) ← 仓库整理与下一步 |

> **规矩 · 命令 · 插件 · 全自动验收 → 只看 [`FUSHENG-DEV-AUTOPILOT.md`](FUSHENG-DEV-AUTOPILOT.md)。** 本文负责文档地图与周计划索引。人工签字 Gate 已废止，以 `python scripts/auto_verify_autopilot.py` 为准。

---

## 一、30 秒：我该读哪份？

| 你是谁 | 读什么 | 路径 |
|--------|--------|------|
| **所有人** | **全自动开发权威** | [**FUSHENG-DEV-AUTOPILOT**](FUSHENG-DEV-AUTOPILOT.md) ⭐⭐⭐ |
| **规矩·命令（旧手册）** | 已合并至 AUTOPILOT | [FUSHENG-DEV-HANDBOOK](FUSHENG-DEV-HANDBOOK.md) |
| **文档地图** | 本文 | 你正在读 |
| **进度 / 问题 / 整理计划** | [**DEV-AUDIT-2026-07-13**](DEV-AUDIT-2026-07-13.md) ⭐ · [STATUS 历史](FUSHENG-DEV-STATUS-2026-07-13.md) |
| **研发执行（主）** | 前后端 W1–W16 周计划、任务 ID、验收 | [**INTEGRATED-DEV-PLAN**](plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md) |
| **按编号依次开发（免对话）** | T001→T070 顺序打勾 | [**EXECUTION-PRIORITY**](plan/FUSHENG-EXECUTION-PRIORITY.md) ⭐ |
| **剩余工作（免对话）** | **R001→R116 全部未完成项** | [**EXECUTION-REMAINING**](plan/FUSHENG-EXECUTION-REMAINING.md) ⭐⭐ |
| **八字紫微打磨+前端自检（免对话）** | BZ001→BZ088；细节索引 | [**BAZI-ZIWEI-POLISH-CHECKLIST**](plan/FUSHENG-BAZI-ZIWEI-POLISH-CHECKLIST.md) |
| **T070 完成后（免对话）** | T071→T140 权威化·GTM·平台 | [**EXECUTION-PRIORITY-POST-W14**](plan/FUSHENG-EXECUTION-PRIORITY-POST-W14.md)（打磨完成后再开） |
| **开工前就绪自检** | T015 前一次性检查 | [**DEV-READINESS**](DEV-READINESS.md) ⭐ |
| **产品 / PM** | 挤哪条赛道、竞品、做什么不做 | [MARKET-ENTRY-STRATEGY](plan/FUSHENG-MARKET-ENTRY-STRATEGY.md) |
| **改前端（UI / 六卷 / FE-BE）** | 前端开发唯一入口 | [**FRONTEND-DEV**](guides/FUSHENG-FRONTEND-DEV.md) ⭐ |
| **改 UI 色字母版** | 色、字、母版定案 | [DESIGN-MASTERPLAN](design/FUSHENG-DESIGN-MASTERPLAN.md) + [skin-preview](design/skin-preview.html) |
| **新人上手** | 跑项目 + 代码地图 | HANDBOOK §一 · [QUICKSTART](guides/FUSHENG-QUICKSTART.md)（→ HANDBOOK） |
| **开工前节点清单** | 每阶段注意什么、用什么插件 | HANDBOOK §二–§七 · [NODE-CHECKLIST](guides/FUSHENG-NODE-CHECKLIST.md)（→ HANDBOOK） |
| **防翻车** | 三门禁、R-01~R-05 | [INTEGRATED §5.11](plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md#511-前端落地预警risk-alert-并入) |
| **后端细节** | ChartSnapshot、explain、校勘 | [BACKEND-MASTER](plan/BACKEND-MASTER-PLAN-2026-07-12.md) |
| **接口决议** | 15 项 FE-BE | [FE-BE-DECISIONS](plan/FE-BE-DECISIONS.md) |
| **六卷 JSON** | 契约 | [life-volume.schema.json](contracts/life-volume.schema.json) · [explain-section-map.json](contracts/explain-section-map.json) |

---

## 二、文档权威分工（消除双真源）

| 内容 | 唯一权威 | 勿再扩写 |
|------|----------|----------|
| **阶段、周计划、BE+FE 任务、W14 验收** | INTEGRATED-DEV-PLAN | 旧 UNIFIED / SONG-DEV / v2–v4 前端稿 |
| **赛道、竞品、战略** | MARKET-ENTRY-STRATEGY | PRODUCT-CORRECTION 全文 |
| **视觉定案** | DESIGN-MASTERPLAN | ART-STYLE、FUSHENG-SONG §2–3 副本 |
| **前端开发全文** | FRONTEND-DEV | UI-DEV / PLAN / RISK-ALERT 已合并 |
| **前端 73 条问题台账** | [archive 附录 §四](archive/appendices/FUSHENG-FRONTEND-PLAN-full-2026-07-12.md) | 不另开新台账 |
| **预警 / 三门禁** | FRONTEND-DEV §9（门禁以 INTEGRATED §5.11 为准） | — |
| **增长 W15+** | BOOK-GTM | 打磨期禁止提前做 |
| **平台 W17+** | PLATFORM-EVOLUTION | 打磨期禁止提前做 |
| **引擎知识库** | design/bazi · design/ziwei | — |
| **API 机器可读** | openapi.json | COMPLETE-API-DOC（已归档） |
| **品牌边界** | [PRODUCT.md](../PRODUCT.md) | — |

---

## 三、阶段划分（执行共识）

| 阶段 | 周次 | 目标 | 不做 |
|------|------|------|------|
| **打磨期** | W1–W14 | 六卷可读、纸墨统一、explain 接上、trust 透明 | 锁卷、付费、埋点、snippets |
| **增长期** | W15+ | life API 权威化、GTM | — |
| **平台期** | W17+ | Engine Registry、KnowledgeStore | 打磨期严禁提前 |

**打磨期结束定义** → INTEGRATED §二、§十（报告六卷+跋、卷五折叠、三门禁、E2E 绿）。

---

## 四、用户主路径

```text
建档 → 八字(卷一) → 紫微(卷四) → 运限(卷三) → 报告(六卷+跋)
```

路由：`/` → `/profile` → `/new/bazi` | `/new/ziwei` → `/report`

---

## 五、联合架构（简图）

```text
前端  buildLifeVolumes (W3–W15) → VolumeSection / ReportView
      api/explain batch · api/life (W16+)
        ↕
后端  POST bazi/full · ziwei/full · archive-bundle
      POST bazi/ziwei explain/batch
      Content: classics@ · glossary@ · content_policy
        ↕ (W16+)
      GET /life/volumes/{case_id}
```

**内容标签宪法：** `fact`（排盘推算）· `cite`（classic_id + verified）· `inference`（经验推断，默认折叠）

---

## 六、周计划速览（详见 INTEGRATED §六）

| 周 | 焦点 | 里程碑 |
|----|------|--------|
| W1–W2 | 样张真源 + 截图门禁 + P0 | 契约冻结 |
| W3 | buildLifeVolumes | C1 schema 共签 |
| W4–W7 | explain + Report 切换 | — |
| **W8** | **六卷可读** | **U2 试读** |
| W9–W11 | 首页/紫微/运限 F5 | — |
| W12–W14 | 测试/a11y/perf | **打磨期收官** |
| W15–W16 | life/volumes 权威 | U5 · GTM 预备 |

**避险顺序：** F1-6 skin → F1-7 截图 → F2 三页 → F3 → F4 → F5 → F6（不可跳步）

---

## 七、活跃文档清单（仅这些参与日常开发）

### 7.1 计划与契约

| 文档 | 用途 |
|------|------|
| [INTEGRATED-DEV-PLAN](plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md) | ⭐ 执行蓝图 |
| [**EXECUTION-PRIORITY**](plan/FUSHENG-EXECUTION-PRIORITY.md) | ⭐ **顺序开发 T001–T070** |
| [MARKET-ENTRY-STRATEGY](plan/FUSHENG-MARKET-ENTRY-STRATEGY.md) | 赛道与竞品 |
| [BACKEND-MASTER-PLAN](plan/BACKEND-MASTER-PLAN-2026-07-12.md) | 后端专章 |
| [FE-BE-DECISIONS](plan/FE-BE-DECISIONS.md) | 协作决议 |
| [BOOK-GTM](plan/FUSHENG-BOOK-GTM-DEV-PLAN-2026-07-12.md) | W15+ |
| [PLATFORM-EVOLUTION](plan/PLATFORM-EVOLUTION-ROADMAP.md) | W17+ |
| [ENGINE-CORE-FIX-PLAN](plan/ENGINE-CORE-FIX-PLAN-2026-07-11.md) | 引擎修复（✅ 已完成） |
| [contracts/](contracts/) | JSON Schema |

### 7.2 前端

| 文档 | 用途 |
|------|------|
| [**FRONTEND-DEV**](guides/FUSHENG-FRONTEND-DEV.md) | ⭐ **前端开发唯一入口** |
| [DESIGN-MASTERPLAN](design/FUSHENG-DESIGN-MASTERPLAN.md) | 视觉定案 |
| [QUICKSTART](guides/FUSHENG-QUICKSTART.md) | 上手 |
| [**NODE-CHECKLIST**](guides/FUSHENG-NODE-CHECKLIST.md) | ⭐ 节点注意 + 插件 |
| [handbook-bazi-layout](design/targets/handbook-bazi-layout.md) | 八字像素 |
| [handbook-report-layout](design/targets/handbook-report-layout.md) | 报告六卷 |
| [handbook-ziwei-layout](design/targets/handbook-ziwei-layout.md) | 紫微方盘 |
| [targets/README](design/targets/README.md) | 截图门禁 |
| [skin-preview.html](design/skin-preview.html) | 样张 |

### 7.3 引擎与报告

| 文档 | 用途 |
|------|------|
| [bazi ENGINE-METHOD-REGISTRY](design/bazi/ENGINE-METHOD-REGISTRY.md) | 八字方法表 |
| [ziwei 知识库](design/ziwei/README.md) | 紫微知识 |
| [ENGINE-CORE-PROGRESS](reports/ENGINE-CORE-PROGRESS-2026-07-11.md) | 引擎进度 |
| [CONTENT-SOURCES](reports/CONTENT-SOURCES-INTEGRATION.md) | 资料整合 |
| [ZW03 / iztro 报告](reports/) | 交叉核验 |

### 7.4 运维（非产品计划）

| 文档 | 用途 |
|------|------|
| [DEPLOYMENT-GUIDE](guides/DEPLOYMENT-GUIDE.md) | 部署 |
| [BACKEND-INTEGRATION-GUIDE](guides/BACKEND-INTEGRATION-GUIDE.md) | 接入 |
| [CURSOR-AGENT-USAGE](guides/CURSOR-AGENT-USAGE.md) | Agent 提示 |

---

## 八、已归档文档（2026-07-12 整合）

以下文档 **不再作为执行依据**，已移至 [`archive/superseded/dev-consolidation-2026-07-12/`](archive/superseded/dev-consolidation-2026-07-12/)：

| 原文档 | 归档原因 | 取代 |
|--------|----------|------|
| FUSHENG-UNIFIED-DEV-PLAN | 并入 INTEGRATED | INTEGRATED §四–§五 |
| PRODUCT-CORRECTION-PLAN | 痛点并入 MARKET-ENTRY + INTEGRATED | §二完成定义 |
| FUSHENG-SONG-DEVELOPMENT | 1194 行重复 | DESIGN-MASTERPLAN + INTEGRATED |
| FUSHENG-FRONTEND-HANDBOOK | 历史分拆 | QUICKSTART + INTEGRATED |
| 2026-07-11 frontend v2 | 旧方案 | DESIGN-MASTERPLAN |
| 2026-07-12 v3/v4/DEV-GUIDE | 历史审计稿 | INTEGRATED |
| FUSHENG-ART-STYLE | 美术重复 | DESIGN-MASTERPLAN |
| PRODUCT-P-ROADMAP | ✅ 已完成 | INTEGRATED W 表 |
| BAZI-ZIWEI-COMPLETION-ROADMAP | 被 INTEGRATED 覆盖 | INTEGRATED |
| PHASE-A-FRONTEND-v3-CHECKLIST | 被 F0–F6 取代 | INTEGRATED §五 |
| BACKEND-ONLY-PLAN | ✅ 结项 | BACKEND-MASTER |
| BACKEND-FOLLOWUP-DEV | 结项 | CONTENT-SOURCES 报告 |
| 9.5-TARGET / MASTER-9.5 | 双工期冲突 | INTEGRATED W1–W14 |
| PROJECT-PLAN-2026-06-15-v1.1 | 早期计划 | PRODUCT.md |

---

## 九、质量门禁（合并 PR 前）

```powershell
# 后端
make scorecard
pytest tests/test_explain_*.py

# 前端
cd frontend
npm run type-check && npm run lint && npm run test && npm run test:e2e
```

**产品：** INTEGRATED §十 全勾 · **设计：** 防丑五问全「是」 · **预警：** R-01~R-05 首屏无触发

---

## 十、修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| dev-hub-1.2 | 2026-07-13 | 增加 FUSHENG-DEV-STATUS 整合总览 |
| dev-hub-1.1 | 2026-07-12 | 增加 DEV-READINESS；handbook 三页；T009–T014 文档收口 |
| dev-hub-1.0 | 2026-07-12 | 统一入口；归档 16 份冗余开发文档 |
