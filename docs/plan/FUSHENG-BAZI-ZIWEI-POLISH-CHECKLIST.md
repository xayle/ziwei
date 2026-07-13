# 浮生 · 八字紫微打磨专清单（免对话开发）

| 字段 | 内容 |
|------|------|
| **版本** | bz-polish-1.2 |
| **日期** | 2026-07-14 |
| **定位** | **只打磨八字/紫微 + 前端自检**；细节索引；**日常执行请用 [FUSHENG-DEV-PIPELINE](../FUSHENG-DEV-PIPELINE.md)** |
| **不含** | GTM · Extension · 平台 E0–E1 · 付费墙 · snippets · 埋点漏斗（见 [POST-W14](FUSHENG-EXECUTION-PRIORITY-POST-W14.md) §暂停说明） |
| **上级** | [INTEGRATED-DEV-PLAN](FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md) · [RISK-ALERT](../guides/FUSHENG-FRONTEND-RISK-ALERT.md) · [AUTOPILOT](../FUSHENG-DEV-AUTOPILOT.md) |
| **入口** | [DEVELOPMENT.md](../DEVELOPMENT.md) |

---

## 开工状态

```text
引擎 scorecard     24/24（A01 绿 · BZ001/BZ016 回归验收以此为准）
主清单进度         T001–T070 ☑ · W102 24/24 ☑ · Phase D 合盘 ☑
本清单             E1/E2/E3/F1/F2 ☑ · F3 大部 ☑ · BZ079–088 终验/签字可后置
机读门禁           autopilot 30/30+20/20 · anti-slop A09/A50 覆盖 BZ064
```

| 轨道 | 做完到 | 含义 |
|------|--------|------|
| **引擎可信** | BZ030 | 八字+紫微边缘 + 对照轨 advisory |
| **Explain/校勘** | BZ045 | batch 可用 · MVP-20 · content_policy |
| **三页自检** | BZ065 | 八字/紫微/报告卷目三门禁 |
| **打磨收官** | BZ088 | 与 T063–T070 终验对齐 |

---

## 零、怎么用本文（不用聊天）

1. **日常主顺序走 [PIPELINE](../FUSHENG-DEV-PIPELINE.md)**；本清单 **BZ###** 为八字/紫微深度补漏与索引，编号独立。
2. 每完成一条：`☐` → `☑`，提交信息写 `BZ0XX: 简述`。
3. **不得**用 advisory 结果覆盖 canonical 引擎；scorecard / autopilot 为机读真源。
4. Cursor 一句话：

   ```text
   执行 docs/plan/FUSHENG-BAZI-ZIWEI-POLISH-CHECKLIST.md 的 BZ052，按该条验收命令收尾。
   ```

5. 卡住：读该条「参考」列，勿重贴全套文档。

---

## 一、优先级总览

```text
E1  八字引擎边缘     BZ001–BZ015
E2  紫微引擎边缘     BZ016–BZ030
E3  Explain/信任     BZ031–BZ045
F1  八字页自检       BZ046–BZ055
F2  紫微页自检       BZ056–BZ065
F3  报告八字紫微     BZ066–BZ075
X   统一终验         BZ076–BZ088
```

**与 T 号映射（避免重复劳动）：**

| 本清单 | 主清单 | 说明 |
|--------|--------|------|
| BZ031–BZ038 | T035-BE · T048-BE | explain / MVP-20 |
| BZ046–BZ055 | T032–T033 · T023 | 八字卷二 + 三页门禁 |
| BZ056–BZ065 | T051–T052 · T023 | 紫微方盘/运限 + 门禁 |
| BZ066–BZ075 | T036–T044 · T048 | 报告六卷八字紫微 |
| BZ076–BZ088 | T056–T070 · T063 | 终验与 W14 勾选 |

---

## 二、顺序任务表

> **角色**：`FE` 前端 · `BE` 后端 · `DS` 设计 · `ALL` 全员 · `∥` 可并行

### 块 E1 · 八字引擎补漏（W1–W4）

| ☐ | ID | 角色 | 任务 | 主要文件 / 参考 | 验收 |
|---|-----|------|------|-----------------|------|
| ☑ | **BZ001** | BE | **GT50** 回归无恶化；`ground_truth_cases.json` 与引擎 geju 对齐率 100% | `data/ground_truth_cases.json` · `make scorecard` | scorecard 24/24 · B 轨全 10 |
| ☑ | **BZ002** | BE | `relations_summary` 稳定输出（合冲刑害/六合/三合等结构化） | `services/bazi_full_service.py` · `app/schemas/bazi.py` | `test_bazi_full_relations_summary_structure` |
| ☑ | **BZ003** | BE | `shensha_summary` 与柱级 `shensha` 一致；空时显式 `[]` | 同上 | pillar↔summary pytest |
| ☑ | **BZ004** | BE | `missing_fields` 覆盖：时柱未知、节气边界、双轨副盘 | `BaziFullRequest` · `bazi_full_service.py` | hour/jieqi/dual pytest |
| ☑ | **BZ005** | BE | 格局 **双轨** `geju.dual_track` 文档化 + 测试（ZIP 等） | REGISTRY · `tests/test_*bazi*` | B-07 REGISTRY + geju tests |
| ☑ | **BZ006** | BE | Compute 瘦身：默认 `full` **无**长 `interpretation_text`（Q4） | bazi compute/full 路由 | `_slim_full_interpretation` |
| ☑ | **BZ007** | BE | `provenance` / `evidence_chain` 与 `rule_version` 回传 | schemas | `/bazi/full` pytest |
| ☑ | **BZ008** | BE | 大运/流年/流月 API 边界：空档案、子时、真太阳时切换 | `tests/test_bazi_horoscope_edges.py` | 无 500 |
| ☑ | **BZ009** | BE | `bazi_summary` + `evidence_ids` 草案（P2-08） | `bazi_full_service.py` · template | evidence_ids 回传 pytest |
| ☑ | **BZ010** | ALL | 文墨八字案例 **advisory**：WM01–03 与引擎四柱/格局 diff 脚本 | `wenmo_engine_diff.py --bazi` | `wenmo-bazi-diff-latest.json` |
| ☑ | **BZ011** | BE | `content_policy`：无 `classic_id` 拒绝 cite（P0-06） | 新建 `services/content_policy.py` | pytest 拒 unverified |
| ☑ | **BZ012** | BE | `ChartSnapshot` 只算一次（P0-07） | `chart_snapshot_service.py` | 重复请求 hash 一致 |
| ☑ | **BZ013** | BE | `disclaimer_block` 进 full + explain schema（P0-08） | `app/schemas/*` | OpenAPI 可见 |
| ☑ | **BZ014** | BE | OpenAPI CI：`export_openapi` diff 阻断（P0-02） | `.github/workflows/ci.yml` | PR 改 schema 会红 |
| ☑ | **BZ015** | ALL | `make sync-frontend-types` 后 FE `api/bazi.ts` 与 OpenAPI 无 drift | `frontend/src/api/bazi.ts` | type-check 过 |

**E1-验收：**

```powershell
make scorecard
pytest -q tests/test_bazi*.py tests/test_boost*bazi* --ignore=tests/legacy
make sync-frontend-types
```

---

### 块 E2 · 紫微引擎补漏（W2–W6）

| ☐ | ID | 角色 | 任务 | 主要文件 / 参考 | 验收 |
|---|-----|------|------|-----------------|------|
| ☑ | **BZ016** | BE | **ZW20** 黄金集回归；`ziwei_ground_truth.json` 全绿 | `make scorecard` | scorecard 24/24 · Z 轨全 10 |
| ☑ | **BZ017** | BE | **ZW18 裁决**（P0-01）：1998-1-28 命宫 trust + `test_zw18_trust` | REGISTRY Z-11 · `tests/test_zw18_trust.py` | 裁决写入文档；测试绿 |
| ☑ | **BZ018** | BE | `trust_level` 全 API 回传（P0-04）：verified / reference / advisory / degraded | `app/schemas/ziwei.py` | FE 契约 §十四 |
| ☑ | **BZ019** | BE | **ZW03 双轨** by design：文墨/iztro 与引擎差异仅 advisory | PRODUCT.md 双轨原则 | colophon 脚注不覆盖盘 |
| ☑ | **BZ020** | BE | **右弼 ±1**（Z-12）：标 advisory；不静默修正 | engine + schema | `youbi_month_vs_iztro_hour` |
| ☑ | **BZ021** | BE | 宫位 **宫干/十神** 补全或显式 `missing_fields`（P2-04 B-07） | REGISTRY · `twelve_palaces` | `palace_ten_gods` advisory |
| ☐ | **BZ022** | BE | `star_profiles.json` 接入 explain stars（P1-11）；trust=reference | `data/ziwei/star_profiles.json` | 不标典籍 |
| ☐ | **BZ023** | BE | iztro 主星对照：`make verify-iztro` 绿 | `scripts/verify_ziwei_iztro.mjs` | 差异仅 advisory |
| ☑ | **BZ024** | BE | iztro **horoscope** 对照脚本草案（P2-09） | `scripts/verify_ziwei_horoscope_iztro.mjs` | WM01 3/3 decadal MATCH |
| ☑ | **BZ025** | BE | 文墨 xlsx 运限表 → horoscope diff（P2-10） | `scripts/wenmo_engine_diff.py --horoscope` | WM01 12/12 advisory |
| ☑ | **BZ026** | BE | 童限 / REGISTRY Z-11 草案（P2-05） | `ENGINE-METHOD-REGISTRY.md` | Z-11 节 + schema 草案 |
| ☑ | **BZ027** | BE | `youbi` 时辰对齐：hour 档与 iztro `--youbi=hour` 一致 | `useYoubiHourAlign` · API | `test_ziwei_iztro_hour_mode_aux_aligned` |
| ☑ | **BZ028** | BE | 紫微 `interpretation_text` 瘦身（同 BZ006） | ziwei full | palace 文案 ≤80 |
| ☐ | **BZ029** | BE | `colophon.wenmo_advisory` 字段草案（P1-13） | explain 响应 schema | F4-9 可接 |
| ☑ | **BZ030** | ALL | P0-12 资料导入可复现 | `scripts/import_desktop_content.py` | `pytest tests/test_import_desktop_content.py` |

**E2-验收：**

```powershell
make scorecard
make verify-iztro
make verify-iztro-hour
pytest -q tests/test_ziwei*.py tests/test_zw18_trust.py
```

---

### 块 E3 · Explain / 校勘 / 信任（W4–W8）

| ☐ | ID | 角色 | 任务 | 主要文件 / 参考 | 验收 |
|---|-----|------|------|-----------------|------|
| ☑ | **BZ031** | BE | `POST /explain/batch` 路由 + service 骨架 | `routers/bazi.py` · `services/explain_service.py` | 24 section fixture 绿 |
| ☑ | **BZ032** | BE | batch ≤4 sections/请求；报告 waterfall ≤4（Q8） | explain router | 集成测试计数 |
| ☑ | **BZ033** | BE | `explain-section-map.json` 与 vol1/2/4/5 映射一致 | `docs/contracts/explain-section-map.json` | 契约测试 |
| ☑ | **BZ034** | FE | `api/explain.ts` 对接真 API（替换纯 mock） | `frontend/src/api/explain.ts` | dev 可调 batch |
| ☑ | **BZ035** | BE | **MVP-20** verified 典籍齐（Q15） | `data/classics.json` | 20 条有 classic_id |
| ☐ | **BZ036** | BE | verified 比例 20%→35% 校勘轨（P2-01）；每周 8h | 校勘流程 | scorecard 内容项提升 |
| ☑ | **BZ037** | BE | `content_policy` 拒 narrative 标 cite（P1-12） | content_policy | unverified 测试红 |
| ☐ | **BZ038** | ALL | **C1** life-volume schema 共签（前后端+校勘） | `life-volume.schema.json` | 签字记录 |
| ☑ | **BZ039** | FE | `buildLifeVolumes` fixture 对齐 schema@1.0 | `frontend/src/utils/buildLifeVolumes.ts` | Vitest 绿 |
| ☑ | **BZ040** | FE | cite **仅** verified；reference/advisory 用 badge 不用「典籍依据」 | `VolumeSection.vue` | 无假出处 |
| ☑ | **BZ041** | FE | `TrustDegradedBanner` + `EngineTrustPanel` 统一（Q10：200 非 403） | 组件 | ZW18 E2E 目视 |
| ☑ | **BZ042** | FE | `missing_fields` / `provenance` 在八字紫微页可见 | trust 组件 | 非折叠深处 |
| ☐ | **BZ043** | BE | `metrics` / 结构化日志基线（P0-10） | logging | SLO 可采 |
| ☐ | **BZ044** | BE | `content_version` meta 回传（P0-05） | `data/*.json` | API 带 version |
| ☑ | **BZ045** | ALL | explain + trust 联调：报告 vol1/2/5 有 layer 块 | ReportView | 无编造 classic_id |

**E3-验收：**

```powershell
pytest -q tests/test_explain_*.py
cd frontend && npm run test -- buildLifeVolumes explain
make scorecard
```

---

### 块 F1 · 八字页前端自检（`/new/bazi`）

| ☐ | ID | 角色 | 任务 | 主要文件 | 验收 |
|---|-----|------|------|----------|------|
| ☑ | **BZ046** | FE | 接 API **`relations_summary`**（非仅 `useEngineTrustDisplay.relations` 派生） | `NewBaziView.vue` · `api/bazi.ts` | 卷二块数据来自 API 字段 |
| ☑ | **BZ047** | FE | 卷二独立块：`relations_summary` + `shensha_summary`（结构档可见） | `NewBaziView.vue` | `data-testid="bazi-vol2-block"` |
| ☑ | **BZ048** | FE | **移除**八字页 mount 自动 `loadDayunNarratives`（卷六不进工作台） | `NewBaziView.vue` · `fushengReport.ts` | 仅用户点击才加载 |
| ☑ | **BZ049** | FE | 深读 **无**卷五域卡（事业/财运等 8 域长文） | `buildBaziModuleCards.ts` | R-04：首屏无长 interpretation |
| ☑ | **BZ050** | FE | 首屏主内容为四柱/十神/格局 KPI；叙述 ≤80 字或折叠 | `NewBaziView.vue` | 防丑五问 4=是 |
| ☑ | **BZ051** | FE | 双轨表 `DualTrackTable` 在结构档可见 | 组件 | ZIP 等 dual_track 可核对 |
| ☑ | **BZ052** | ALL | **三门禁**自检（色彩/布局/内容） | RISK-ALERT §5 | §5.1–5.3 全过 |
| ☑ | **BZ053** | FE | **375px** 无页级横滚；一屏一锚（盘面优先） | 浏览器 DevTools | R-01 无叠层 |
| ☑ | **BZ054** | FE | 债务 `rg` 扫描（见下方 **§三 自检命令**） | `frontend/src` | 0 命中违规 pattern |
| ☑ | **BZ055** | FE | Vitest/E2E：`bazi` 空档案 · degraded · 结构档切换 | `e2e/*` · `__tests__/*` | 最小集绿 |

**F1-验收：**

```powershell
rg "loadDayunNarratives" frontend/src/views/new/NewBaziView.vue
rg "linear-gradient|PageHead|#334155|-ok-bg" frontend/src/views/new/NewBaziView.vue frontend/src/utils/buildBaziModuleCards.ts
cd frontend && npm run test:e2e -- bazi
```

---

### 块 F2 · 紫微页前端自检（`/new/ziwei` · 运限）

| ☐ | ID | 角色 | 任务 | 主要文件 | 验收 |
|---|-----|------|------|----------|------|
| ☑ | **BZ056** | FE | 方盘 Hero ≥60% 视口（handbook-ziwei） | `FushengZiweiView.vue` · `FushengZiweiPlate.vue` | 375/1440 目视 |
| ☑ | **BZ057** | FE | 无 `PageHead`；壳篇题唯一 | 紫微相关 views | rg PageHead 0 |
| ☑ | **BZ058** | FE | 方盘 **无** `linear-gradient`；`--surface` 纯色 | `FushengZiweiPlate.vue` | F2-2 |
| ☑ | **BZ059** | FE | trust `degraded` 横幅首屏可见（ZW18 案例） | `TrustDegradedBanner.vue` | 200 非 403 |
| ☑ | **BZ060** | FE | `missing_fields`（宫干/右弼等）在 trust 区列出 | `EngineTrustPanel` | 不静默吞掉 |
| ☑ | **BZ061** | FE | 深度三档：概览 / 结构 / 深读 口径与八字一致 | `FushengZiweiView.vue` | 切换无布局跳 |
| ☑ | **BZ062** | FE | `FushengZiweiTimeline` 运限分节 + sticky 日期 | `FushengZiweiTimeline.vue` | 卷三叙事感 |
| ☑ | **BZ063** | FE | 宫位说明不用长 `interpretation_text` 充首屏 | plate 周边文案 | ≤80 字或折叠 |
| ☑ | **BZ064** | ALL | 三门禁 + 防丑五问（紫微页） | RISK-ALERT §5.4 · AUTOPILOT A09/A50 | anti-slop E2E + Q5 代理绿 |
| ☑ | **BZ065** | FE | E2E：紫微加载 · 运限 · degraded | `e2e/*` | 绿 |

**F2-验收：**

```powershell
rg "linear-gradient|PageHead" frontend/src/views frontend/src/components/fusheng/FushengZiwei*
cd frontend && npm run test:e2e -- ziwei
```

---

### 块 F3 · 报告八字紫微自检（`/report`）

| ☐ | ID | 角色 | 任务 | 主要文件 | 验收 |
|---|-----|------|------|----------|------|
| ☑ | **BZ066** | FE | 卷目 **六卷+跋**；DOM 无旧 11 章名 /「四维分析」 | `ReportView.vue` | T036 对齐 |
| ☑ | **BZ067** | FE | 卷二：`relations_summary` + `shensha` 来自 snapshot | `buildLifeVolumes.ts` | vol2 非空或有「暂无」 |
| ☑ | **BZ068** | FE | 卷四：紫微盘 + stars **reference** 层；不标典籍 | `VolumeSection` · vol4 | P1-11 |
| ☑ | **BZ069** | FE | 卷五：推断默认折叠 + badge「推断」 | `VolumeSection.vue` | `aria-expanded=false` |
| ☑ | **BZ070** | FE | 卷六：**不** mount 自动 LLM / `loadDayunNarratives` | `ReportView.vue` | 用户触发 |
| ☑ | **BZ071** | FE | 跋：`ColophonFootnote` ≤3 行；iztro + wenmo **advisory** | `ColophonFootnote.vue` | F4-9 |
| ☑ | **BZ072** | FE | `explain/batch` 填 vol1/2/5；waterfall ≤4 | `ReportView.vue` | Network 计数 |
| ☑ | **BZ073** | FE | `disclaimer` + `ReadingGuide` 卷首可见 | 组件 | P0-08 |
| ☑ | **BZ074** | FE | 八字紫微 **crossValidation** 不一致时 trust 提示 | `validateBaziZiweiConsistency` | 有 case 则目视 |
| ☑ | **BZ075** | ALL | 报告三门禁 + 打印 `report-print.css` 六卷不截断 | `report-print.css` | 打印预览 |

**F3-验收：**

```powershell
rg "四维分析|ChapterStub|loadDayunNarratives" frontend/src/views/ReportView.vue
cd frontend && npm run test:e2e -- fusheng-report
```

---

### 块 X · 统一终验（对齐 T063–T070）

| ☐ | ID | 角色 | 任务 | 验收 |
|---|-----|------|------|------|
| ☑ | **BZ076** | ALL | 跑 **§三 全量自检命令** 一遍，贴 PR | `docs/reports/R084-self-check-2026-07-12.md` |
| ☑ | **BZ077** | FE | `make quality-gate-frontend` | type-check · lint · test · build |
| ☑ | **BZ078** | BE | `make quality-gate-backend` | 契约 + assembly 测试 |
| ☐ | **BZ079** | ALL | 对照 [EXECUTION-PRIORITY §六](FUSHENG-EXECUTION-PRIORITY.md#六w14-终验勾选t063-对照) 产品 11 项 + 预警 7 项 | 勾选截图 |
| ☐ | **BZ080** | DS | 三页截图 vs `docs/design/targets/*.png`；防丑五问签字 | M1 不倒退 |
| ☑ | **BZ081** | FE | Vitest 矩阵：六卷 × depth × 断点 | F6-1 |
| ☑ | **BZ082** | FE | Playwright 375px · degraded · 空档案 | F6 E2E |
| ☐ | **BZ083** | FE | a11y：aria-expanded · 焦点 · 色弱双编码 | P-A11Y |
| ☑ | **BZ084** | FE | 报告 waterfall p95 ≤4 请求 | `fusheng-report.spec.ts` R082 E2E | 4/4 chart 请求 |
| ☐ | **BZ085** | ALL | R-01~R-05 三页首屏复查 | 无红灯 |
| ☑ | **BZ086** | ALL | `make scorecard` 24/24 无回归 | `scorecard-latest.json` |
| ☐ | **BZ087** | ALL | **M4 能传** / **M5 能辩** 产品试 | 卷目+跋截图愿分享 |
| ☐ | **BZ088** | ALL | 八字紫微打磨轨签字；可进入 T070 / W14 收官 | 负责人签字 |

**X-终验：**

```powershell
make scorecard
make quality-gate
cd frontend && npm run type-check && npm run lint && npm run test && npm run test:e2e && npm run build
```

---

## 三、前端自检命令速查（每次 PR / BZ052+）

### 3.1 债务扫描（F2 三门禁）

```powershell
# 根目录 — 违规样式/组件
rg "linear-gradient|PageHead|#334155|-ok-bg|trust-drift-bg|Inter|Noto Serif" frontend/src docs/design/skin-preview.html

# 八字：卷六自动叙事
rg "loadDayunNarratives" frontend/src/views/new/NewBaziView.vue frontend/src/views/ReportView.vue

# 报告：旧 IA
rg "四维分析|ChapterStub" frontend/src/views/ReportView.vue

# API 字段：卷二未接
rg "relations_summary" frontend/src
```

**期望：** 债务 pattern **0 命中**；`relations_summary` 在 `api/bazi.ts` 与卷二视图 **有命中**。

### 3.2 引擎与对照

```powershell
make scorecard
make verify-iztro
make verify-iztro-hour
pytest -q tests/test_import_desktop_content.py tests/test_ziwei_iztro*.py
```

### 3.3 前端质量门

```powershell
make quality-gate-frontend
make sync-frontend-types
cd frontend && npm run test:e2e -- bazi ziwei fusheng-report
```

### 3.4 人工目检（不可脚本替代）

复制 [RISK-ALERT §5.4](../guides/FUSHENG-FRONTEND-RISK-ALERT.md#54-防丑五问负责人目检必须全是) 防丑五问，**三页各做一遍**：

| 页 | 路径 | 必过 |
|----|------|------|
| 八字 | `/new/bazi` | 盘面锚点 · 卷二可见 · 无自动 LLM |
| 紫微 | `/new/ziwei` | 方盘 ≥60% · degraded 可测 |
| 报告 | `/report` | 六卷+跋 · vol5 折叠 |

### 3.5 W14 产品勾选（与 T063 相同）

见 [EXECUTION-PRIORITY §六](FUSHENG-EXECUTION-PRIORITY.md#六w14-终验勾选t063-对照)。

---

## 四、本清单明确不做

与 [EXECUTION-PRIORITY §五](FUSHENG-EXECUTION-PRIORITY.md#五打磨期不做整段跳过) 相同，另加强：

| 不做 | 原因 |
|------|------|
| GTM / 抖音试投 / snippets | 打磨期纪律 |
| Extension 合盘/择日/相似 | 非八字紫微核心 |
| `GET /life/volumes` 权威切换（U5） | 属 POST-W14 T072+ |
| 平台 Registry 迁移 E0–E1 | W17+ |
| 用文墨/iztro **覆盖**引擎 canonical | PRODUCT 双轨 |
| 无 verified 标「典籍依据」 | 内容宪法 |

---

## 五、已知问题登记表（打磨时更新）

| 码 | 问题 | 状态 | 对应 BZ |
|----|------|------|---------|
| **GAP-B01** | FE 未接 `relations_summary` API 字段 | 🟢 | BZ046–BZ047 |
| **GAP-B02** | 八字/报告 mount `loadDayunNarratives` | 🟢 | BZ048 · BZ070 |
| **GAP-Z01** | ZW18 命宫 trust 待裁决 + 测试 | 🟡 | BZ017 |
| **GAP-Z02** | 宫干/十神部分空 | ✅ | `palace_ten_gods` missing_fields |
| **GAP-Z03** | 右弼 ±1 advisory 未 UI 注明 | ✅ | BZ020 · BZ060 · trust advisory |
| **GAP-E01** | `content_policy` / explain 路由未落地 | ✅ | BZ011 · BZ031 ☑ |
| **GAP-E02** | `ChartSnapshot` 服务未落地 | ✅ | BZ012 ☑ |
| **GAP-E03** | MVP-20 verified 未齐 | ✅ | BZ035 ☑ |
| **GAP-C01** | horoscope iztro/文墨对照脚本未建 | ✅ | BZ024–BZ025 已落地 |
| **GAP-F01** | `quality-gate` 未含 scorecard/iztro | 🟢 | `--with-scorecard` + `make quality-gate-full` |

状态图例：🔴 阻塞 · 🟡 advisory/可延期 · 🟢/✅ 已关闭

---

## 六、文档索引

| 块 | 细节 |
|----|------|
| E1–E2 | [BACKEND-MASTER](BACKEND-MASTER-PLAN-2026-07-12.md) · [ENGINE-CORE-FIX](ENGINE-CORE-FIX-PLAN-2026-07-11.md) |
| E3 | [explain-section-map.json](../contracts/explain-section-map.json) · INTEGRATED §5.5 |
| F1–F3 | [FRONTEND-PLAN](../guides/FUSHENG-FRONTEND-PLAN.md) · [RISK-ALERT](../guides/FUSHENG-FRONTEND-RISK-ALERT.md) |
| 对照资料 | [CONTENT-SOURCES-INTEGRATION](../reports/CONTENT-SOURCES-INTEGRATION.md) |
| 主顺序 | [EXECUTION-PRIORITY T001–T070](FUSHENG-EXECUTION-PRIORITY.md) |

---

## 七、修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| bz-polish-1.2 | 2026-07-14 | **P3-10～12** · GAP-E01–E03 ✅ · BZ001/016/064 ☑ · 入口改 PIPELINE |
| bz-polish-1.1 | 2026-07-12 | FE 块 BZ046–075 进度；GAP-B01/B02 关闭；链 DEV-AUDIT |
| bz-polish-1.0 | 2026-07-12 | 初版：八字紫微引擎边缘 + 三页自检 + 与 T015–T070 映射 |
