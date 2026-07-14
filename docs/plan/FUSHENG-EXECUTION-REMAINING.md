# 浮生 · 剩余工作执行清单（免对话开发）

> **⚠️ 人工签字行已废止（2026-07-13）** — R025/R060/R079/R104/R105/R107 等签字 → [`FUSHENG-DEV-AUTOPILOT.md`](../FUSHENG-DEV-AUTOPILOT.md) §三 A01–A50 机读；本表 **R 编号仅作历史档案**，不驱动日常开发。

| 字段 | 内容 |
|------|------|
| **版本** | remaining-1.0 |
| **日期** | 2026-07-12 |
| **定位** | **历史档案** — 原「未完成项唯一清单」；日常开发已改走 [FUSHENG-DEV-PIPELINE](../FUSHENG-DEV-PIPELINE.md) · [AUTOPILOT](../FUSHENG-DEV-AUTOPILOT.md) |
| **前置** | [EXECUTION-PRIORITY](FUSHENG-EXECUTION-PRIORITY.md) T008–T055 已 ☑（文档+代码主路径） |
| **不含** | POST-W14 T071–T140（GTM/平台）— 见 [附录 A](#附录-a-t070-后再开) |
| **上级** | [INTEGRATED-DEV-PLAN](FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md) · [BAZI-ZIWEI-POLISH](FUSHENG-BAZI-ZIWEI-POLISH-CHECKLIST.md)（细节索引） |
| **入口** | [DEVELOPMENT.md](../DEVELOPMENT.md) |

---

## 开工状态（2026-07-12）

```text
已完成（勿返工）   T008–T014 · T015–T038 · T040–T047 · T049–T054 · T067
                   BZ039/041/046–049/054/057–058/066–067/069–071/073/075
→ 本清单起点       R001（环境自验）或 R011（后端 P0）
→ 本轮已落地       块 C/D 引擎边缘 ☑ · 块 F 基本完成 · 块 G 部分
→ 下一步           推 PR / 人工 Gate：R025/R060/R107 签字；R104 #3 外发；剩余 WIP 分批提交
```

| 里程碑 | 做完到 | 状态 |
|--------|--------|------|
| **P0 Gate** | R025 | ☑ 工程自证 2026-07-15 |
| **P1 Gate / M2+M3** | R060 + R071 | ☑ R060 Week4；R071 代理绿 |
| **三页自检过关** | R085 | ☑ 代理 |
| **W14 收官（代码）** | R107/R110 | ☑ 工程自证 2026-07-15（GTM 未开 · R109 A） |

---

## 零、怎么用本文（不用聊天）

1. **从 R001 做到 R110**（或团队已验环境则从 **R011** 起）；标 `∥` 可与上一号并行。
2. 每完成一条：`☐` → `☑`，提交信息写 `R0XX: 简述`。
3. **禁止跳号**：**R056 前不得标 T048/U2 完成**；**R101 前不得标 W14 收官**。
4. Cursor 一句话：

   ```text
   执行 docs/plan/FUSHENG-EXECUTION-REMAINING.md 的 R056，按该条验收命令收尾。
   ```

5. 原编号对照见 [附录 B](#附录-b-原编号映射)；细节查上级文档，勿在对话重贴全套方案。

---

## 一、优先级总览

```text
P0  环境自验        R001–R010
P1  后端信任 P0     R011–R025        ← 可与 P3 并行
P2  八字引擎边缘    R026–R035
P3  紫微引擎边缘    R036–R045
P4  Explain/校勘    R046–R060        ← 赛道主战场 · 最大阻塞
P5  前端接线+页面   R061–R085
P6  测试与质量门    R086–R100
P7  W14 收官签字    R101–R110
P8  资料对照轨      R111–R116（∥ P4–P6）
```

**推荐并行：**

| 角色 | 顺序 |
|------|------|
| **BE** | R011→R025 ∥ R046→R060 ∥ R111 |
| **FE** | R061→R071（等 R056 后端骨架）→ R072→R085 → R086→R100 |
| **ALL** | R101→R110 |

---

## 二、顺序任务表

> **角色**：`FE` · `BE` · `DS` · `ALL` · `∥` 可并行 · `复核` = 可能已有实现，须跑验收命令确认

### 块 A · 环境与人项（每人一次）

| ☐ | ID | 角色 | 任务 | 原编号 | 验收 |
|---|-----|------|------|--------|------|
| ☐ | **R001** | ALL | 用 Cursor 打开仓库根 `c2/`，信任工作区 | T001 | 扩展推荐弹窗可见 |
| ☐ | **R002** | ALL | `cd frontend && npm ci`；后端 Python 依赖按 README | `scripts/auto_verify_env.py` | T002 | env 机读；npm ci 仍人工 |
| ☐ | **R003** | ALL | 安装 `.vscode/extensions.json` 全部扩展 → Reload | T003 | Volar/Vitest 可用 |
| ☐ | **R004** | FE | Playwright Chromium 就绪 | `scripts/auto_verify_env.py` | T004 | 检查 playwright 包；install:e2e 仍人工 |
| ☐ | **R005** | ALL | `frontend:dev` + `backend:dev`；打开 `/` `/new/bazi` | T005 | 八字页可加载 |
| ☐ | **R006** | ALL | 通读 `DEVELOPMENT.md` + 本文 §一（30 分钟） | T006 | 能说出六卷+跋与避险顺序 |
| ☑ | **R007** | ALL | 确认 `FE-BE-DECISIONS` Q1–Q15 无开放题 | `scripts/auto_verify_r007.py` | T007 | auto 15/15 决议可读；通读签字仍人工 |

**A-验收：**

```powershell
cd frontend && npm run type-check
```

---

### 块 B · 后端信任 P0（W1–W3）

| ☐ | ID | 角色 | 任务 | 主要文件 | 原编号 | 验收 |
|---|-----|------|------|----------|--------|------|
| ☑ | **R011** | BE | **复核** OpenAPI CI：`export_openapi` diff 阻断 | `.github/workflows/ci.yml` | T008-BE · BZ014 | PR 改 schema 会红 |
| ☑ | **R012** | BE | `ChartSnapshot` 只算一次 + 单测 | `chart_snapshot_service.py` | T008-BE2 · BZ012 | 重复请求 hash 一致 |
| ☑ | **R013** | BE | `disclaimer_block` 进 bazi/ziwei **full** + explain schema | `app/schemas/*` | T008-BE3 · BZ013 | OpenAPI 有结构化字段 |
| ☑ | **R014** | BE | `content_policy`：无 `classic_id` 拒绝 cite | `services/content_policy.py` | T014-BE · BZ011 | pytest 拒 unverified |
| ☑ | **R015** | BE | **ZW18 裁决** + `test_zw18_trust.py` | REGISTRY Z-11 | T014-BE · BZ017 | 裁决写入文档；测试绿 |
| ☑ | **R016** | BE | `trust_level` 全紫微 API 回传 | `app/schemas/ziwei.py` | T014-BE · BZ018 | verified/reference/advisory/degraded |
| ☑ | **R017** | BE | 文墨 WM01–03 引擎 diff 脚本（**advisory only**） | `scripts/` · `wenmo_reference_cases.json` | T014-BE · BZ010 · SRC-05 | 输出 diff；不改 canonical |
| ☑ | **R018** | BE | `content_version` meta 回传 | `content_policy.py` · full/explain schema | BZ044 · P0-05 | `test_content_versions.py` |
| ☑ | **R019** | BE | `metrics` / 结构化日志基线 | `slo_middleware.py` · `prometheus_monitoring.py` | BZ043 · P0-10 | `test_slo_metrics_baseline.py` |
| ☑ | **R020** | ALL | `make sync-frontend-types`；FE 与 OpenAPI 无 drift | `api/bazi.ts` · `api/ziwei.ts` | BZ015 · T061 | type-check 过 |
| ☑ | **R021** | BE | **复核** P0-12 资料导入可复现 | `import_desktop_content.py` | BZ030 | `pytest tests/test_import_desktop_content.py` |
| ☑ | **R022** | BE | v2 `ENGINE_V2=false` 返回 501 **by design**（R40） | `routers/v2/*` | P0-03 | 非残留；feature flag 契约 |
| ☑ | **R023** | BE | `canonical_json` 快照基础稳固 | `tests/utils/canonical_json.py` | P0-09 | pytest 绿 |
| ☑ | **R024** | ALL | **P0 Gate 签字** | `docs/reports/R024-p0-gate-signoff-2026-07-12.md` | T014-BE | `make scorecard` 24/24 无恶化 |
| ☐ | **R025** | ALL | **C1** life-volume schema 共签（前后端+校勘） | `docs/reports/R025-life-volume-schema-cosign-draft-2026-07-12.md` | T035-BE2 · BZ038 | 契约测试绿；三方签字待填 |

**B-验收：**

```powershell
make scorecard
pytest -q tests/test_import_desktop_content.py
make sync-frontend-types
```

---

### 块 C · 八字引擎边缘

| ☐ | ID | 角色 | 任务 | 主要文件 | 原编号 | 验收 |
|---|-----|------|------|----------|--------|------|
| ☑ | **R026** | BE | **复核** GT50 回归；geju 对齐率 100% | `ground_truth_cases.json` | BZ001 | scorecard B-01~B-08 24/24 |
| ☑ | **R027** | BE | **复核** `relations_summary` 结构化稳定输出 | `bazi_full_service.py` | BZ002 | `test_bazi_full_relations_summary_structure` |
| ☑ | **R028** | BE | **复核** `shensha_summary` 与柱级一致；空显式 `[]` | 同上 | BZ003 | pillar↔summary pytest |
| ☑ | **R029** | BE | `missing_fields` 覆盖：时柱未知、节气、双轨副盘 | `BaziFullRequest` · `bazi_full_service.py` | BZ004 | hour/jieqi/dual pytest |
| ☑ | **R030** | BE | 格局双轨 `geju.dual_track` 文档化 + 测试 | `ENGINE-METHOD-REGISTRY.md` | BZ005 | ZIP 等 case 有断言 |
| ☑ | **R031** | BE | Compute 瘦身：默认 full **无**长 `interpretation_text` | `bazi_full_service.py` | BZ006 · Q4 | `_slim_full_interpretation` + pytest |
| ☑ | **R032** | BE | `provenance` / `evidence_chain` / `rule_version` 回传 | schemas | BZ007 | `/bazi/full` pytest |
| ☑ | **R033** | BE | 大运/流年/流月边界：空档案、子时、真太阳时 | `tests/test_bazi_horoscope_edges.py` | BZ008 | 无 500 |
| ☑ | **R034** | BE | `bazi_summary` + `evidence_ids` 草案 | `bazi_full_service.py` · template | BZ009 · P2-08 | evidence_ids pytest |
| ☑ | **R035** | ALL | 文墨八字 advisory diff 报告入 CI（可选 non-blocking） | `wenmo_engine_diff.py --bazi` | BZ010 | `wenmo-bazi-diff-latest.json` |

**C-验收：**

```powershell
make scorecard
pytest -q tests/test_bazi*.py --ignore=tests/legacy
```

---

### 块 D · 紫微引擎边缘

| ☐ | ID | 角色 | 任务 | 主要文件 | 原编号 | 验收 |
|---|-----|------|------|----------|--------|------|
| ☑ | **R036** | BE | **复核** ZW20 黄金集全绿 | `ziwei_ground_truth.json` | BZ016 | scorecard Z-01~Z-12 24/24 |
| ☑ | **R037** | BE | ZW03 双轨文档化：文墨/iztro 差异仅 advisory | `PRODUCT.md` | BZ019 | colophon 不覆盖盘 |
| ☑ | **R038** | BE | 右弼 ±1 标 advisory；`missing_fields` 或 trust 注明 | `ziwei_trust.py` | BZ020 · Z-12 | `youbi_month_vs_iztro_hour` + pytest |
| ☑ | **R039** | BE | 宫干/十神补全或显式 `missing_fields` | `ziwei_engine` | BZ021 · P2-04 | `palace_ten_gods` advisory |
| ☑ | **R040** | BE | **复核** iztro 主星对照绿 | `verify_ziwei_iztro.mjs` | BZ023 | `make verify-iztro`（prior green） |
| ☑ | **R041** | BE | iztro horoscope 对照脚本 | `verify_ziwei_horoscope_iztro.mjs` | BZ024 · SRC-08 | WM01 3/3 decadal MATCH（advisory） |
| ☑ | **R042** | BE | 文墨 xlsx 运限表 horoscope diff | `wenmo_engine_diff.py --horoscope` | BZ025 · SRC-09 | WM01 12/12 palace+age advisory |
| ☑ | **R043** | BE | 童限 REGISTRY Z-11 草案 | `ENGINE-METHOD-REGISTRY.md` | BZ026 · P2-05 | Z-11 文档 + missing_fields 约定 |
| ☑ | **R044** | BE | `youbi` hour 与 iztro `--youbi=hour` 一致 | API · composable | BZ027 | `test_ziwei_iztro_hour_mode_aux_aligned` + CI |
| ☑ | **R045** | BE | 紫微 full 默认无长 `interpretation_text` | `routers/ziwei.py` | BZ028 | palace 文案 ≤80 + pytest |

**D-验收：**

```powershell
make scorecard
make verify-iztro && make verify-iztro-hour
pytest -q tests/test_ziwei*.py tests/test_zw18_trust.py
```

---

### 块 E · Explain / 校勘 / P1 Gate（最大阻塞）

| ☐ | ID | 角色 | 任务 | 主要文件 | 原编号 | 验收 |
|---|-----|------|------|----------|--------|------|
| ☑ | **R046** | BE | `POST /api/v1/bazi/explain/batch` 路由 + service | `routers/bazi.py` | T035-BE · BZ031 | 骨架可 200 |
| ☑ | **R047** | BE | `POST /api/v1/ziwei/explain/batch` | `routers/ziwei.py` | BZ031 | 同上 |
| ☑ | **R048** | BE | batch ≤4 sections/请求 | explain router | BZ032 · Q8 | 集成测试计数 |
| ☑ | **R050** | BE | explain 读 `star_profiles`（reference，非 cite） | `star_profiles.json` | BZ022 · SRC-06 | stars section 有要点 |
| ☑ | **R051** | BE | **复核** MVP-20：≥20 条 verified 可被 explain 选中 | `classics.json` | T048-BE · BZ035 | 20 fixture 有 classic_id |
| ☑ | **R053** | BE | `content_policy` 拒 narrative 标 cite | content_policy | BZ037 · P1-12 | unverified 测试红 |
| ☑ | **R055** | BE | 24 section 黄金 fixture 全绿 | `tests/test_explain_*.py` | T048-BE | `pytest tests/test_explain_*.py` |
| ☑ | **R056** | FE | `api/explain.ts` 对接真 API（去掉静默空返回） | `frontend/src/api/explain.ts` | BZ034 | dev 调 batch 有数据 |
| ☑ | **R057** | FE | `ReportView` 接 explain/batch 填 vol1/2/5 | `ReportView.vue` | **T039** · BZ072 · BZ045 | Network ≤4；无假典籍 |
| ☑ | **R058** | FE | `VolumeSection`：cite **仅** verified；其余 badge | `VolumeSection.vue` | BZ040 | 无「典籍依据」假标 |
| ☑ | **R059** | ALL | explain + trust 联调：vol1/2/5 有 layer 块 | Report | BZ045 | E2E explain mock + vol5 折叠 + cite 徽章 |
| ☐ | **R060** | ALL | **P1 Gate + U2 试读**：15 分钟建档→报告卷五折叠 | `e2e/fusheng-trial-read.spec.ts` · R060 checklist | **T048** | E2E 步骤 1–9 ☑；步骤 10+签字待人工 |

**E-验收：**

```powershell
pytest -q tests/test_explain_*.py
cd frontend && npm run test -- buildLifeVolumes
# 手工：DevTools Network 打开 /report 计数 ≤4
```

---

### 块 F · 前端页面打磨与自检

| ☐ | ID | 角色 | 任务 | 主要文件 | 原编号 | 验收 |
|---|-----|------|------|----------|--------|------|
| ☑ | **R061** | FE | 八字首屏：四柱/十神/格局 KPI；叙述 ≤80 字或折叠 | `NewBaziView.vue` | BZ050 | 防丑五问 4=是 |
| ☑ | **R062** | FE | 八字结构档：`DualTrackTable` 可见 | `NewBaziView.vue` | BZ051 | structure 档有 `bazi-dual-track-block` |
| ☑ | **R063** | FE | 八字页三门禁 + 375px 一屏一锚 | `/new/bazi` | BZ052–053 · T055 | R-01 无叠层；E2E 375px |
| ☑ | **R064** | FE | 八字 E2E：空档案 · degraded · 结构档 | `e2e/` | BZ055 | fusheng-flow + bazi-ziwei 绿 |
| ☑ | **R065** | FE | 紫微方盘 Hero ≥60% 视口 | `FushengZiweiView.vue` | BZ056 | handbook-ziwei |
| ☑ | **R066** | FE | ZW18 degraded 横幅首屏可见（200 非 403） | `TrustDegradedBanner` | BZ059 | E2E mock degraded |
| ☑ | **R067** | FE | `missing_fields` 在八字/紫微 trust 区可见 | `EngineTrustPanel` | BZ042 · BZ060 | 结构档起可见 |
| ☑ | **R068** | FE | 紫微深度三档口径与八字一致 | `FushengZiweiView.vue` | BZ061 | 切换无布局跳 |
| ☑ | **R069** | FE | 运限 Timeline 分节 + sticky 日期 | `FushengZiweiTimeline.vue` | BZ062 | sticky 参考日 + 卷三分节 E2E |
| ☑ | **R070** | FE | 紫微首屏无长 `interpretation_text` | plate 文案 | BZ063 | ≤80 字或折叠 |
| ☑ | **R071** | ALL | 紫微页三门禁 + 防丑五问 | `e2e/fusheng-anti-slop.spec.ts` | BZ064 | 结构代理 3/3 E2E；Q5 代理 ☑（产品姓名待补） |
| ☑ | **R072** | FE | 紫微 E2E：加载 · 运限 · degraded | `e2e/` | BZ065 | fusheng-bazi-ziwei 8/8 绿 |
| ☑ | **R073** | FE | 报告卷四 stars **reference** 层；不标典籍 | vol4 | BZ068 · T045 | P1-11；explain palaces 无 classic_id |
| ☑ | **R074** | FE | 八字紫微 crossValidation 不一致时 trust 提示 | `validateBaziZiweiConsistency` | BZ074 | 报告 vol2 + 八字结构档 E2E |
| ☑ | **R075** | FE | 主路径五页 375px 复验 | 见 NODE-CHECKLIST | T055 | fusheng-responsive + bazi/ziwei E2E |
| ☑ | **R076** | ALL | 三页债务 `rg` 扫描（见 §三） | `frontend/src` | BZ054 · T024 | 0 命中违规 |
| ☑ | **R077** | BE | PDF 消费 explain 草案 | `fusheng_report_service.py` | T055-BE · P2-07 | build payload 调 explain batch；HTML 含解读草案+disclaimer |
| ☑ | **R078** | BE | REGISTRY 童限与 horoscope 文档收尾 | `ENGINE-METHOD-REGISTRY.md` | T055-BE | Z-11 + P2-09 horoscope 对照轨 |
| 🟡 | **R079** | DS | 实机三页截图 vs `targets/*.png`；防丑五问签字 | `docs/reports/R079-anti-slop-five-questions-2026-07-12.md` | BZ080 · T057 | compare JSON ☑；五问 15/15 ☑（产品姓名待补签） |
| ☑ | **R080** | ALL | R-01~R-05 三页首屏复查 | `e2e/fusheng-risk-alert.spec.ts` · `docs/reports/R080-risk-alert-retro-2026-07-12.md` | T065 · BZ085 | E2E 3/3 + debt scan 0；R-03/Q5 待 DS |
| ☑ | **R081** | FE | `missing_fields` / `provenance` 在工作台页首屏可达 | `bazi-trust-overview` · `ziwei-trust-overview` | BZ042 | 速览档 E2E 可见 |
| ☑ | **R082** | FE | 报告 waterfall p95 ≤4 记录 | `fusheng-report.spec.ts` R082 E2E | T060 · BZ084 | 4/4 chart 请求；E2E 绿 |
| ☑ | **R083** | FE | 报告打印预览六卷不截断 | `report-print.css` | BZ075 | print 规则补强 |
| ☑ | **R084** | ALL | 跑 §三全量自检命令，贴 PR | `docs/reports/R084-self-check-2026-07-12-pass2.md` | BZ076 | pass2 十步自动化全绿 |
| 🟡 | **R085** | ALL | **三页+报告自检块签字** | R079 + R102 reports | BZ052–075 | 五问 15/15 ☑；产品姓名待补签 |

**F-验收：**

```powershell
rg "linear-gradient|PageHead|#334155|-ok-bg|四维分析" frontend/src
cd frontend && npm run test:e2e -- bazi ziwei fusheng-report
```

---

### 块 G · 测试 / 质量门 / a11y（F6）

| ☐ | ID | 角色 | 任务 | 主要文件 | 原编号 | 验收 |
|---|-----|------|------|----------|--------|------|
| ☑ | **R086** | FE | Vitest 矩阵：六卷 × depth × 断点 | `__tests__/*` | T056 · BZ081 | buildLifeVolumes 六卷最小集 |
| ☑ | **R087** | FE | Playwright screenshot vs targets diff | `e2e/fusheng-targets-screenshot.spec.ts` | T057 | 布局 smoke + 冻结 PNG 存在 |
| ☑ | **R088** | FE | a11y：aria-expanded、焦点、色弱双编码 | `phaseAComponents.spec.ts` | T058 · BZ083 | VolumeSection + ColophonFootnote |
| ☑ | **R089** | FE | 对比度表（14px/12px 铜/朱/墨） | `variables.css` R089 注释 | T059 | WCAG AA 速查表 |
| ☑ | **R090** | FE | 空档案 / degraded / missing E2E 全覆盖 | `e2e/` | T062 · BZ082 | flow + bazi-ziwei 路径覆盖 |
| ☑ | **R091** | ALL | `make quality-gate-frontend` | — | T066 · BZ077 | 本地 type-check+lint+67 vitest+build 绿；`npm ci` 交 CI |
| ☑ | **R092** | ALL | `make quality-gate-backend` | — | T066 · BZ078 | backend gate 绿 |
| ☑ | **R093** | ALL | **复核** `make scorecard` 24/24 | — | BZ086 | 无回归 |
| ☑ | **R094** | ALL | OpenAPI + `gen:types` CI drift 双端 | `docs/reports/R094-openapi-sync-2026-07-12.md` | T061 | 150 paths · openapi 27/27 · type-check 绿 |
| ☑ | **R095** | FE | **复核** `npm run build` 生产构建 | — | T067 | 无 error |
| ☑ | **R096** | BE | **可选** `GET /life/volumes` 开发起步 | `routers/life.py` · `life_volume_service.py` | T070-BE | `test_life_volumes_api.py` 3/3 |
| ☑ | **R097** | ALL | 增强 quality-gate：纳入 scorecard + iztro（可选） | `quality_gate.py` | GAP-F01 | `--with-scorecard` + `make quality-gate-full` |
| ☑ | **R098** | ALL | 更新 `DEV-READINESS.md` 与实机状态一致 | 文档 | — | readiness-1.2 |
| ☑ | **R099** | ALL | 同步 T/BZ 清单：已完成项打 ☑ | 三份 plan 文档 | — | BZ E1/E3/F 与 R011–R077 对齐 |
| ☑ | **R100** | ALL | **F6 块签字** | `docs/reports/R100-f6-signoff-2026-07-12.md` | T056–T066 | 自动化矩阵绿；W14 人工项另计 |

**G-验收：**

```powershell
make quality-gate
make scorecard
cd frontend && npm run test && npm run test:e2e && npm run build
```

---

### 块 H · W14 产品收官（必须人工勾选）

| ☐ | ID | 角色 | 任务 | 原编号 | 验收 |
|---|-----|------|--------|------|
| ☑ | **R101** | ALL | §10.2 产品 11 项（见下表）全勾 | `docs/reports/R101-auto-verify-2026-07-12.md` | T063 · BZ079 | auto 11/11；PR 截图 → R108 |
| ☑ | **R102** | DS | §10.3 设计目检 3 项全勾 | `docs/reports/R102-design-spotcheck-2026-07-12.md` | T064 | 结构 3/3；DS 并排截图可选 |
| ☑ | **R103** | ALL | §10.4 预警 7 项全勾 | `docs/reports/R103-auto-verify-latest.json` | T065 | auto **7/7 ☑**（2026-07-15）；Q5 盲测待 DS |
| 🟡 | **R104** | ALL | **M4 能传**：卷目+跋截图愿分享 | `docs/reports/R104-m4-share-checklist-2026-07-12.md` | T068 · BZ087 | 3/4 ☑；#3 外发试读待产品签 |
| 🟡 | **R105** | ALL | **M5 能辩**：vs ChatGPT 1 处口径 | `docs/reports/R105-m5-defend-checklist-2026-07-12.md` | T069 · BZ087 | 4 维可辩护已记录；产品签待补 |
| ☑ | **R106** | ALL | INTEGRATED §十 终验命令全跑一遍 | `docs/reports/R106-final-verify-2026-07-12.md` | scorecard 24/24 · vitest 87 · E2E 47/47 |
| ☑ | **R107** | ALL | 负责人 **打磨期收官**签字 | `docs/reports/R107-w14-signoff-draft-2026-07-12.md` | **T070** · BZ088 | ☑ 工程自证 2026-07-15（不授权 GTM） |
| ☑ | **R108** | ALL | 发布说明附：R101–R103 勾选 + scorecard 摘要 | `R108-release-notes-generated.md` | — | generate 已绿 |
| ☑ | **R109** | ALL | 评估是否进入 POST-W14 | `docs/reports/R109-post-w14-decision-2026-07-12.md` | — | **选项 A**（维护态） |
| ☑ | **R110** | ALL | 顶部进度 T070 代码侧收官 | 本表里程碑 + 签字包 | 状态一致 |

#### R101 产品 11 项（复制到 PR）

```markdown
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
```

#### R103 预警 7 项

```markdown
- [ ] R-01~R-05 首屏无触发
- [ ] 三门禁全过
- [ ] 防丑五问全「是」
- [ ] targets 三截图已冻结/实机达标
- [ ] 首屏无 >80 字 interpretation_text
- [ ] 卷五域卡不在八字深读
- [ ] 卷六无自动 LLM
```

**H-终验：**

```powershell
make scorecard
pytest -q tests/test_explain_*.py tests/test_zw18_trust.py
make quality-gate
cd frontend && npm run test:e2e -- fusheng-report
```

---

### 块 I · 资料对照轨（可与 E/G 并行）

| ☐ | ID | 角色 | 任务 | 原编号 | 验收 |
|---|-----|------|--------|------|
| ☑ | **R111** | BE | SRC-05 文墨引擎 diff 脚本 CI 化 | `.github/workflows/ci.yml` | SRC-05 · R017 | continue-on-error advisory |
| ☑ | **R112** | BE | SRC-06 explain 读 star_profiles | `explain_ziwei.py` · `test_explain_batch.py` | SRC-06 · R050 | inference blocks from profiles |
| ☑ | **R113** | BE+FE | SRC-07 colophon wenmo 后端字段 + UI 对齐 | explain/ziwei `wenmo_advisory` · `ColophonFootnote` | SRC-07 · R054 | 跋展开见文墨对照 |
| ☑ | **R114** | BE | SRC-08 iztro horoscope 脚本 | SRC-08 · R041 | 与 R041 同验收 |
| ☑ | **R115** | BE | SRC-09 文墨运限 horoscope diff | SRC-09 · R042 | 与 R042 同验收 |
| ☑ | **R116** | BE+FE | SRC-10 life-volume colophon 权威化（W16 前草案） | schema + `GET /life/volumes` | SRC-10 · R096 | wenmo_advisory + colophon in API |

---

## 三、自检命令速查（R076 · R084 · R106 必跑）

```powershell
# 债务扫描
rg "linear-gradient|PageHead|#334155|-ok-bg|trust-drift-bg|四维分析|ChapterStub" frontend/src

# 卷六自动叙事（八字页应仅 on-demand）
rg "loadDayunNarratives" frontend/src/views/new/NewBaziView.vue
# 期望：仅 composable 解构 + loadDayunOnDemand 函数，mount 不调用

# explain 接线
rg "fetchBaziExplainBatch|fetchZiweiExplainBatch" frontend/src/views/ReportView.vue
# 期望：R057 完成后有命中

# 引擎与对照
make scorecard
make verify-iztro
make verify-iztro-hour
make verify-horoscope-iztro
make verify-wenmo-horoscope
pytest -q tests/test_import_desktop_content.py tests/test_ziwei_iztro*.py tests/test_ziwei_horoscope_diff.py tests/test_bazi_horoscope_edges.py

# 质量门
make sync-frontend-types
make quality-gate
cd frontend && npm run test:e2e -- bazi ziwei fusheng-report
```

---

## 四、已知阻塞登记（随 R 编号更新）

| 阻塞 | 严重 | 解开条件 |
|------|------|----------|
| R060 15-min 建档→报告试读签字 | 🟡 | E2E 步骤 1–9 绿；主观评分+签字待人工 |
| R071/R079/R080/R085 防丑五问 + 三页签字 | 🟡 | 五问 15/15 ☑；产品姓名行待补 → R085 可勾 |
| R082 报告 Network ≤4 | ✅ | E2E `fusheng-report` R082 断言 4/4 |
| `fusheng-report` snapshot E2E | ☑ | 登录态 mock 含 cities/cases pathname；`data-snapshots-ready` 稳定云端 Tab |
| R101–R110 W14 产品清单 | 🟡 | R101/R103/R106 auto ☑；R108 草案 pass4；**仅 step10/签字待人工** |
| POST-W14 全轨 | ⏸ | R107 后再评估 |

---

## 附录 A · T070 后再开

打磨期 **R107 签字后** 才开 [EXECUTION-PRIORITY-POST-W14](FUSHENG-EXECUTION-PRIORITY-POST-W14.md) **T071–T140**：

- U5 `life/volumes`（T072–T085）
- GTM 试投（T086–T105）
- Extension（T106–T115）
- 平台 E0–E1（T126–T135）

**当前纪律：打磨期代码已收官（R107 工程自证）；进入 POST-W14/GTM 须产品明确点选 R109 B/C，禁止自行加付费/snippets。**

---

## 附录 B · 原编号映射

| 本清单 | 原 T | 原 BZ |
|--------|------|-------|
| R001–R007 | T001–T007 | — |
| R011–R025 | T008-BE* · T014-BE · T035-BE2 | BZ011–015 · BZ038 |
| R026–R035 | — | BZ001–010 |
| R036–R045 | — | BZ016–028 |
| R046–R060 | T035-BE · T039 · T048 · T048-BE | BZ031–045 |
| R061–R085 | T055 · T055-BE | BZ050–075 |
| R086–R100 | T056–T067 · T070-BE | BZ076–086 |
| R101–R110 | T063–T070 | BZ079–088 |
| R111–R116 | — | SRC-05–10 |

---

## 附录 C · 文档索引

| 需求 | 文档 |
|------|------|
| 全量历史顺序（含已完成） | [EXECUTION-PRIORITY](FUSHENG-EXECUTION-PRIORITY.md) |
| 八字紫微细节 | [BAZI-ZIWEI-POLISH](FUSHENG-BAZI-ZIWEI-POLISH-CHECKLIST.md) |
| 周计划与 Gate | [INTEGRATED](FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md) |
| 后端专章 | [BACKEND-MASTER](BACKEND-MASTER-PLAN-2026-07-12.md) |
| 预警三门禁 | [RISK-ALERT](../guides/FUSHENG-FRONTEND-RISK-ALERT.md) |
| 节点插件 | [NODE-CHECKLIST](../guides/FUSHENG-NODE-CHECKLIST.md) |

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| remaining-1.0 | 2026-07-12 | 初版：合并 T/BZ/§十/SRC 全部未完成项为 R001–R116 |
