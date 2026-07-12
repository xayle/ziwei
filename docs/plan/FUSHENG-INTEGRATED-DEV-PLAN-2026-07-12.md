# 浮生 · 前后端完整开发文档（统一执行版）

| 字段 | 内容 |
|------|------|
| **版本** | integrated-1.3 |
| **日期** | 2026-07-12 |
| **统一入口** | [**`../DEVELOPMENT.md`**](../DEVELOPMENT.md) ← 开发文档唯一导航 |
| **顺序执行** | [**`FUSHENG-EXECUTION-PRIORITY.md`**](./FUSHENG-EXECUTION-PRIORITY.md) ← **T001–T070 免对话清单** |
| **定位** | **前后端执行蓝图** — 产品打磨期（W1–W14）+ GTM 预备（W15+） |
| **合并来源** | [BACKEND-MASTER v2.2](./BACKEND-MASTER-PLAN-2026-07-12.md) · [FUSHENG-FRONTEND-PLAN](../guides/FUSHENG-FRONTEND-PLAN.md) · [FE-BE-DECISIONS](./FE-BE-DECISIONS.md) |
| **共享契约** | [`life-volume.schema.json`](../contracts/life-volume.schema.json) · [`explain-section-map.json`](../contracts/explain-section-map.json) |
| **美术权威** | [`FUSHENG-DESIGN-MASTERPLAN.md`](../design/FUSHENG-DESIGN-MASTERPLAN.md) |
| **前端预警** | [**FUSHENG-FRONTEND-RISK-ALERT**](../guides/FUSHENG-FRONTEND-RISK-ALERT.md) — **§五·§十·§十一已并入本文** |
| **资料整合** | [CONTENT-SOURCES-INTEGRATION](../reports/CONTENT-SOURCES-INTEGRATION.md) — **§8.4·附录 D** |
| **增长（后置）** | [BOOK-GTM](./FUSHENG-BOOK-GTM-DEV-PLAN-2026-07-12.md) **W15+** |
| **赛道战略** | [MARKET-ENTRY-STRATEGY](./FUSHENG-MARKET-ENTRY-STRATEGY.md) — 竞品·做什么·W 映射 |

---

## 〇、一句话与阶段划分

> **算法写命盘，典籍写讲解，前端编成书；AI 只当卷六问书助手。**

| 阶段 | 周次 | 目标 | 刻意不做 |
|------|------|------|----------|
| **打磨期** | W1–W14 | 六卷可读、纸墨统一、explain 接上、trust 透明 | 锁卷、付费墙、抖音埋点、snippets API |
| **增长期** | W15+ | life API 权威化、GTM、entitlement | — |

**打磨期铁律**（来自 [RISK-ALERT](../guides/FUSHENG-FRONTEND-RISK-ALERT.md)）：

```text
先统一真源 → 再打磨 3 页（八字/紫微/报告卷目）→ 最后才扩六卷 IA
禁止：在丑排版上贴「卷一·命之根」卷名
禁止：用 interpretation_text 长文充首屏
禁止：未过截图门禁就合并 Report 大重构
跳过 P0 皮肤统一直接做六卷 → 翻车概率 >80%
```

---

## 一、文档权威分工（消除双真源）

| 内容 | 唯一权威 |
|------|----------|
| **阶段、周计划、BE+FE 任务、验收** | **本文** |
| 后端架构细节（ChartSnapshot、SLO、RACI） | 本文 §四 + BACKEND-MASTER 附录 |
| 前端问题台账 73 条、F0–F6 文件级 | 本文 §五 + FRONTEND-PLAN 附录 |
| 色、字、母版、卷目视觉 | DESIGN-MASTERPLAN |
| 六卷 JSON 形状 | `docs/contracts/life-volume.schema.json` |
| explain section 映射 | `docs/contracts/explain-section-map.json` |
| 协作决议 | [FE-BE-DECISIONS](./FE-BE-DECISIONS.md) |
| **前端落地预警、三门禁、防丑五问** | **本文 §5.11、§十、§十一**（源：[RISK-ALERT](../guides/FUSHENG-FRONTEND-RISK-ALERT.md)） |
| **Desktop 资料/文墨整合任务** | **本文 §8.4、附录 D**（源：[CONTENT-SOURCES](../reports/CONTENT-SOURCES-INTEGRATION.md)） |

---

## 二、产品完成定义（打磨期结束 = W14）

用户路径：

```text
建档 → 八字盘面(卷一工作台) → 紫微方盘(卷四) → 运限轴(卷三) → 报告六卷连续读完 → 跋可展开校勘
```

**必须满足：**

1. 报告卷目 = **卷首 + 六卷 + 跋**（无「四维分析」旧章）
2. 卷二 **业之象** 独立呈现 `relations_summary` + `shensha_summary`
3. 卷五 **推断默认折叠**；无 verified `classic_id` **不得**标「典籍依据」
4. 卷六 **不自动**调 LLM；问书须用户点击
5. 全站 **纸墨铜朱**；无 PageHead 双标题、无铜金 gradient
6. 请求：**报告页 ≤4 次 HTTP**（bundle + 2× explain/batch + ziwei full 或并入 bundle）
7. `npm run type-check && lint && test && test:e2e` 全绿
8. 后端：explain/batch 可用 · disclaimer API · ZW18 trust · OpenAPI CI

---

## 三、联合架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端 (Vue 3)                             │
│  buildLifeVolumes (W3–W15 Adapter) → VolumeSection / ReportView │
│  api/explain.ts batch · api/life.ts (W16 切换权威)               │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP
┌────────────────────────────▼────────────────────────────────────┐
│  Compute          ChartSnapshot (内部)        Explain            │
│  POST /bazi/full  一次计算                    POST .../explain   │
│  POST /ziwei/full                             POST .../batch     │
│  archive-bundle                               content_policy     │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│  Content: classics@ · glossary@ · MVP-20 verified · 校勘 RACI      │
└─────────────────────────────────────────────────────────────────┘
                             │ P3+
┌────────────────────────────▼────────────────────────────────────┐
│  Read Model: GET /life/volumes/{case_id} → life-volume@1.0       │
└─────────────────────────────────────────────────────────────────┘
```

### 3.1 内容标签宪法（前后端强制）

| UI 文案 | 数据条件 | `layer` 字段 |
|---------|----------|--------------|
| 排盘推算 | 来自引擎字段 | `fact` |
| 典籍依据 | `classic_id` 且 verified | `cite` |
| 经验推断 | 模板/启发式 | `inference` |

**禁止：** 无 `classic_id` 使用 `cite`；`interpretation_text` 直接标典籍。

### 3.2 报告加载三阶段

| 阶段 | 周次 | 协议 |
|------|------|------|
| A | W3–W7 | `archive-bundle` + 前端 `buildLifeVolumes` |
| B | W8–W15 | bundle + **`explain/batch`** + adapter 填 cite/fact |
| C | W16+ | **`GET /life/volumes`**；废弃 adapter |

---

## 四、后端完整开发计划

> 详案：[BACKEND-MASTER-PLAN v2.2](./BACKEND-MASTER-PLAN-2026-07-12.md)

### 4.1 设计原则摘要

D1 引擎分离 · D2 Compute/Explain 分层 · D3 missing_fields · D4 verified-only citation · D5 八字/紫微分轨 guide · D7 ChartSnapshot 只算一次 · D9 disclaimer

### 4.2 Phase P0 · 信任与契约（W1–W3）

| ID | 任务 | 产出文件 | Gate |
|----|------|----------|------|
| P0-01 | ZW18 裁决 | REGISTRY Z-11, ground_truth | `test_zw18_trust` |
| P0-02 | OpenAPI CI | `.github/workflows/ci.yml` | diff 阻断 |
| P0-03 | 删 v2 501 | `routers/v2/*` | 无 501 |
| P0-04 | `trust_level` | `app/schemas/ziwei.py` | FE 契约 §十四 |
| P0-05 | Content version | `data/*.json` meta | API 返回 version |
| P0-06 | content_policy | `services/content_policy.py` | unverified 拒绝 |
| P0-07 | ChartSnapshot | `chart_snapshot_service.py` | 只算一次测试 |
| P0-08 | disclaimer_block | schemas + routers | full/explain 均有 |
| P0-09 | canonical_json | `tests/utils/canonical_json.py` | 快照基础 |
| P0-10 | metrics baseline | 结构化日志/指标 | SLO 可采 |
| P0-11 | 文墨对照轨 WM01–03 | `data/imported/wenmo_reference_cases.json` | 引擎命宫与 WM 盘 diff 可测；**advisory 非 canonical** |
| P0-12 | 资料导入可复现 | `scripts/import_desktop_content.py` | `test_import_desktop_content` 绿 |

### 4.3 Phase P1 · Explain Service（W4–W8）

**API：**

```
POST /api/v1/bazi/explain
POST /api/v1/ziwei/explain
POST /api/v1/bazi/explain/batch   # ≤4 sections
POST /api/v1/ziwei/explain/batch
```

**核心文件：**

| 路径 | 说明 |
|------|------|
| `app/schemas/explain.py` | CitationModel, ExplainedSectionModel, BatchResponse |
| `services/explain_service.py` | 编排 |
| `services/explain_bazi.py` / `explain_ziwei.py` | section 生成 |
| `services/explain_cache.py` | chart_hash + content_version |
| `routers/explain.py` | 路由 |

**Compute 瘦身：** 默认无长 `interpretation_text`；`legacy_domains=1` 至 **2026-11-01**。

**MVP-20：** P1 结束 20 条 verified 典籍齐。

**Explain 内容源（已入库）：**

| 文件 | layer | 用途 |
|------|-------|------|
| `data/ziwei/star_profiles.json` | `reference` | 卷四 stars section；**不得**标「典籍依据」 |
| `data/imported/narrative_style_samples.json` | `inference` | 六卷 prose 润色参考；content_policy 拦截 cite |
| `ziwei_classic_refs` + `classics.json` | `cite` | 仅 verified 进 UI |

| ID | 任务 | Gate |
|----|------|------|
| P1-11 | `explain_ziwei` 读 `star_profiles` | stars section 有五行/要点；trust=reference |
| P1-12 | `content_policy` 拒 narrative 标 cite | unverified 拒绝测试 |
| P1-13 | colophon `wenmo_advisory` 字段草案 | schema + explain 响应可选 |

**quota Redis：** 有公测/内测 **本阶段必完成**。

### 4.4 Phase P2 · Content + PDF（W9–W13）

| ID | 任务 |
|----|------|
| P2-01 | classics 20%→35%（校勘每周 8h） |
| P2-02 | glossary 68→120 + school_note |
| P2-03 | concepts 分轨 reading_order |
| P2-04 | B-07 宫位 REGISTRY + tiangan/shishen |
| P2-05 | Z-11 童限 / Z-12 右弼 Schema |
| P2-06 | liunian-domain 结构化 |
| P2-07 | PDF 消费 explain；HTML 快照 CI |
| P2-08 | bazi_summary + evidence_ids |
| P2-09 | iztro horoscope 对照脚本草案 | `scripts/verify_ziwei_horoscope_iztro.mjs` |
| P2-10 | 文墨 xlsx 大限/流年表 → horoscope diff | WM01 抽样；advisory only |

### 4.5 Phase P3 · Read Model + 生产（W14–W16）

| ID | 任务 |
|----|------|
| P3-01 | `GET /life/volumes/{case_id}` → life-volume@1.0 |
| P3-02 | `GET /life/snippets`（GTM 用） |
| P3-03 | liunian Redis worker |
| P3-04 | archive-bundle 扩展 name/zeri |

### 4.6 后端验收（打磨期）

- ChartSnapshot 单算 · batch explain 24 黄金 fixture · MVP-20/35% verified · disclaimer 全覆盖 · Scorecard 24/24 · OpenAPI CI 绿

---

## 五、前端完整开发计划

> 详案：[FUSHENG-FRONTEND-PLAN](../guides/FUSHENG-FRONTEND-PLAN.md)（73 条问题台账）

### 5.1 前期原则（打磨期不做）

锁卷 · snippets · 埋点漏斗 · 暗色 · H5 token · 姓名商业化 — **整段后置 W15+**

### 5.2 现状摘要（2026-07-12）

| 已落地 | 未落地（致命） |
|--------|----------------|
| NewAppShell, BaziReferenceTable, 深度三档 | Report **11 章** vs 六卷 |
| Vitest 61/61 | 无 buildLifeVolumes / VolumeSection |
| 部分纸墨 token | relations_summary 未接卷二 |

### 5.3 Phase F0 · 文档与门禁（W1，2–3 天）

| ID | 任务 | 产出 |
|----|------|------|
| F0-1 | 本文定为总纲；SONG-DEV 删重复 | 引用链 |
| F0-2 | QUICKSTART 30min | `FUSHENG-QUICKSTART.md` |
| F0-3 | FE-BE-DECISIONS 填表 | 15 题决议 |
| F0-4 | 契约 types | `frontend/src/types/life-volume.ts` 从 schema 生成或手写对齐 |
| F0-5 | **RISK-ALERT 并入门禁** | 本文 §5.11；PR 合并前查 R-01~R-05 |

### 5.4 Phase F1 · 设计真源（W1–W2，与 F2 并行）

| ID | 任务 |
|----|------|
| F1-1 | skin-preview §09 六卷 + §10 字体 A/B |
| F1-2 | handbook-report-layout.md（母版 C） |
| F1-3 | handbook-ziwei-layout.md |
| F1-4 | 字体子集 public/fonts |
| F1-5 | S0.5 签字门禁 |
| F1-6 | **重写 skin-preview** — 与 `variables.css` + MASTERPLAN hex/字体一致；**去 Inter、语义绿黄 alert 底、gradient** |
| F1-7 | **冻结截图门禁** — `docs/design/targets/bazi.png` · `ziwei.png` · `report-toc.png` |

**验收**：skin-preview 与 MASTERPLAN 色板 hex 一致；**不得以旧样张（Inter/alert 底）作为验收标准**。

### 5.5 Phase F2 · 视觉债务（W2–W3）

删 PageHead · 方盘去 gradient · 进度条实心铜 · 暖灰 skeleton · 加载 ZhiSong · 扩展页 fs-card · 去 `--trust-ok-bg` 等语义色铺底

**验收：**

- `rg "linear-gradient|PageHead|#334155|-ok-bg" frontend/src` 白名单外为 0
- **色彩/布局/内容三门禁**（§5.11）在八字/紫微/报告卷目三页通过
- 375px 三页无页级横滚

### 5.6 Phase F3 · 六卷数据层（W3–W5）

| 新建 | 说明 |
|------|------|
| `utils/buildLifeVolumes.ts` | **Adapter**，输出 life-volume@1.0 |
| `utils/buildColophonSummary.ts` | 跋 ≤3 行 |
| `components/fusheng/VolumeSection.vue` | 卷节通用 |
| `components/fusheng/ColophonFootnote.vue` | 跋脚注 |
| `components/fusheng/ReadingGuide.vue` | 卷首导读 |
| `composables/useReadingProgress.ts` | 续读断点 |
| `api/explain.ts` | batch 封装 |
| `api/life.ts` | mock + 未来切换 GET volumes |

**改造：**

- `buildBaziModuleCards`：layer 改 fact/cite/inference；7 域；截断 80 字
- `NewBaziView`：深读 **移除卷五域卡**；卷二 relations+shensha 独立块

**类型冻结：** 对齐 `life-volume.schema.json`；`layer` 用用户语义非 engine/heuristic。

### 5.7 Phase F4 · 报告重构（W5–W8，核心）

| ID | 任务 |
|----|------|
| F4-1 | Report 改六卷+跋；删 11 章 |
| F4-2 | 拆 ReportChapterNav + ReportBody |
| F4-3 | 接 **explain/batch** 填 vol1/2/5 cite 层 |
| F4-4 | 卷六折叠；**关** loadDayunNarratives 自动加载 |
| F4-5 | ColophonFootnote 每卷末 |
| F4-6 | disclaimer API 或静态过渡 |
| F4-7 | report-print.css 六卷 |
| F4-8 | E2E fusheng-report 更新 |
| F4-9 | 跋 `ColophonFootnote` 展示 iztro + **wenmo advisory**（degraded 必显） |
| F4-10 | 卷四读 explain `stars`（`star_profiles` reference 层）；无 verified 不标典籍 |

**六卷映射：**

| id | 标签 | 数据源 |
|----|------|--------|
| preface | 卷首 | Case + reading_guide |
| vol1 | 卷一·命之根 | bazi pillars/geju/yongshen + explain geju |
| vol2 | 卷二·业之象 | relations_summary + shensha_summary |
| vol3 | 卷三·运之波 | dayun / liunian / liuri / monthly **分节** |
| vol4 | 卷四·宫之图 | ziwei + trust_level |
| vol5 | 卷五·事之理 | domains fact+inference 折叠 |
| vol6 | 卷六·问书 | LLM 手动触发 |
| colophon | 跋·校勘 | colophon summary |

### 5.8 Phase F5 · 工作台对齐（W8–W11）

NewHomeView 母版 B + 续读 · ProfileView 双栏 · FushengZiweiView 方盘 Hero · Timeline 卷三叙事 · trust degraded 横幅（对齐 BE §十四）

### 5.9 Phase F6 · 测试/a11y/性能（W12–W14）

Vitest：buildLifeVolumes fixture 对齐 schema · Playwright 六卷/折叠/375/degraded · screenshot 基线 · a11y aria/色弱双编码 · waterfall p95 记录 · `gen:types` CI

### 5.10 前端关键文件地图

| 阶段 | 必改 |
|------|------|
| F2 | FushengZiweiView, ProfileView, variables.css, fusheng-page.css |
| F3 | buildLifeVolumes.ts, VolumeSection.vue, NewBaziView.vue, api/explain.ts |
| F4 | ReportView.vue（拆）, report-print.css, e2e/fusheng-report.spec.ts |
| F5 | NewHomeView, FushengZiweiTimeline, trust banner 组件 |
| F6 | e2e/*, utils/__tests__/* |

### 5.11 前端落地预警（RISK-ALERT 并入）

> 源文档：[FUSHENG-FRONTEND-RISK-ALERT](../guides/FUSHENG-FRONTEND-RISK-ALERT.md) · **任一 R 码首屏出现 → 该页不得标「完成」**

#### 五类翻车码

| 码 | 现象 | 当前实机风险 | 打磨期动作 |
|----|------|--------------|------------|
| **R-01** | 顶栏+PageHead+提要叠 4–5 层 | 紫微/档案/运限仍有 PageHead | F2 删 PageHead；壳有篇题则无内页大标题 |
| **R-02** | 米白套米白+绿黄 alert | `variables.css` `--trust-ok-bg` | F2 去语义色铺底；纸面仅两级 |
| **R-03** | 与国风站互换无差别 | skin-preview 仍 Inter/Noto | F1-6 重写样张；F1-7 冻结 targets |
| **R-04** | 满屏待计算/长 interpretation | buildBaziModuleCards 深读 8 域 | F3 首屏事实 KPI；推断默认折叠 |
| **R-05** | 名词国风、组件西化 | Report 11 章；gradient 按钮 | F4 六卷 IA；F2 去 gradient |

#### 三套真源（未完成前禁止扩页）

| 真源 | 状态 | 动作 |
|------|------|------|
| MASTERPLAN | ✅ 定案 | 执行不得绕过 |
| skin-preview | 🔴 与定案冲突 | F1-6 重写后方能作验收依据 |
| frontend/src | 🟡 部分对齐 | F2 三页达标后再 F4 |

#### 三门禁（合并 PR 必过）

**色彩：** 全页色相 ≤ 纸墨铜朱；纸面两级 `#f5f0e6`→`#fffaf5`；铜 &lt;8%；朱批 ≤3；小字不用铜/冷灰。

**布局：** 一屏一锚（盘面/卷封/卷目）；无双标题；间距 24/32px；375px 无横滚。

**内容：** 首屏可核对事实；推断折叠+badge「推断」；卷五域不在八字页；卷六不自动 LLM；无 verified 不标典籍。

#### 防丑五问（负责人目检，全「是」才可合并下一阶段）

1. 首屏是否只有一个视觉主角？  
2. 是否只有纸+内容白两级底？  
3. 铜色是否只在 1 CTA + KPI + active 导航？  
4. 首屏是否有数字/盘面而非大段叙述？  
5. 遮住中文标题后截图是否仍能认出浮生？  

#### 打磨期禁止（与 §5.1 叠加）

未统一样张就做 Report 六卷大重构 · 同时改 IA+全站皮肤+新组件 · 用「宋式」修辞替代视觉减法 · E2E mock 绿当作视觉过关

#### 推荐避险顺序

```text
P0  统一真源（F1-6 skin-preview）→ P0 截图门禁（F1-7）
P1  三页达标（八字/紫微/报告卷目，F2）
P2  报告 IA 卷目改名（F4-1，禁止一步到位塞内容）
P3  六卷组件（F3/F4，IA 稳定后）
```

---

## 六、联合周计划（W1–W16）

| 周 | 后端 | 前端 | 设计/校勘 | 用户里程碑 |
|----|------|------|-----------|------------|
| **W1** | P0 启动：Snapshot/disclaimer/OpenAPI；P0-12 资料导入测试 | F0+F1（含 F1-6 skin 重写启动） | skin 六卷页；S0.5 | — |
| **W2** | P0 完：ZW18/trust/content_policy；**P0-11 文墨 diff** | F1+F2 视觉；**F1-7 截图门禁** | 字体样张；**防丑五问初验** | 契约冻结会 |
| **W3** | P0 Gate | F2+F3 buildLifeVolumes | — | **C1** schema 共签 |
| **W4** | P1 explain 骨架 | F3 组件 | — | — |
| **W5** | P1 explain/batch | F3 卷二接 API | — | — |
| **W6** | P1 MVP-20；**P1-11 star_profiles** | F4 Report 卷目切换 | 校勘 8h/周起 | — |
| **W7** | P1 黄金 fixture | F4 接 batch | — | — |
| **W8** | **P1 Gate**；P1-13 colophon wenmo | **F4 六卷可读**；F4-9 跋 advisory | MVP-20 齐 | **U2 试读卷一二** |
| **W9** | P2 校勘/PDF | F5 首页/档案 | 校勘 | — |
| **W10** | P2 REGISTRY 童限 | F5 紫微/运限 | — | — |
| **W11** | P2 PDF CI | F5 trust UI | — | — |
| **W12** | P2 Gate；**P2-09 iztro horoscope** | F6 测试矩阵 | verified 35% | **U4 PDF 内测** |
| **W13** | P2 收尾；**P2-10 文墨运限** | F6 a11y/perf | — | — |
| **W14** | P3 life/volumes 开发 | F6 E2E 绿 | — | 打磨期 FE 收官 |
| **W15** | P3 Gate | 切 api/life.ts | — | — |
| **W16** | snippets/worker | 废弃 adapter | — | **U5 六卷 API 权威** |

**缓冲：** W13–W14 含 20% 延期；砍 scope 见 BACKEND-MASTER §十二、前端 F4 卷六可延后。

---

## 七、API 契约速查

### 7.1 打磨期必需端点

| 方法 | 路径 | 前端用途 | 阶段 |
|------|------|----------|------|
| POST | `/api/v1/bazi/full` | 盘面事实 | 已有 |
| POST | `/api/v1/ziwei/full` | 方盘 | 已有 |
| POST | `/api/v1/fusheng/archive-bundle` | 报告拼装 | 已有 |
| POST | `/api/v1/bazi/explain/batch` | 卷一/二/五 讲解 | P1 |
| POST | `/api/v1/ziwei/explain/batch` | 卷四 | P1 |
| GET | `/api/v1/glossary` | TermHint | 已有 |
| GET | `/life/volumes/{id}` | 报告权威 | P3 |

### 7.2 ExplainBatch 示例

```json
// POST /api/v1/bazi/explain/batch
{
  "year": 1990, "month": 1, "day": 15, "hour": 10,
  "sections": ["geju", "relations", "reading"]
}
```

### 7.3 trust_level UI（前后端共遵）

| trust_level | 卷四 | 卷三运限付费 | UI |
|-------------|------|--------------|-----|
| full | 正常 | 按 entitlement（打磨期无墙） | iztro 可折叠 |
| degraded | 展示+警告 | 打磨期仅文案 | **命宫 iztro 对照条** 必显 |

---

## 八、内容与自然语言

### 8.1 MVP-20 + 校勘 RACI

见 BACKEND-MASTER §5.3–5.4。前端 **W8 前** 卷五禁止「典籍依据」标签。

### 8.2 卷三运限分节（命理+产品）

| 节 | 内容 | 勿混 |
|----|------|------|
| 3.1 | 大运十年 | 与流年分开 |
| 3.2 | 流年 | 当前大运下 |
| 3.3 | 流月/流日 | 可选深读 |

### 8.3 文案规范

- 用户不见：L1/L4、engine、heuristic  
- 卷六 LLM 必带：「示例稿·非引擎结论」或 API disclaimer  
- 典籍格式：`《书名》·卷/章·页`（P-COPY-05 样例进 handbook）

### 8.4 Desktop 资料整合（已入库 + 待接线）

> 盘点报告：[CONTENT-SOURCES-INTEGRATION](../reports/CONTENT-SOURCES-INTEGRATION.md) · 脚本：`scripts/import_desktop_content.py`

**已入库（勿重复导入）：**

| 资产 | 路径 | trust |
|------|------|-------|
| 文墨三盘对照 | `data/imported/wenmo_reference_cases.json` | advisory |
| 十四主星档案 | `data/ziwei/star_profiles.json` | reference |
| 叙事样例 | `data/imported/narrative_style_samples.json` | inference |
| 紫微术语 +12 | `data/glossary.json` | glossary |
| 清单 | `data/imported/source_manifest.json` | meta |

**待开发（按周）：**

| 周次 | BE | FE | 验收 |
|------|----|----|------|
| W2 | P0-11 WM01–03 diff 脚本 | — | 命宫/主星 diff 可输出 |
| W6 | P1-11 explain 读 star_profiles | — | stars section 有参考文案 |
| W8 | P1-13 colophon wenmo 字段 | F4-9 跋展示 advisory | degraded 见对照脚注 |
| W12 | P2-09 iztro horoscope 脚本 | — | 大限/流年抽样 diff |
| W14 | P2-10 文墨 xlsx 运限表 | — | WM01 horoscope advisory |
| W16 | life/volumes colophon 权威 | 废弃 adapter | schema 含 `wenmo_advisory` |

**明确不做：** 文墨 docx 全文进产品 · App.swf/exe · Desktop/紫薇 旧 data 覆盖 · narrative 标典籍 · wenmo 替代引擎

---

## 九、测试与 CI 联合矩阵

| 场景 | 后端 | 前端 |
|------|------|------|
| life-volume 形状 | schema validate fixture | buildLifeVolumes 单测 |
| explain 确定性 | canonical_json 24 fixtures | — |
| citation 仅 verified | test_content_policy | VolumeSection 无假 cite |
| ZW18 trust | test_zw18_trust | E2E degraded 横幅 |
| 六卷 E2E | — | Playwright 卷目/折叠 |
| OpenAPI/types | export diff CI | gen:types CI |
| PDF | HTML 快照 | 打印六卷不截断 |
| 性能 | batch p95 ≤1200ms | 报告 waterfall ≤3s 本地 |
| 资料导入 | `test_import_desktop_content` | — |
| 文墨/iztro 对照 | P0-11 diff · P2-09 horoscope | F4-9 跋 advisory UI |
| **视觉截图门禁** | — | F1-7 targets 三页；**不替代** E2E |

---

## 十、验收清单（W14 打磨期收官）

### 10.1 自动

```powershell
# 后端
make scorecard
pytest tests/test_explain_*.py tests/test_zw18_trust.py
python scripts/export_openapi.py  # CI diff

# 前端
cd frontend
npm run type-check && npm run lint && npm run test && npm run test:e2e && npm run build
```

### 10.2 产品（必须全勾）

- [ ] 报告六卷+跋，无旧章名  
- [ ] 卷二 relations/shensha 独立  
- [ ] 卷五推断默认折叠  
- [ ] 卷六不自动 LLM  
- [ ] 跋 ≤3 行可展开  
- [ ] 首页 ReadingGuide + 续读  
- [ ] 无 PageHead；无铜金 gradient  
- [ ] 375px 主路径无页级横滚  
- [ ] explain/batch 接入报告  
- [ ] disclaimer 展示  
- [ ] ZW18 degraded UI  

### 10.3 设计目检

- [ ] skin-preview 与实页卷名一致  
- [ ] 像册页不像 SaaS  
- [ ] 铜朱预算达标  

### 10.4 前端预警门禁（RISK-ALERT，W2 起每 PR）

- [ ] **R-01~R-05** 首屏无触发（见 §5.11）  
- [ ] 色彩/布局/内容 **三门禁** 全过  
- [ ] **防丑五问** 全「是」  
- [ ] skin-preview 与 MASTERPLAN hex/字体一致（F1-6）  
- [ ] `targets/bazi.png` · `ziwei.png` · `report-toc.png` 已冻结（F1-7）  
- [ ] 首屏无 &gt;80 字 interpretation_text  
- [ ] 卷五域卡不在八字深读；卷六无自动 LLM  

**级别：** 🔴 红灯=停扩功能只做减法 · 🟡 黄灯=本 sprint 修 · 🟢 三门禁+五问全过才可进 F4 大重构

---

## 十一、风险与砍 Scope

| 风险 | 缓解 |
|------|------|
| Report 重构 E2E 大面积红 | F4 先数据层后样式 |
| 无 explain 卷五品质平 | W8 前接受；仅 fact/inference |
| buildLifeVolumes 与 API drift | schema 契约测试双端 |
| 双工期乐观 | 联合周计划 W14 收官，非 FE 8 周单独 |
| 文档再膨胀 | 执行只改本文 + 契约 JSON |
| **三套真源分裂（RISK-ALERT）** | **F1-6 先统一 skin-preview；F1-7 截图门禁；禁止未过门禁做 F4** |
| **排版/配色/AI 味（R-01~R-05）** | §5.11 三门禁 + 防丑五问；P0 只打磨三页 |
| **样张验收验回丑版** | skin-preview 重写前不得以 D2「✅」为准 |
| **文墨/iztro 当 canonical** | P0-11 advisory only；跋脚注，不覆盖引擎 |
| **narrative 误标典籍** | P1-12 content_policy + FE 无 classic_id 不渲染 cite |

**后端砍序：** 见 BACKEND-MASTER §十二  
**前端可砍：** F5 扩展页美化 · F6 screenshot 部分页

**一句话备忘（RISK-ALERT）：** 浮生好看不靠「宋」字多，靠盘面大、纸墨稳、事实满、叙述收；样张、代码、定案不一致时停手统一。

---

## 十二、增长期与平台演进（W15+）

### 12.1 增长期（W15–W16）

BOOK-GTM：entitlement · analytics · snippets · 支付 · LandingVolume — **依赖 U5 六卷 API**。

### 12.2 平台演进（W17+，打磨期收官后）

**东方命理计算平台** 路线图（Engine Registry · KnowledgeStore · Pipeline · Capability）：

→ **[PLATFORM-EVOLUTION-ROADMAP](./PLATFORM-EVOLUTION-ROADMAP.md)**（E0–E3，**不替代**本文 W1–W16 执行）

| 阶段 | 周次 | 要点 |
|------|------|------|
| E0 | W17–W18 | Engine Protocol + 分层命名 |
| E1 | W19–W24 | Registry(bazi/ziwei) + KnowledgeStore + GET /engines |
| E2 | W25–W32 | PipelineStep + Rule 扩面 + liuyao 插件试点 |
| E3 | W33+ | Evidence 专家 API · 新术数 · CMS 校勘 |

**打磨期严禁提前做：** 全量 Registry 迁移 · Workflow DAG · Knowledge ORM · Evidence Graph · Mutation Test

---

## 附录 A · 问题台账索引（前端 73 条）

完整表见 [FUSHENG-FRONTEND-PLAN §四](../guides/FUSHENG-FRONTEND-PLAN.md)。致命项：**P-IA-01, P-ENG-01, P-API-01, P-API-04** — 由 F3/F4 + P1 explain 关闭。

---

## 附录 B · 后端字段速查

见 [BACKEND-MASTER 附录 A](./BACKEND-MASTER-PLAN-2026-07-12.md) 与 §三–§四字段全景。

---

## 附录 D · 外部资料整合任务清单

| ID | 来源 | 任务 | 负责 | 周次 | 状态 |
|----|------|------|------|------|------|
| SRC-01 | 文墨天机 xlsx | WM01–03 入库 | — | — | ✅ |
| SRC-02 | ziwei-main 文档 | star_profiles.json | — | — | ✅ |
| SRC-03 | 文墨 docx | narrative_samples（inference） | — | — | ✅ |
| SRC-04 | 资料/紫薇 | 跳过（c2 为权威） | — | — | ⏭ |
| SRC-05 | 引擎 vs WM | P0-11 wenmo diff | BE | W2 | ⬜ |
| SRC-06 | star_profiles | P1-11 explain_ziwei | BE | W6 | ⬜ |
| SRC-07 | colophon | P1-13 + F4-9 advisory UI | BE+FE | W8 | ⬜ |
| SRC-08 | iztro horoscope | P2-09 对照脚本 | BE | W12 | ⬜ |
| SRC-09 | 文墨运限表 | P2-10 horoscope diff | BE | W14 | ⬜ |
| SRC-10 | life-volume | colophon.wenmo_advisory 权威化 | BE+FE | W16 | ⬜ |

复现导入：`python scripts/import_desktop_content.py --desktop "D:/Users/Administrator/Desktop"`

---

## 附录 C · 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| integrated-1.0 | 2026-07-12 | 前后端统一执行版；契约 JSON；联合 W1–W16 |
| integrated-1.1 | 2026-07-12 | §12.2 挂钩 PLATFORM-EVOLUTION W17+ |
| integrated-1.3 | 2026-07-12 | 链入 DEVELOPMENT.md；16 份冗余开发文档归档 |
| integrated-1.2 | 2026-07-12 | 并入 RISK-ALERT（§5.11·§十·§十一）；Desktop 资料 §8.4·附录 D；P0-11~P2-10、F1-6/7、F4-9/10 |
