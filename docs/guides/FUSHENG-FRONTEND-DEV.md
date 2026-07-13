# 浮生 · 前端开发手册（唯一入口）

| 字段 | 内容 |
|------|------|
| **版本** | fe-dev-1.0 |
| **日期** | 2026-07-12 |
| **定位** | **前端相关开发文档的唯一权威** — 合并 UI 开发、方案、预警、上手、环境 |
| **全栈入口** | [`DEVELOPMENT.md`](../DEVELOPMENT.md) |
| **规矩·命令·插件** | [**`FUSHENG-DEV-AUTOPILOT.md`**](../FUSHENG-DEV-AUTOPILOT.md) ← **全自动权威** |
| **执行打勾** | [`FUSHENG-DEV-PIPELINE`](../FUSHENG-DEV-PIPELINE.md) · BZ 细节见 [BAZI-ZIWEI-POLISH](../plan/FUSHENG-BAZI-ZIWEI-POLISH-CHECKLIST.md) |

> **一句话**：算法写命盘，典籍写讲解，**前端编成书** — 宋式六卷辑录；UI 只暴露 **排盘推算 / 典籍依据 / 经验推断** 三层语义。

**本文已合并（勿再扩写旧文件）：**

| 原文件 | 现归属 |
|--------|--------|
| `FUSHENG-FRONTEND-UI-DEV.md` | §4–§8 |
| `FUSHENG-FRONTEND-PLAN.md` | §10–§12、§14 |
| `FUSHENG-FRONTEND-RISK-ALERT.md` | §9 |
| `FUSHENG-QUICKSTART.md` 前端节 | §2 |
| `FUSHENG-NODE-CHECKLIST.md` F 节点 | §3、§10 |
| 视觉定案全文 | [`FUSHENG-DESIGN-MASTERPLAN`](../design/FUSHENG-DESIGN-MASTERPLAN.md)（外链，不重复） |

---

## 一、30 秒：按角色跳转

| 你是谁 | 先读 |
|--------|------|
| **新人 / 跑项目** | [§2 快速上手](#二快速上手) |
| **改 UI / 布局** | [§5 视觉定案](#五视觉与布局定案) · [§8 组件库](#八组件库) |
| **接 API / 报告六卷** | [§7 前后端适配](#七前后端适配-fe-be) |
| **合并 PR 前** | [§9 预警门禁](#九预警与质量门禁) · [§12 验收](#十二验收命令) |
| **设计 / DS** | MASTERPLAN + `skin-preview.html` + [§9.4 防丑五问](#94-防丑五问) |
| **Cursor 插件细节** | [`CURSOR-FRONTEND-EXTENSIONS.md`](./CURSOR-FRONTEND-EXTENSIONS.md) |
| **八字/紫微对话模板** | [`CURSOR-BAZI-ZIWEI-PLAYBOOK.md`](./CURSOR-BAZI-ZIWEI-PLAYBOOK.md) |

**权威分工（消除双真源）：**

| 内容 | 唯一权威 |
|------|----------|
| **前端开发全文** | **本文** |
| 色/字/母版像素 | `FUSHENG-DESIGN-MASTERPLAN.md` |
| 阶段周计划（BE+FE） | `FUSHENG-INTEGRATED-DEV-PLAN.md` §五 |
| 顺序打勾 | `FUSHENG-EXECUTION-REMAINING.md` |
| 15 题接口决议 | `FE-BE-DECISIONS.md` |
| 六卷 JSON | `contracts/life-volume.schema.json` |
| explain 映射 | `contracts/explain-section-map.json` |

---

## 二、快速上手

### 2.1 10 分钟跑起来

```powershell
# 项目根 — 后端
python -m uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm ci
npm run dev
```

访问：`http://localhost:5173`（或 Vite 提示端口）→ `/` · `/new/bazi` · `/report`

### 2.2 改什么去哪个文件

| 要改什么 | 路径 |
|----------|------|
| 应用壳 / 导航 | `frontend/src/components/new/NewAppShell.vue` |
| 首页 | `frontend/src/views/new/NewHomeView.vue` |
| 八字盘面 | `frontend/src/views/new/NewBaziView.vue` |
| 紫微方盘 | `frontend/src/views/new/FushengZiweiView.vue` |
| 运限 | `frontend/src/views/new/FushengZiweiTimeline.vue` |
| 报告六卷 | `frontend/src/views/ReportView.vue` |
| 六卷数据拼装 | `frontend/src/utils/buildLifeVolumes.ts` |
| FE-BE 适配 | `frontend/src/utils/feBeAdapter.ts` · `constants/feBeContract.ts` |
| API 客户端 | `frontend/src/api/{bazi,ziwei,explain,life}.ts` |
| 样式 Token | `frontend/src/assets/variables.css` |
| 页面工具类 | `frontend/src/assets/fusheng-page.css` |
| OpenAPI 类型 | `npm run gen:types` → `frontend/src/api/schema.d.ts` |

### 2.3 契约（必知）

- 六卷形状：`docs/contracts/life-volume.schema.json`
- explain → 卷映射：`docs/contracts/explain-section-map.json`
- TypeScript：`frontend/src/types/life-volume.ts`

---

## 三、环境与工具

### 3.1 仓库与环境

| 步骤 | 要求 |
|------|------|
| 打开根目录 | **必须** `c2/` 根，不要只开 `frontend/` |
| 信任工作区 | Cursor → Trust Workspace |
| Node | 18+ · `cd frontend && npm ci` |
| Playwright | `cd frontend && npm run install:e2e` |
| 字体 | `frontend/public/fonts/LXGWNeoZhiSong-subset.woff2`（Network 200） |

### 3.2 VS Code / Cursor Tasks

`Ctrl+Shift+P` → **Tasks: Run Task**：

| Task | 用途 |
|------|------|
| `frontend:dev` | 本地目视 |
| `frontend:type-check` | 每 PR |
| `frontend:test` | Vitest |
| `frontend:lint` | ESLint |
| `frontend:e2e` | Playwright |
| `backend:dev` | 接 explain / life API |

### 3.3 推荐扩展（摘要）

来源 `.vscode/extensions.json` → **Install All** → Reload。

| 分类 | 扩展 | 用途 |
|------|------|------|
| 核心 | Vue.volar · ESLint | `.vue` / TS |
| 设计 | colorize · cssvar · Live Server | Token · skin-preview |
| 测试 | vitest.explorer · Playwright | 单测 · E2E |

完整说明 → [`CURSOR-FRONTEND-EXTENSIONS.md`](./CURSOR-FRONTEND-EXTENSIONS.md)

### 3.4 环境变量

| 变量 | 作用 |
|------|------|
| `VITE_DEV_API_TARGET` | 开发 API 代理（默认 `http://127.0.0.1:8000`） |
| `VITE_USE_LIFE_VOLUMES_API=true` | 报告强制走 `GET /life/volumes` |

---

## 四、产品路径与六卷 IA

### 4.1 用户主路径

```text
/ 首页 → /profile 档案 → /new/bazi 八字 | /new/ziwei 紫微 → /report 报告（六卷+跋）
```

| 路由 | 视图 | 母版 | 卷目叙事 |
|------|------|------|----------|
| `/` | `NewHomeView.vue` | A · 卷首 | ReadingGuide + 续读 + VolumeTocGrid |
| `/profile` | `ProfileView.vue` | B · 双栏 | 档案 KPI |
| `/new/bazi` | `NewBaziView.vue` | A · 盘面 | 卷一·命之根 |
| `/new/ziwei` | `FushengZiweiView.vue` | A · Hero | 卷四·宫之图 |
| `/new/ziwei/timeline` | `FushengZiweiTimeline.vue` | A | 卷三·运之波 |
| `/report` | `ReportView.vue` | C · 连续读 | 全书 |

**壳**：`NewAppShell.vue`（56px 顶栏 + 篇题/卷名 eyebrow）。**禁止**页内再叠 `PageHead` 双标题。

**路由 ↔ 卷名**：`composables/useVolumeRouteMeta.ts`

### 4.2 六卷 IA（冻结）

| ID | 卷名 | 主要内容 |
|----|------|----------|
| `preface` | 卷首 | 读法导览、disclaimer |
| `vol1` | 卷一·命之根 | 四柱、格局、十神 KPI |
| `vol2` | 卷二·业之象 | relations / shensha |
| `vol3` | 卷三·运之波 | 大运、流年、运限 |
| `vol4` | 卷四·宫之图 | 紫微方盘、宫位 reference |
| `vol5` | 卷五·事之理 | 域分析 · **默认折叠** |
| `vol6` | 卷六·问书 | LLM · **须主动展开** |
| `colophon` | 跋·校勘 | missing_fields、iztro ≤3 行 |

常量：`LIFE_VOLUME_LABELS` · `CONTENT_LAYER_LABELS` → `types/life-volume.ts`

### 4.3 内容三层（UI 唯一语义）

| ContentLayer | 用户文案 | API provenance |
|--------------|----------|----------------|
| `fact` | 排盘推算 | `engine` |
| `cite` | 典籍依据 / 待校勘 | `classical` + `classic_id` |
| `inference` | 经验推断 | `heuristic` · 默认折叠 |

映射：`feBeAdapter.mapProvenanceLayerToContent` · Q5 见 [`FE-BE-DECISIONS`](../plan/FE-BE-DECISIONS.md)

---

## 五、视觉与布局定案

> 完整像素与母版 → [`FUSHENG-DESIGN-MASTERPLAN.md`](../design/FUSHENG-DESIGN-MASTERPLAN.md)  
> 样张 → [`docs/design/skin-preview.html`](../design/skin-preview.html)  
> 截图门禁 → [`docs/design/targets/`](../design/targets/README.md)

### 5.1 设计一句话

**纸墨为底，界画为骨，铜朱点睛；卷目清晰，盘面最大，校勘最小。**

### 5.2 工程真源

| 文件 | 用途 |
|------|------|
| `variables.css` | Token 真源（色/字/间距/z-index） |
| `fusheng-page.css` | `.fs-page` · `.fs-card` · `.fs-register-row` · `.fs-kpi-strip` |
| `report-print.css` | 六卷打印 |
| `public/fonts/*.woff2` | 刻本宋 display |

### 5.3 色彩（全站 chrome ≤4 色相）

| Token | Hex | 用途 |
|-------|-----|------|
| `--brand-paper` | `#f5f0e6` | 纸底 |
| `--surface` | `#fffaf5` | 内容白（卡片/盘面） |
| `--brand-ink` | `#1a1410` | 墨 |
| `--brand-mist` | `#6b5d4f` | 雾（辅文） |
| `--brand-gold` | `#b8894d` | 铜（KPI/主 CTA，&lt;8% 面积） |
| `--brand-cinnabar` | `#8b3a2a` | 朱（警示左线） |

**纸面两级**：纸底 → 内容白。**禁止** surface 套 surface-2 再套暖色卡。

**禁止**：`linear-gradient` 铜金按钮 · `#334155` 冷灰正文 · Tailwind 绿黄 alert 铺底 · `-ok-bg` 语义底。

### 5.4 字体

| Token | 用于 |
|-------|------|
| `--font-display` | 卷名、干支、典籍引文（LXGW Neo ZhiSong） |
| `--font-ui` | 导航、按钮、表单、正文 |

正文不全文衬线；宋式体现在 **卷名 + 盘面占格**，非页面大字「宋式美学」。

### 5.5 册页组件类（codex）

| 类名 | 用途 |
|------|------|
| `.fs-card` | 默认扁平卡片（无阴影） |
| `.fs-card--seal` | 全页唯一重阴影（首页 Hero、报告封面） |
| `.fs-card--register` | 册目列表容器 |
| `.fs-register-row` | 卷目单行 |
| `.fs-kpi-strip` | KPI 分格条 |
| `.fs-page-head` | 母版 A 页眉（铜顶线 + 卷名左钤） |
| `.fs-codex-divider` | 节间界画线 |

圆角：`--radius-codex: 8px`。阴影：默认 `--shadow: none`；`--shadow-seal` 仅 seal 用。

---

## 六、工程结构

```text
frontend/src/
├── api/              # bazi · ziwei · explain · life · client
├── assets/           # variables.css · fusheng-page.css · report-print.css
├── components/
│   ├── fusheng/      # 业务组件（VolumeSection · Plate · Trust…）
│   └── new/          # NewAppShell · BaziReferenceTable
├── composables/      # useFushengReport · useVolumeRouteMeta · useReadingProgress
├── constants/        # feBeContract.ts
├── stores/           # profile · fushengReport · auth
├── types/            # life-volume.ts
├── utils/            # buildLifeVolumes · feBeAdapter · buildEngineTrustDisplay
└── views/new/        # 主路径页面
```

**分层约定：**

| 层 | 说明 |
|----|------|
| Primitive | `.fs-btn` · `.fs-card`（fusheng-page.css） |
| Block | `VolumeSection` · `SummaryStrip` · `EngineTrustPanel` |
| Page | `NewBaziView` 等 — 避免页内 200 行 scoped CSS，抽到 `fusheng-page.css` |

---

## 七、前后端适配（FE-BE）

决议全文 → [`FE-BE-DECISIONS.md`](../plan/FE-BE-DECISIONS.md)

### 7.1 与 UI 相关的决议摘要

| # | 决议 | 前端实现 |
|---|------|----------|
| Q1 | W3–W15 `buildLifeVolumes`；W16+ `GET life/volumes` | `ReportView`：remote 成功则**不调用** Adapter（T081 deprecated） |
| Q5 | provenance ≠ UI layer | `feBeAdapter` |
| Q8 | 不默认 `loadDayunNarratives` | 卷三仅盘面/explain |
| Q9 | 报告 ≤4 chart + explain batch | `fetchReportExplainBatches` |
| Q10 | ZW18 degraded → 200 + 横幅 | `TrustDegradedBanner` |
| Q13 | 续读 localStorage | `useReadingProgress` |
| Q15 | 仅 verified 可标「典籍依据」 | `VolumeSection` + `classic_id` |

### 7.2 代码入口

| 模块 | 路径 |
|------|------|
| 契约常量 | `constants/feBeContract.ts` |
| 适配函数 | `utils/feBeAdapter.ts` |
| 六卷 Adapter | `utils/buildLifeVolumes.ts`（**@deprecated T081** · 仅无 remote 回退 / Vitest） |
| 远程六卷 | `api/life.ts` |
| Explain batch | `api/explain.ts` |

### 7.3 报告页数据流

```text
archive-bundle / bazi+ziwei full
        ↓
GET /life/volumes（登录案例 或 VITE_USE_LIFE_VOLUMES_API / localStorage flag）
        ↓  remote 成功且 flag 权威 → 跳过 explain/batch + 不跑 Adapter（T079–T081）
        ↓  remote 失败 → explain/batch + buildLifeVolumes（deprecated 回退）
        ↓
VolumeSection × N + ColophonFootnote
```
DOM：`data-life-volume-source="local|remote"`  
Hash 续卷：`/report#report-volume-vol5`（router scrollBehavior + ReportView sync）

### 7.4 主要 API

| 端点 | 前端 |
|------|------|
| `POST /api/v1/bazi/full` | `api/bazi.ts` |
| `POST /api/v1/ziwei/full` | `api/ziwei.ts` |
| `POST /api/v1/bazi/explain/batch` | `api/explain.ts` |
| `POST /api/v1/ziwei/explain/batch` | `api/explain.ts` |
| `GET /api/v1/life/volumes/{case_id}` | `api/life.ts` |
| `POST /api/v1/fusheng/archive-bundle` | `stores/fushengReport.ts` |

OpenAPI 变更：`python scripts/export_openapi.py` → `cd frontend && npm run gen:types`

契约测试：`tests/test_fe_be_explain_sections.py` · `tests/test_life_volume_schema_contract.py`

---

## 八、组件库

| 组件 | 用途 |
|------|------|
| `NewAppShell` | 顶栏 + 卷名 eyebrow + 移动底栏 |
| `VolumeHead` | 母版 A 页眉（卷名 eyebrow） |
| `VolumeTocGrid` | 首页六卷册目 |
| `ContentLayerLegend` | 三层图例 |
| `ReadingGuide` | 读法导览 + 续读 |
| `VolumeSection` | 六卷节 · 折叠 · layer |
| `ColophonFootnote` | 跋 ≤3 行 |
| `ReportChapterNav` | 报告卷目侧栏 |
| `SummaryStrip` | KPI 分格条 |
| `BaziReferenceTable` | 四柱界格 |
| `FushengZiweiPlate` | 方盘 Hero |
| `EngineTrustPanel` | missing / provenance / 双轨 |
| `TrustDegradedBanner` | ZW18 degraded |
| `AnalysisPanel` | 深读块 |

---

## 九、预警与质量门禁

### 9.1 铁律

```text
先统一真源 → 再打磨三页（八字/紫微/报告卷目）→ 再扩六卷
禁止：丑排版上贴卷名 · interpretation_text 充首屏 · 未过截图门禁就大重构 Report
```

### 9.2 预警码 R-01 ~ R-05

| 码 | 现象 | 首屏不得出现 |
|----|------|--------------|
| R-01 | 顶栏+大标题+口径叠 4–5 层 | `PageHead` 与壳双标题 |
| R-02 | 暖色三层嵌套 + 绿黄 alert | `-ok-bg` · 冷灰 `#334155` |
| R-03 | 与国风模板站无差别 | Inter 全文 · 16px 圆角白卡堆叠 |
| R-04 | 长文占位、无盘面 KPI | &gt;80 字 interpretation 首屏 |
| R-05 | 名词国风、组件西化 | 渐变按钮 · SaaS 卡片修辞 |

### 9.3 三门禁（合并 PR）

**色彩：** 纸墨铜朱 + 五行仅干支字 · 铜 &lt;8% · 朱 ≤3 处左线  
**布局：** 一屏一锚 · 无 PageHead · 375px 无页级横滚  
**内容：** 推断默认折叠 · 卷五不在八字深读 · 卷六不自动 LLM · 无 classic_id 不标典籍

```powershell
rg "linear-gradient|PageHead|#334155|-ok-bg" frontend/src
# 白名单外应为 0
```

### 9.4 防丑五问（DS 签字 · 全「是」才可进下一阶段）

1. 首屏是否 **只有一个** 视觉主角？  
2. 是否只有 **纸 + 内容白** 两级底？  
3. 铜色是否只在 **1 CTA + KPI + active 导航**？  
4. 首屏是否有 **数字/盘面** 而非大段叙述？  
5. **遮住所有中文标题**，截图是否仍能认出浮生（界格+纸色+密度）？  

表格模板 → [`docs/design/targets/README.md`](../design/targets/README.md)

### 9.5 改 UI 标准流程

1. 查 MASTERPLAN + skin-preview  
2. 改 `variables.css` / `fusheng-page.css`  
3. 改对应 `views/new/*` 或 `ReportView.vue`  
4. 块级 `layer` ∈ fact/cite/inference  
5. Vitest + E2E + §9.3 rg 扫描  

---

## 十、开发阶段 F0–F6（摘要）

> 详细节点表 → [`FUSHENG-NODE-CHECKLIST.md`](./FUSHENG-NODE-CHECKLIST.md) · 全栈周计划 → INTEGRATED §五

| 阶段 | 焦点 | 出口 |
|------|------|------|
| **F0** | 契约 · FE-BE 15 题 · R 预警习惯 | 无开放接口争论 |
| **F1** | skin-preview 与 MASTERPLAN 对齐 · targets 三截图 | 设计真源统一 |
| **F2** | 删 PageHead · 去 gradient · 纸面两级 | M1 能看 · 三门禁 |
| **F3** | buildLifeVolumes · VolumeSection · ReadingGuide | 六卷 Adapter 单测绿 |
| **F4** | ReportView 六卷+跋 · explain 接入 | E2E report 绿 |
| **F5** | 首页/紫微/运限/档案 polish | 主路径完整 |
| **F6** | Vitest 矩阵 · Playwright · a11y | type-check+lint+test+e2e 全绿 |

**关键改造文件（索引）：**

| 阶段 | 文件 |
|------|------|
| F2 | `variables.css` · `fusheng-page.css` · 各 View 去 PageHead |
| F3 | `buildLifeVolumes.ts` · `VolumeSection.vue` · `NewBaziView.vue` |
| F4 | `ReportView.vue` · `report-print.css` · `e2e/fusheng-report.spec.ts` |
| F5 | `NewHomeView.vue` · `FushengZiweiView.vue` · `ProfileView.vue` |
| F6 | `e2e/*` · `utils/__tests__/*` |

---

## 十一、打磨期刻意不做

| 不做 | 原因 |
|------|------|
| 卷目 `locked` / 付费墙 | W17+ GTM |
| snippets 分享卡 / 埋点漏斗 | 增长期 |
| 暗色模式 | 纸墨单主题未稳 |
| H5 外链读卷 | 分发后置 |
| 页内大字「宋式美学」营销 | 视觉减法；卷名+盘面表达 |

**要做**：六卷 IA · 盘面精度 · 校勘可信 · 连续阅读 · 全站视觉统一 · 测试可回归。

---

## 十二、验收命令

```powershell
# 前端
cd frontend
npm run type-check
npm run lint
npm run test
npm run test:e2e -- fusheng-report fusheng-bazi-ziwei fusheng-anti-slop
npm run build
# → 输出写入 ../static/app/（FastAPI 静态入口）；**须与源码同 commit**（见 §12.3）

# 根目录
make scorecard
make sync-frontend-types          # OpenAPI 变更后
pytest tests/test_fe_be_explain_sections.py tests/test_life_volume_schema_contract.py
node scripts/compare-live-targets.mjs   # 需先 E2E 导出 targets
```

### 12.1 产品门禁（F6 / R101）

- [ ] 报告 **六卷+跋**，无旧章名  
- [ ] 八字深读 **无** 卷五域卡  
- [ ] 卷五推断 **默认折叠** · 卷六 **不自动** LLM  
- [ ] 首页 **ReadingGuide** + 续读  
- [ ] 全站无 `PageHead` · 无铜金 gradient  
- [ ] 375px 主路径无页级横滚  
- [ ] explain/batch 接入报告 · disclaimer 展示 · ZW18 degraded UI  

### 12.2 设计门禁

- [ ] targets 三截图 vs 实机（或 compare JSON PASS）  
- [ ] 防丑五问 15 格签字  
- [ ] 衬线仅在 display 白名单  

### 12.3 部署约定（TD-31 / P3-17）

| 项 | 约定 |
|----|------|
| **运行时入口** | 后端挂载 `static/app/`（`/static/app/`） |
| **源码真源** | `frontend/src/`；改 UI 后必须 `npm run build` |
| **产物入库** | **`static/app/` 随 PR 提交**（单仓部署，CI 不单独发布 frontend dist） |
| **禁止** | 只改 `frontend/src` 不重建静态度；或本地 `static/app` 长期落后于 main 却另开功能 PR |
| **字体** | `frontend/public/fonts/*.woff2` 与 `static/app/fonts/` **已入库**（~4.3MB；pre-commit `maxkb` 已豁免） |

---

## 十三、设计外链（不重复全文）

| 文档 | 用途 |
|------|------|
| [`FUSHENG-DESIGN-MASTERPLAN.md`](../design/FUSHENG-DESIGN-MASTERPLAN.md) | 色/字/母版/卷目像素 |
| [`skin-preview.html`](../design/skin-preview.html) | 视觉样张 |
| [`handbook-bazi-layout.md`](../design/targets/handbook-bazi-layout.md) | 八字像素 |
| [`handbook-ziwei-layout.md`](../design/targets/handbook-ziwei-layout.md) | 紫微像素 |
| [`handbook-report-layout.md`](../design/targets/handbook-report-layout.md) | 报告六卷 |
| [`targets/*.png`](../design/targets/README.md) | 截图门禁 |

---

## 十四、执行清单索引

| 清单 | 范围 |
|------|------|
| [`EXECUTION-REMAINING`](../plan/FUSHENG-EXECUTION-REMAINING.md) | **R061–R085** 前端打磨（当前主执行） |
| [`BAZI-ZIWEI-POLISH-CHECKLIST`](../plan/FUSHENG-BAZI-ZIWEI-POLISH-CHECKLIST.md) | BZ 细节 |
| [`DEV-READINESS.md`](../DEV-READINESS.md) | 开工自检 |

**历史 73 条问题台账（P-xxx 跟踪）：** [`archive/appendices/FUSHENG-FRONTEND-PLAN-full-2026-07-12.md`](../archive/appendices/FUSHENG-FRONTEND-PLAN-full-2026-07-12.md) §四

---

## 十五、修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| **fe-dev-1.0** | **2026-07-12** | 合并 UI-DEV · FRONTEND-PLAN · RISK-ALERT · QUICKSTART/NODE 前端节为唯一入口 |
| ui-dev-1.2 | 2026-07-12 | （已并入）册页视觉 codex 打磨 |
| fe-plan-1.0 | 2026-07-12 | （已并入）方案与验收 |
| risk-alert-1.0 | 2026-07-12 | （已并入）预警门禁 |
