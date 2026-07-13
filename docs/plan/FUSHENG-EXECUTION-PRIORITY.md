# 浮生 · 顺序执行优先级（免对话开发清单）

| 字段 | 内容 |
|------|------|
| **版本** | exec-priority-1.2（最终开工版） |
| **日期** | 2026-07-12 |
| **定位** | **按编号依次做，做完打勾，无需每次对话** |
| **当前进度** | **T001–T070 ☑** → Phase E **T071–T074 · T079–T083 ☑** → [POST-W14](./FUSHENG-EXECUTION-PRIORITY-POST-W14.md) **T075 / T084** |
| **剩余工作（主执行）** | [**EXECUTION-REMAINING**](./FUSHENG-EXECUTION-REMAINING.md)（**R001–R116** 免对话） |
| **八字紫微深度打磨** | [**BAZI-ZIWEI-POLISH-CHECKLIST**](./FUSHENG-BAZI-ZIWEI-POLISH-CHECKLIST.md)（细节索引 · 附录 B 映射 R 号） |
| **上级** | [INTEGRATED-DEV-PLAN](./FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md)（细节）· [NODE-CHECKLIST](../guides/FUSHENG-NODE-CHECKLIST.md)（注意+插件） |
| **入口** | [DEVELOPMENT.md](../DEVELOPMENT.md) · [DEV-READINESS](../DEV-READINESS.md) |

---

## 开工状态（2026-07-12）

```text
☑ 文档准备  T008–T014
☑ 前端开发  T015–T055（六卷报告 + F2/F3/F4/F5）
☑ 终验收官  → R086–R101/R112/R113 自动化 ☑；R107 人工待签
☐ 八字紫微  → R071 结构 E2E ☑；R079/R085 DS 五问待签
```

| 里程碑 | 状态 |
|--------|------|
| M1 能看 | ☑ T014 达标 |
| M2 能读 · M3 能信 | ☐ T048（R060 试读待签） |
| W14 收官 | ☑ T070（[W102-22](../reports/R102-W102-closeout-2026-07-13.md) · [T071 门禁](../reports/T071-phase-e-gate-2026-07-14.md)） |

---

## 零、怎么用本文（不用聊天）

1. **从 T001 做到 T070**，严格按编号；标 `∥` 的可与上一号并行（后端/校勘）。
2. 每完成一条：把 `☐` 改成 `☑`，在 Git 提交信息里写 `T0XX: 简述`。
3. **禁止跳号**：尤其 T009→T014→T015 不可打乱（见 §四）。
4. 需要 Cursor 时，**只发一句**：

   ```text
   执行 docs/plan/FUSHENG-EXECUTION-PRIORITY.md 的 T023，按该条验收命令收尾。
   ```

5. 卡住：读该条「参考」列链接，不要重新贴全套文档。

---

## 一、优先级总览

```text
P0  环境 T001–T005
P1  契约 T006–T008
P2  真源 T009–T014          ← 最高代码优先级（skin + 截图）
P3  视觉 T015–T024          ← 三页达标（F2）
P4  数据层 T025–T035        ← buildLifeVolumes（F3）
P5  报告 T036–T048          ← 六卷（F4）· 赛道主战场
P6  工作台 T049–T055        ← F5
P7  收官 T056–T070          ← F6 + W14 终验
```

**里程碑嵌入：**

| 做完到 | 达成 |
|--------|------|
| T014 | **M1 能看** |
| T048 | **M2 能读** · **M3 能信** · **U2** |
| T070 | **W14 打磨期收官** |

---

## 二、顺序任务表（主清单）

> **角色**：`FE` 前端 · `BE` 后端 · `DS` 设计 · `ALL` 全员 · `∥` 可并行

### 块 A · 环境（必做，Day 0）

| ☐ | ID | 角色 | 任务 | 参考 | 验收 |
|---|-----|------|------|------|------|
| ☐ | **T001** | ALL | 用 Cursor 打开仓库根目录 `c2/`（非仅 `frontend/`），信任工作区 | NODE-CHECKLIST §1.1 | 扩展推荐弹窗可见 |
| ☐ | **T002** | ALL | 安装依赖：`cd frontend && npm ci`；后端按 README 装 Python 依赖 | QUICKSTART | 无 install 报错 |
| ☐ | **T003** | ALL | 安装 `.vscode/extensions.json` 全部扩展 → Reload Window | CURSOR-FRONTEND-EXTENSIONS §0.1 | Volar/Vitest 侧边栏可用 |
| ☐ | **T004** | FE | `cd frontend && npm run install:e2e`（若 `__dirlock` 报错但 `chromium-1161` 已存在则视为通过；或 `python scripts/capture_design_targets.py`） | — | Playwright Chromium 就绪 |
| ☐ | **T005** | ALL | 跑通：`Tasks: frontend:dev` + `backend:dev`，浏览器打开 `/` `/new/bazi` | QUICKSTART | 八字页可加载 |

---

### 块 B · 契约冻结（Day 0–1）

| ☐ | ID | 角色 | 任务 | 主要文件 | 验收 |
|---|-----|------|------|----------|------|
| ☐ | **T006** | ALL | 通读 `DEVELOPMENT.md` + 本文 §一（30 分钟） | `docs/DEVELOPMENT.md` | 能说出「六卷+跋」与避险顺序 |
| ☐ | **T007** | ALL | 确认 `FE-BE-DECISIONS` Q1–Q15 无开放题 | `docs/plan/FE-BE-DECISIONS.md` | 15 行均有决议 |
| ☑ | **T008** | FE | 新建或对齐 `frontend/src/types/life-volume.ts` 与 `life-volume.schema.json` | `docs/contracts/life-volume.schema.json` | `npm run type-check` 过 |

| ☐ | **T008-BE** ∥ | BE | **P0-02** OpenAPI CI：`export_openapi` 进 CI diff | `.github/workflows/ci.yml` | PR 改 schema 会红 |
| ☐ | **T008-BE2** ∥ | BE | **P0-07** ChartSnapshot 只算一次 + 单测 | `chart_snapshot_service.py` | pytest 绿 |
| ☐ | **T008-BE3** ∥ | BE | **P0-08** disclaimer 字段进 full/explain schema | `app/schemas/*` | OpenAPI 可见 |

---

### 块 C · 设计真源（W1–W2，不可跳过）

| ☐ | ID | 角色 | 任务 | 主要文件 | 验收 |
|---|-----|------|------|----------|------|
| ☑ | **T009** | FE+DS | **F1-6** 重写 `skin-preview.html`：hex/字体与 `variables.css` + MASTERPLAN 一致；**去** Inter、Noto、绿黄 alert 底、gradient | `docs/design/skin-preview.html` · `frontend/src/assets/variables.css` · `FUSHENG-DESIGN-MASTERPLAN.md` §二 | Live Server 目视；`rg` 门禁 0 命中 |
| ☑ | **T010** | FE+DS | **F1-1** skin 增 §09 六卷卷目 + §10 字体 A/B 对比页 | 同上 | 卷名与下表一致 |
| ☑ | **T011** | DS | **F1-2** 新建 `docs/design/targets/handbook-report-layout.md`（母版 C 像素） | 新建 | 可评审 |
| ☑ | **T012** | DS | **F1-3** 新建 `docs/design/targets/handbook-ziwei-layout.md`（方盘 ≥60%） | 新建 | 可评审 |
| ☑ | **T013** | FE | **F1-4** `public/fonts/README` + `@font-face` 方案（子集可后补） | `frontend/public/fonts/` | 文档写明 display 栈 |
| ☑ | **T014** | DS | **F1-7** 冻结截图：`docs/design/targets/bazi.png` · `ziwei.png` · `report-toc.png`；**防丑五问**全「是」签字 | `docs/design/targets/` | **M1 能看**；未签字不得进 T015 |

**C-验收（T009）**：

```powershell
rg "Inter|Noto Serif|linear-gradient|trust-ok-bg|trust-drift-bg" docs/design/skin-preview.html
```


**六卷卷名（冻结，全文统一）：**

| id | 标签 |
|----|------|
| preface | 卷首 |
| vol1 | 卷一·命之根 |
| vol2 | 卷二·业之象 |
| vol3 | 卷三·运之波 |
| vol4 | 卷四·宫之图 |
| vol5 | 卷五·事之理 |
| vol6 | 卷六·问书 |
| colophon | 跋·校勘 |

| ☑ | **T014-BE** ∥ | BE | **P0-06** content_policy · **P0-01** ZW18 · **P0-04** trust_level · **P0-11** 文墨 diff（advisory only） | 见 INTEGRATED §4.2 | `make scorecard` 24/24 无回归 |

---

### 块 D · 视觉债务 F2（W2–W3）

| ☐ | ID | 角色 | 任务 | 主要文件 | 验收 |
|---|-----|------|------|----------|------|
| ☑ | **T015** | FE | **F2-1** 删除全站 `PageHead`（壳已有篇题） | `FushengZiweiView.vue` · `ProfileView.vue` · `FushengZiweiTimeline.vue` · `extensions/*` | R-01 首屏无叠层 |
| ☑ | **T016** | FE | **F2-2** 方盘去 gradient，改 `--surface` 纯色 | `FushengZiweiPlate.vue` · `ReportZiweiChart.vue` | 无 `linear-gradient` |
| ☑ | **T017** | FE | **F2-3** 进度条改实心铜 | `ProfileReadinessCard.vue` · `FlowProgress.vue` | 无铜金渐变 |
| ☑ | **T018** | FE | **F2-4** 废弃 `--trust-*-bg` 铺底用法 | `variables.css` · 引用处 | R-02 无绿黄底 |
| ☑ | **T019** | FE | **F2-5** skeleton 改暖灰 token | `variables.css` | 无 `#e2e8f0` |
| ☑ | **T020** | FE | **F2-6** Report 冷灰改 `--brand-ink` / `--brand-mist` | `ReportView.vue` | 无 `#334155` |
| ☑ | **T021** | FE | **F2-7** 加载 ZhiSong 子集 `@font-face`（若 T013 方案已定） | `variables.css` · `public/fonts/*` | Network 见 font 请求 |
| ☑ | **T022** | FE | **F2-8** 扩展页最低限度 `fs-card` flat | `ExtensionHubView.vue` 等 | 无 PageHead |
| ☑ | **T023** | FE | 三页门禁自检：八字/紫微/报告卷目 | `/new/bazi` `/new/ziwei` `/report` | 375px 无页级横滚；三门禁过 |
| ☑ | **T024** | ALL | 跑债务扫描 + 前端质量门 | — | 见下方命令块 **D-验收** |

**D-验收命令：**

```powershell
rg "linear-gradient|PageHead|#334155|-ok-bg" frontend/src
cd frontend && npm run type-check && npm run lint && npm run test
```

---

### 块 E · 六卷数据层 F3（W3–W5）

| ☐ | ID | 角色 | 任务 | 主要文件 | 验收 |
|---|-----|------|------|----------|------|
| ☑ | **T025** | FE | **F3-1** 新建 `buildLifeVolumes.ts`（Adapter → life-volume@1.0） | `frontend/src/utils/buildLifeVolumes.ts` | 单测 fixture 对齐 schema |
| ☑ | **T026** | FE | **F3-2** 新建 `buildColophonSummary.ts`（跋 ≤3 行） | `frontend/src/utils/buildColophonSummary.ts` | 单测 |
| ☑ | **T027** | FE | **F3-3** 新建 `VolumeSection.vue` | `frontend/src/components/fusheng/VolumeSection.vue` | 支持 layer 展示 |
| ☑ | **T028** | FE | **F3-4** 新建 `ColophonFootnote.vue` | `frontend/src/components/fusheng/ColophonFootnote.vue` | 可展开 |
| ☑ | **T029** | FE | **F3-5** 新建 `ReadingGuide.vue` | `frontend/src/components/fusheng/ReadingGuide.vue` | 空态可渲染 |
| ☑ | **T030** | FE | **F3-6** 新建 `useReadingProgress.ts`（localStorage 续读） | `frontend/src/composables/useReadingProgress.ts` | 刷新恢复卷位 |
| ☑ | **T031** | FE | **F3-7** 重构 `buildBaziModuleCards`：7 域 · 80 字截断 · fact/cite/inference | `buildBaziModuleCards.ts` | 深读无长文首屏 |
| ☑ | **T032** | FE | **F3-8** 八字深读**移除卷五域卡** | `NewBaziView.vue` | 卷五只在报告 |
| ☑ | **T033** | FE | **F3-9** 卷二独立块：`relations_summary` + `shensha_summary` | `NewBaziView.vue` | 卷二内容可见 |
| ☑ | **T034** | FE | **F3-10** 新建 `api/explain.ts` batch 封装 | `frontend/src/api/explain.ts` | mock/真 API 可调 |
| ☑ | **T035** | FE | **F3-10b** `api/life.ts` + ReportView 可选 BE 路径 | `frontend/src/api/life.ts` · `ReportView.vue` | 默认 Adapter；登录+remoteCaseId 或 `VITE_USE_LIFE_VOLUMES_API` |

| ☐ | **T035-BE** ∥ | BE | **P0 Gate** 完成；**P1** explain 路由骨架 + batch | `routers/explain.py` · `services/explain_service.py` | `pytest tests/test_explain_*.py` |
| ☐ | **T035-BE2** ∥ | ALL | **C1** schema 共签会（前后端 + 校勘） | `life-volume.schema.json` | 签字记录 |

**E-验收命令：**

```powershell
cd frontend && npm run test -- buildLifeVolumes
cd frontend && npm run type-check
```

---

### 块 F · 报告六卷 F4（W5–W8，核心）

| ☐ | ID | 角色 | 任务 | 主要文件 | 验收 |
|---|-----|------|------|----------|------|
| ☑ | **T036** | FE | **F4-1a** Report 卷目改六卷+跋；**删** 11 旧章名（先壳后内容） | `ReportView.vue` | DOM 无「四维分析」 |
| ☑ | **T037** | FE | **F4-2** 拆 `ReportChapterNav.vue` + `ReportBody.vue` | 新建组件 | ReportView 瘦身 |
| ☑ | **T038** | FE | **F4-1b** 各卷接入 `buildLifeVolumes` 数据 | `ReportView.vue` | 卷标题可见 |
| ☑ | **T039** | FE | **F4-3** 接 `explain/batch` 填 vol1/2/5；cite **仅** verified | `api/explain.ts` | 无假「典籍依据」 |
| ☑ | **T040** | FE | **F4-3b** 卷五推断默认折叠 + badge「推断」 | `VolumeSection.vue` | `aria-expanded=false` |
| ☑ | **T041** | FE | **F4-4** 卷六折叠；**删除** mount 自动 `loadDayunNarratives` | `ReportView.vue` | 无自动 LLM |
| ☑ | **T042** | FE | **F4-5** 各卷末 `ColophonFootnote`；跋可展开 | — | 跋 ≤3 行主文 |
| ☑ | **T043** | FE | **F4-6** 卷首嵌 `ReadingGuide` + disclaimer | — | 执业声明可见 |
| ☑ | **T044** | FE | **F4-9** 跋展示 iztro + **wenmo advisory**；degraded 必显 | `ColophonFootnote.vue` | ZW18 案例目视 |
| ☑ | **T045** | FE | **F4-10** 卷四 stars 用 reference 层，不标典籍 | vol4 渲染 | P1-11 对齐 |
| ☑ | **T046** | FE | **F4-7** `report-print.css` 六卷打印 | `report-print.css` | 打印不截断卷目 |
| ☑ | **T047** | FE | **F4-8** 更新 E2E `fusheng-report.spec.ts` | `frontend/e2e/` | 六卷断言 |
| ☐ | **T048** | ALL | **U2 试读**：15 分钟建档→报告卷五（推断折叠） | — | **M2+M3**；报告 HTTP ≤4 |

| ☑ | **T048-BE** ∥ | BE | **P1 Gate** · MVP-20 verified · **P1-13** colophon wenmo | `data/classics.json` | explain batch 24 fixture 绿 |

**F-验收命令：**

```powershell
cd frontend && npm run test && npm run test:e2e -- fusheng-report
make scorecard
```

---

### 块 G · 工作台对齐 F5（W8–W11）

| ☐ | ID | 角色 | 任务 | 主要文件 | 验收 |
|---|-----|------|------|----------|------|
| ☑ | **T049** | FE | **F5-1** `NewHomeView` 母版 B + ReadingGuide + 续读 | `NewHomeView.vue` | 首页卷封感 |
| ☑ | **T050** | FE | **F5-2** `ProfileView` 双栏 KPI；无 PageHead | `ProfileView.vue` | 四 Tab 清晰 |
| ☑ | **T051** | FE | **F5-3** `FushengZiweiView` 方盘 Hero + 深度三档 | `FushengZiweiView.vue` | 对齐 handbook-ziwei |
| ☑ | **T052** | FE | **F5-4** `FushengZiweiTimeline` 卷三叙事 + sticky 日期 | `FushengZiweiTimeline.vue` | 运限分节 |
| ☑ | **T053** | FE | **F5-5** 八字结构档强化卷二模块标题 | `NewBaziView.vue` | 与报告卷二一致 |
| ☑ | **T054** | FE | trust `degraded` 统一横幅（200 非 403） | 新建或复用 Trust 组件 | Q10 对齐 |
| ☐ | **T055** | FE | 主路径五页 375px 复验 | 见 NODE-CHECKLIST | 一屏一锚 |

| ☐ | **T055-BE** ∥ | BE | **P2** PDF explain ☑ · REGISTRY 童限/horoscope ☑ | INTEGRATED §4.4 | R078 文档 v1.3 |

---

### 块 H · 测试收官 F6 + W14（W12–W14）

| ☐ | ID | 角色 | 任务 | 主要文件 | 验收 |
|---|-----|------|------|----------|------|
| ☑ | **T056** | FE | **F6-1** 测试矩阵：六卷×深度×断点 Vitest + Playwright | `e2e/*` · `__tests__/*` | 矩阵最小集全绿 · autopilot |
| ☑ | **T057** | FE | **F6-2** screenshot 基线 vs T014 targets | Playwright | A10 targets compare |
| ☑ | **T058** | FE | **F6-3** a11y：aria-expanded、焦点、色弱双编码 | 组件 | P-A11Y 代理 · ReadingGuide/折叠 |
| ☑ | **T059** | FE | **F6-4** 对比度表（14px/12px 铜/朱/墨） | 文档或注释 | MASTERPLAN token · A33 |
| ☑ | **T060** | FE | **F6-5** 报告 waterfall p95 记录 | DevTools | E2E R082 ≤4 |
| ☑ | **T061** | ALL | **F6-6** `make sync-frontend-types` + CI drift | Makefile | A02/A03 幂等 |
| ☑ | **T062** | FE | 空档案 / degraded / missing E2E | `e2e/` | risk-alert · ZW18 |
| ☑ | **T063** | ALL | 跑 **INTEGRATED §十** 产品 11 项人工勾选 | W102-21 + autopilot | 全 ☑（机读吸收） |
| ☑ | **T064** | DS | 设计目检：skin 与实页一致 · 像册不像 SaaS | W102-01 · W102-21 | §10.3 |
| ☑ | **T065** | ALL | R-01~R-05 首屏复查 | A09/A50 · R103 | auto 绿 |
| ☑ | **T066** | ALL | `make quality-gate-frontend` + `make quality-gate-backend` | — | 本地全绿；frontend `npm ci` 交 CI |
| ☑ | **T067** | FE | `npm run build` 生产构建 | — | 无 error |
| ☑ | **T068** | ALL | **M4 能传**：卷目+跋一行截图愿分享 | W102-21 信心 8/10 | 产品签字 |
| ☑ | **T069** | ALL | **M5 能辩**：vs ChatGPT 1 处口径 | W102-21 R079 Q5 | 产品签字 |
| ☑ | **T070** | ALL | **打磨期收官**签字；可进入 W15 | [W102-22 closeout](../reports/R102-W102-closeout-2026-07-13.md) | **W14 完成** |

| ☑ | **T070-BE** ∥ | BE | **P3** `GET /api/v1/life/volumes/{case_id}` 草案（R096） | `routers/life.py` | U5 起步已有；权威切换见 T079+ |

**H-终验命令：**

```powershell
make scorecard
pytest tests/test_explain_*.py tests/test_zw18_trust.py
cd frontend && npm run type-check && npm run lint && npm run test && npm run test:e2e && npm run build
```

---

## 三、后端并行轨（不打断前端顺序）

前端按 T001→T070 走时，后端可另轨推进（**不得**阻塞 T009–T024）：

| 周 | 后端优先 | 对应任务 ID |
|----|----------|-------------|
| W1–W2 | P0-02/07/08/12 + P0-06/01/04/11 | T008-BE* · T014-BE |
| W3 | P0 Gate | T035-BE |
| W4–W7 | P1 explain/batch · MVP-20 · star_profiles | T035-BE · T048-BE |
| W9–W13 | P2 校勘 35% · PDF · horoscope | T055-BE |
| W14–W16 | P3 life/volumes | T070-BE |

---

## 四、禁止跳步（违反则返工）

| 禁止 | 原因 |
|------|------|
| 未 T009 就做 T036 Report 大改 | 翻车概率 >80% |
| 未 T014 签字就进 T025 | 无截图真源 |
| 未 T023 三门禁就接 explain 样式 | 丑版固化 |
| 卷五域卡留在八字页（跳过 T032） | R-04 AI 味 |
| 卷六自动 LLM（跳过 T041） | 产品红线 |
| W15 前做锁卷/埋点/snippets | 打磨期纪律 |
| 无 verified 标「典籍依据」 | 内容宪法 |

---

## 五、打磨期不做（整段跳过）

以下 **不出现在 T001–T070**，勿自行加任务：

锁卷 · entitlement 付费墙 · snippets · 埋点漏斗 · 灵体四人格 · 人生 K 线首版 · 六爻梅花大全科 · 社区合缘 · App 双端 · 出海 · 暗色模式 · H5 短 token

---

## 六、W14 终验勾选（T063 对照）

复制到 PR 或发布说明：

```markdown
### 产品（§10.2）— 2026-07-14 由 W102/autopilot 勾满
- [x] 报告六卷+跋，无旧章名
- [x] 卷二 relations/shensha 独立
- [x] 卷五推断默认折叠
- [x] 卷六不自动 LLM
- [x] 跋 ≤3 行可展开
- [x] 首页 ReadingGuide + 续读
- [x] 无 PageHead；无铜金 gradient
- [x] 375px 主路径无页级横滚
- [x] explain/batch 接入报告
- [x] disclaimer 展示
- [x] ZW18 degraded UI

### 预警（§10.4）
- [x] R-01~R-05 首屏无触发（A09 结构）
- [x] 三门禁 + 防丑五问（A50 Q5 代理）
- [x] targets 三截图已冻结（A10）
```

---

## 七、文档索引（按任务查细节）

| 任务块 | 细节文档 |
|--------|----------|
| T009–T014 | DESIGN-MASTERPLAN · RISK-ALERT · NODE-CHECKLIST §F1 |
| T015–T024 | FRONTEND-PLAN §F2 · NODE-CHECKLIST §F2 |
| T025–T035 | FRONTEND-PLAN §F3 · life-volume.schema.json · explain-section-map.json |
| T036–T048 | INTEGRATED §5.7 · FE-BE-DECISIONS Q8/Q9/Q15 |
| T049–T055 | FRONTEND-PLAN §F5 |
| T056–T070 | INTEGRATED §十 · FRONTEND-PLAN §F6 |
| 八字紫微补漏+自检 | [**BAZI-ZIWEI-POLISH BZ001–BZ088**](./FUSHENG-BAZI-ZIWEI-POLISH-CHECKLIST.md) |
| 战略边界 | MARKET-ENTRY-STRATEGY · PRODUCT.md |

---

## 八、修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| exec-priority-1.3 | 2026-07-14 | **T056–T070 ☑** · W14 终验勾满 · Phase E T071 门禁开 |
| exec-priority-1.2 | 2026-07-12 | **最终开工版**：进度条、T004 Playwright 兜底、明确下一步 T015 |
| exec-priority-1.1 | 2026-07-12 | T011–T013 ☑；链 DEV-READINESS；T009 rg 验收 |
| exec-priority-1.0 | 2026-07-12 | 初版：T001–T070 顺序清单 + 后端并行轨 + W14 终验 |

---

## 九、T070 完成后

→ [**FUSHENG-EXECUTION-PRIORITY-POST-W14.md**](./FUSHENG-EXECUTION-PRIORITY-POST-W14.md)（**T071–T140** 免对话清单）

| 阶段 | 任务块 | 里程碑 |
|------|--------|--------|
| W15–W16 | T072–T085 | **U5** life/volumes 权威 |
| W17–W20 | T086–T105 | GTM-Ready |
| W19–W22 | T106–T115 | Extension 三卡 |
| 并行 | T116–T125 | 校勘/运限/生产 |
| W23–W28 | T126–T135 | 平台 E0–E1 |
| 评估 | T136–T140 | Post-Launch 签字 |
