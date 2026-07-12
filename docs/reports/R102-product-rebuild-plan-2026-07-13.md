# R102 · 产品体验重建计划 — 2026-07-13

| 字段 | 内容 |
|------|------|
| **版本** | r102-1.1 |
| **日期** | 2026-07-13 |
| **触发** | 产品信心不足：UI 规划/布局/审美未达预期；内容空洞、可读性不足 |
| **对照真源** | [`skin-preview.html`](../design/skin-preview.html) · [`design/targets/`](../design/targets/) · [`FUSHENG-DESIGN-MASTERPLAN.md`](../design/FUSHENG-DESIGN-MASTERPLAN.md) |
| **内容审计** | [`content-hollowness-audit-latest.json`](content-hollowness-audit-latest.json) · `scripts/audit_content_hollowness.py` |
| **上位** | [`DEV-AUDIT-2026-07-13.md`](../DEV-AUDIT-2026-07-13.md) §W5 · [`R079-targets-compare-latest.json`](R079-targets-compare-latest.json) |

> **一句话**：机读全绿 ≠ 产品可交付。本文给出 **UI 差距清单**、**内容空洞审计**、**4 周按角色重建路线图**，作为 W5 目检与后续 sprint 的唯一执行真源。

---

## 〇、总判断

| 维度 | 评分（10 分制） | 说明 |
|------|:--------------:|------|
| 引擎 / 数据可信度 | 7.5 | 排盘骨架扎实，双轨、校勘意识强 |
| 信息架构 / 产品规划 | 6.0 | 六卷概念清晰，用户路径仍像「功能拼装」 |
| 视觉审美 / 宋式落地 | 4.5 | 设计宪法完备，实机偏「米色后台 + 表格堆叠」 |
| 内容丰满度 / 可读性 | 4.0 | 结构有了，叙事与典籍层偏薄 |
| 工程交付 / 可维护 | 8.0 | 契约、测试、门禁成熟 |
| **综合产品信心** | **5.0** | **工程过关，产品体验未过关** |

**核心矛盾**：团队用「工程验收标准」证明产品完成，用户用「像不像一册可信命盘辑录、读下来丰不丰满」验收——两套尺子不一致。

---

## 一、UI 差距清单（对照 skin-preview / targets）

**图例：** 🔴 必改 · 🟡 明显差距 · 🟢 基本对齐 · ⏸ 未纳入 targets 但影响体验

### 1. 全局 / AppShell

| # | skin-preview / masterplan 要求 | 实机现状 | 严重度 |
|---|-------------------------------|----------|:------:|
| G1 | 全站像「册页辑录」，纸墨铜朱四色预算 | token 已对齐，整体仍偏「表单 + KPI + 表格后台」 | 🟡 |
| G2 | 宋体 display 栈（A33 woff2） | 本地字体存在，实机宋式气质未 W5 目检签字 | 🟡 |
| G3 | 每屏 ≤1 处阴影（仅卷封 Hero） | 多处 `fs-card` 边框叠 card | 🟡 |
| G4 | 禁止三层标题（Shell + PageHead + 色块 h2） | `VolumeHead` + section 内 `h2` 仍双层/三层（如紫微页） | 🔴 |
| G5 | autopilot 美学 20/20 全绿 | 验结构 proxy，未验「像不像一册书」 | ⏸ |

### 2. 首页 `/new`（无 frozen target）

| # | 目标 | 实机 | 严重度 |
|---|------|------|:------:|
| H1 | 卷封 Hero：篆印 + 档案名 + 立义 | 有 hero-card，缺 skin-preview 级封面构图 | 🟡 |
| H2 | 首屏主角是「续读/进报告」 | KPI + 主路径说明 + 扩展工具三卡并列，像 onboarding | 🔴 |
| H3 | 六卷卷目 IA 为主视觉 | `VolumeTocGrid` 在 ReadingGuide 之后，权重不足 | 🟡 |
| H4 | 读法导览来自 explain `reading` | `ReadingGuide` 为静态固定文案 | 🔴 |

### 3. 八字页 `/new/bazi`（target: `bazi.png` · [handbook-bazi](../design/targets/handbook-bazi-layout.md) §7）

| # | handbook / skin §11 | 实机 | 严重度 |
|---|---------------------|------|:------:|
| B1 | 首屏 1/3 视口内见完整六柱 Hero | 有 grid；上方 VolumeHead + 口径条 + KPI + 速览 Trust 卡 | 🟡 |
| B2 | Trust 为白底脚注，非大框抢戏 | 速览态仍渲染 `EngineTrustPanel` | 🔴 |
| B3 | SummaryStrip KPI 值为铜金 | CSS `--brand-gold-dark` ✅ | 🟢 |
| B4 | 58% 左盘 + 42% 右栈 sticky | grid 结构 ✅ | 🟢 |
| B5 | 深度默认速览 | 三档 toggle ✅ | 🟢 |
| B6 | 禁止 L1/L2/L3 工程文案 | 已基本移除 ✅ | 🟢 |
| B7 | 解读下沉、默认折叠 | 仅「深读」出 AnalysisPanel ✅ | 🟢 |
| B8 | 六柱 Hero 比例 | targets height advisory：live 800 vs frozen 564 | 🟡 |
| B9 | flat 卡 ≤4 块 | 实际超 4 块（Head/KPI/Trust/Hero/深度/卷二/双轨/脚注/深读） | 🔴 |
| B10 | 典籍层左铜框 + 引文 | AnalysisPanel 有样式，geju 常 fallback「暂无典籍句式」 | 🟡 |

### 4. 紫微页 `/new/ziwei`（target: `ziwei.png` · [handbook-ziwei](../design/targets/handbook-ziwei-layout.md)）

| # | 目标 | 实机 | 严重度 |
|---|------|------|:------:|
| Z1 | 方盘 ≥60% 宽、≥50% 首屏高 | VolumeHead + KPI + 深度条 + h2「传统方盘」挤占首屏 | 🟡 |
| Z2 | 无双标题 | VolumeHead + section h2 重复 | 🔴 |
| Z3 | 纯色 `--surface` 无 gradient | ✅ | 🟢 |
| Z4 | degraded 必显横幅 | `TrustDegradedBanner` ✅ | 🟢 |
| Z5 | 速览右栏宫位解释 | 深读才有 `PalaceAnalysisGrid` | 🟡 |
| Z6 | 运限拆 timeline | 符合规划 ✅ | 🟢 |
| Z7 | 页内 explain batch | **未请求** `ziwei/explain/batch`（仅 report） | 🔴 |

**与 frozen PNG：** height 800 vs 402 → 实机首屏低于样页「方盘占半屏」意图。

### 5. 报告页 `/report`（target: `report-toc.png` · [handbook-report](../design/targets/handbook-report-layout.md)）

| # | 目标 | 实机 | 严重度 |
|---|------|------|:------:|
| R1 | 首屏卷目/卷封，非字段清单 | 卷封后紧接双 SummaryStrip + 经度/时区等 meta | 🔴 |
| R2 | 连续阅读单 scroll | continuous toggle ✅ | 🟢 |
| R3 | 卷五推断默认折叠 | E2E 已验 ✅ | 🟢 |
| R4 | 跋 ≤3 行，校勘 expandable | vol2/vol4 内嵌整页 `EngineTrustPanel`（两次） | 🔴 |
| R5 | 请求 ≤4 | computeBazi + computeZiwei + explain×2，无 archive-bundle | 🟡 |
| R6 | 像辑录非 SaaS | 校勘 UI（Trust/iztro 双轨表）占比过大 | 🔴 |
| R7 | 卷三运限有叙事 | 多为「1. 丙子 0.0岁起」列表 | 🔴 |
| R8 | reading explain 进卷首 | explain batch 未请求 `reading` | 🔴 |

### 6. 档案页 `/profile`

| # | 问题 | 严重度 |
|---|------|:------:|
| P1 | 算法参数多，缺「改完会怎样」即时说明 | 🟡 |
| P2 | 完整度百分比驱动，不像「写辑录封面信息」 | 🟡 |
| P3 | case 同步字段全，UI 仍为标准表单 | 🟡 |

### UI 差距汇总

| 优先级 | 数量 | 代表项 |
|--------|:----:|--------|
| 🔴 P0 | 12 | 三层标题、Trust 抢戏、报告卷首 meta 化、页内 explain 未接入 |
| 🟡 P1 | 10 | 首屏比例、卡片过多、宋式目检、home 编排 |
| 🟢 已对齐 | 8 | token/KPI 铜色、深度三档、degraded、continuous read |

---

## 二、内容空洞审计

**样本档案：** 1990-01-15 08:30 男 · 北京（116.41°E）  
**方法：** live `bazi_full` + `ziwei_full` + explain batch，按 `buildLifeVolumes.ts` 等价逻辑统计 block。

**指标：**

- **fallback 占比**：含「缺失/暂无/待计算/待载入/列表数据」等占位
- **thin 占比**：非 fallback 但 **<40 字**
- **trunc 占比**：触达 500 字截断上限

### 2.1 各卷统计

| 卷 | blocks | fallback | thin | trunc | 均字数 | 评级 |
|----|:------:|:--------:|:----:|:-----:|:------:|:----:|
| 卷首 preface | 1 | 0% | **100%** | 0% | 32 | 🔴 |
| 卷一 vol1 | 13 | 0% | 54% | 0% | 90 | 🟡 |
| 卷二 vol2 | 3 | **33%** | 33% | 0% | 29 | 🔴 |
| 卷三 vol3 | 9 | 11% | **89%** | 0% | 12 | 🔴 |
| 卷四 vol4 | 12 | 0% | **100%** | 0% | 10 | 🔴 |
| 卷五 vol5 | 3 | 0% | 0% | 0% | 96 | 🟢 |
| 卷六 vol6 | 1 | 0% | 100% | 0% | 24 | 🔴 |
| 跋 colophon | 1 | 0% | 100% | 0% | 25 | 🟡 |
| **合计** | **43** | **5%** | **72%** | **0%** | **~44** | **🔴** |

> **结论：** 6/8 卷 thin ≥80%；仅卷五（explain domains）可读厚度达标。

### 2.2 分卷诊断

| 卷 | 问题 | 样例 |
|----|------|------|
| **卷一** | 有典籍引文（99 字 ✅），但被 13 个 thin block 稀释 | 首条仅「日主 庚辰；格局 正印格。」 |
| **卷二** | `formatRelationsSummaryText` 对标准命例仍输出「暂无干支关系摘要」— **集成 bug** | 神煞 57 字像标签云 |
| **卷三** | 大运条目无 narrative | `1. 丙子 0.0岁起` |
| **卷四** | explain palaces 12 block 均 ≤11 字 | `命宫 酉：廉贞、破军` |
| **卷五** | explain domains 73–123 字 — **唯一达标** | 财运/事业/性格成段 |
| **卷六** | 纯占位 | 「不自动调用 LLM」 |
| **卷首/跋** | 静态模板 | 无个案读法 |

### 2.3 Explain 管线

| 指标 | 值 |
|------|-----|
| bazi explain sections | 4（geju/relations/domains/summary） |
| bazi blocks / 均长 | 8 / **83.9 字** |
| ziwei blocks / 均长 | 12 / **~10 字** |
| reading section | **未请求** |
| explain 失败 UX | 静默 `{ sections: [] }` |

### 2.4 页面层 fallback 密度（源码 grep）

| 文件 | 「缺失/待计算/暂无」次数 |
|------|:--:|
| `NewBaziView.vue` | 37 |
| `ReportView.vue` | 16 |
| `FushengZiweiView.vue` | 5 |

### 2.5 内容健康度目标（4 周验收）

| 指标 | 当前 | 目标 |
|------|:----:|:----:|
| 全卷 thin block 占比 | 72% | **≤35%** |
| 卷三/卷四 均字数 | 12 / 10 | **≥60** |
| 卷二 relations fallback | 33% | **0%** |
| 每卷 ≥1 段 cite ≥80 字 | 2/8 | **6/8** |
| explain reading 接入 | 否 | 是 |

---

## 三、4 周重建路线图

**原则：** 停功能扩张；**W5 目检 → 内容灌满 → 视觉减法 → 验收签字**。  
每周五：`make audit-content` + 实机截图对比 targets。

### 第 1 周 · 对齐真源 + 视觉减法

| 角色 | 交付 | 验收 |
|------|------|------|
| **PM** | 冻结本文 §一 P0 共 12 条；R060 15 分钟真人试读 | 试读 ≥7/10 或书面优先级 |
| **设计** | W5 目检：skin-preview 并排实机三页；补 home/profile target 草图；R079 Q1–Q5 **真人**签字 | `docs/design/audit-screenshots/target-*-2026-07-*.png` |
| **FE** | ① 八字速览去 Trust 大卡 ② 紫微去 duplicate h2 ③ 报告卷首封面-only ④ flat 卡 ≤4 | E2E anti-slop 仍绿 + DS 并排 |
| **内容** | 修 `formatRelationsSummaryText` 空路径；查 ziwei explain 碎块根因 | vol2 fallback 0% |
| **BE** | explain ziwei palaces 合并为 ≥40 字/宫；`reading` section 最小实现 | ziwei explain 均字 ≥40 |

**周出口：** 三页首屏主角达标；Trust 不再抢戏。

### 第 2 周 · 内容灌满

| 角色 | 交付 | 验收 |
|------|------|------|
| **PM** | 每卷最少内容 spec（§2.5）；卷三/卷四 narrative 用户故事 | 内容 spec v1 签字 |
| **设计** | 卷一开篇、卷三运限、卷四宫论 排版样张 → skin-preview §13–15 | 3 张 HTML mock |
| **FE** | 八字/紫微接入 explain（含 reading）；explain 失败 banner；buildLifeVolumes 卷三/四加厚；减少 UI fallback | audit thin ≤50% |
| **内容** | 卷一–四各 +2 verified classic + 1 engine 成段 | +4 classic/卷 |
| **BE** | 卷三 dayun explain；life/volumes 与 adapter 字数差距 <20% | API 厚度对齐 |

**周出口：** 标准命例 ≥4 卷均字 ≥60。

### 第 3 周 · 报告辑录化 + PDF 一致

| 角色 | 交付 | 验收 |
|------|------|------|
| **PM** | R060 步骤 1–10 全勾；10 分钟连续阅读试读脚本 | P1 Gate |
| **设计** | 报告 print/PDF；卷封阴影唯一；mobile 375 卷目 | handbook-report v1.1 |
| **FE** | Trust 仅 colophon；archive-bundle；PDF 全 algo 参数；卷五展开 ≥300 字/domain | E2E trial-read + PDF 一致 |
| **内容** | 卷六预置 3 示例 Q&A；卷首 reading explain | 卷六非占位 |
| **BE** | archive-bundle gender 修复；FushengReportPdfRequest algo 字段 | bundle = /ziwei/full |

**周出口：** 报告像翻书；PDF = 屏幕。

### 第 4 周 · 验收收口

| 角色 | 交付 | 验收 |
|------|------|------|
| **PM** | R079/R060/R101 产品签字；15 min demo 脚本 | 信心复评 ≥7/10 |
| **设计** | Q5 盲测；home/profile targets 冻结 | targets 5 页 |
| **FE** | 报告 ≤4 请求；sync-frontend-types；debt 0 | autopilot 30+20 |
| **内容** | 空 block 扫尾；卷三 narrative 模板 | thin ≤35% |
| **QA** | `make audit-content` 进 CI advisory | 机读内容门禁 |
| **全体** | skin-preview vs live vs targets 最终截图 PR | R102 closeout |

### 甘特一览

```text
Week1  [设计目检][FE视觉减法][修relations bug]
Week2  [内容灌满][explain接入][排版样张]
Week3  [报告辑录化][PDF一致][archive-bundle]
Week4  [试读签字][CI内容门禁][demo脚本]
```

### 资源建议

| 角色 | 投入 |
|------|------|
| PM | 0.3 FTE |
| 设计 | 0.5 FTE |
| FE | 1 FTE |
| 内容/校勘 | 0.5 FTE |
| BE | 0.2 FTE |

---

## 四、验收命令

```powershell
# UI 截图对比
cd frontend && npm run test:e2e -- fusheng-targets-screenshot
node scripts/compare-live-targets.mjs

# 内容空洞审计（标准命例）
make audit-content
# 或：python scripts/audit_content_hollowness.py
# → docs/reports/content-hollowness-audit-latest.json

# 设计样页并排目检
# 浏览器：docs/design/skin-preview.html
# 实机：http://127.0.0.1:8000/new/bazi 等
```

---

## 十一、未收录技术债

> 以下项 **不在 §一 UI 差距** 内，但影响 FE-BE 一致性与 PDF/报告可信度；挂 DEV-AUDIT **P2-5～P2-8、P3-2～P3-4**。

| ID | 问题 | 位置 / 说明 | 计划周 |
|----|------|-------------|--------|
| TD-01 | `buildBaziRequest()` 未传 `birth_time_precision` | `frontend/src/api/bazi.ts` → `/bazi/full` | Week3 |
| TD-02 | 报告 PDF 缺紫微 algo 参数（`late_zishi` 等） | `build_fusheng_report_payload()` / `FushengReportPdfRequest` | Week3 |
| TD-03 | `archive-bundle` ziwei `gender` 用 `male`/`female` 非 `男`/`女` | `_case_to_ziwei_request` | Week3 |
| TD-04 | 报告仍并行 `computeBazi` + `computeZiwei`，未走 `archive-bundle` | `ReportView` / report store | Week3 |
| TD-05 | `explain.ts` 吞错 → `{ sections: [] }` 静默 | 八字页已有 banner（W102-09）；紫微待 W102-10 | Week2 |
| TD-06 | `api/bazi.ts` 重复声明 `city_tier` / `industry` | 工程卫生 | Week4 |
| TD-07 | 手写 API types 与 `schema.d.ts` 双轨 | `make sync-frontend-types` 后仍手写 | Week4 |
| TD-08 | `formatRelationsSummaryText` fallback | ✅ W102-06 · vol2 0% | — |
| TD-09 | 卷三大运展示 `0.0岁起`（float 未格式化） | `buildLifeVolumes` 卷三 adapter | Week2 |
| TD-10 | 六卷 PDF 与合盘 PDF 共用 `render_html_to_pdf` | 合盘 P3 见 [R086 §五](R086-relation-compat-sample-pdf-review-2026-07-13.md#五差距与优先级) | R102 之后 |
| TD-11 | PDF 请求「幽灵字段」（FE 发 `birth_time_precision`/`late_zishi` BE 不收） | `buildFushengReportPdfRequest` vs `FushengReportPdfRequest` | Week3 |
| TD-12 | `archive-bundle` 参数缺口 + FE 零调用 | `fusheng_archive.py` · 无 TS client | Week3 |
| TD-13 | `lateZishi` 仅存 case tags，bundle 不读 | `profileCaseSync.ts` · `Case` 无列 | Week3 |
| TD-14 | Q12 页面 explain 常量未接线 | ✅ 八字 `NewBaziView` · 紫微 W102-10 | Week2 |
| TD-15 | `fetchLifeVolumes` 失败静默 fallback | `api/life.ts` · `ReportView` | Week2 |
| TD-16 | CI 跑 `auto_verify_w14` ≠ 本地 autopilot 全量 | `.github/workflows/ci.yml` | W102-P3-02 |
| TD-17 | `audit-content` 未进 CI | Makefile 有 · CI 无 | Week4 |
| TD-18 | `verify_surface_levels.py`（A45）未进 CI | AUTOPILOT | Week4 |
| TD-19 | `auto_verify_r007` 只验 markdown 不验实现 | FE-BE Q12/Q6/Q9 | 🟡 |
| TD-20 | AUTOPILOT 文称 A30–A59，脚本止于 A50 | 编号口径 | ✅ W102-00b 修正 |
| TD-21 | 扩展页 partner 经度/性别（CompatView · ZiweiCompatView） | `extensions/*` | R086 之后 |
| TD-22 | `profile/summary` 精简排盘 vs workbench 不一致 | `profile_summary.py` | Week3 |
| TD-23 | Q6 `source_page` FE 未展示 | FE-BE W12 | Week4 |
| TD-24 | audit JSON 缺 rollup 字段（thin 合计等） | `audit_content_hollowness.py` | 🟡 低 |
| TD-25 | `explain.ts` / life API 等静默失败（除 TD-05） | 见 DEV-AUDIT P2-9 链 | Week2 |
| TD-27 | audit vol2 路径 ≠ FE | ✅ W102-07 | — |
| TD-30 | EXECUTION-REMAINING 与 AUTOPILOT pass 叙事冲突 | 文档 | P3-13 |
| TD-31 | `static/app/assets` 与源码 build 漂移 | 部署 | P3-17 |
| TD-32 | 报告 E2E A15/A17/A43 本地红 | `fusheng-report` spec | P2-9 |

---

## 五、修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| r102-1.0 | 2026-07-13 | 初版：UI 差距 · 内容审计 · 4 周路线图；挂 DEV-AUDIT W5 |
| r102-1.1 | 2026-07-13 | §十一 未收录技术债；§四 `make audit-content` |
| r102-1.2 | 2026-07-13 | TD-08/27 ✅ · TD-11～32 第二轮 · P2-6 closeout |

---

**R102 状态：** 🟡 Week1 出口 ✅（10/24）；Week2 内容灌满待启动。
