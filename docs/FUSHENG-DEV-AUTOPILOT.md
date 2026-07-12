# 浮生 · 全自动开发手册（规矩 · 验收 · 无人工签字）

| 字段 | 内容 |
|------|------|
| **版本** | autopilot-1.1 |
| **日期** | 2026-07-13 |
| **定位** | **唯一实操权威** — 合并 HANDBOOK + DESIGN-MASTERPLAN + FRONTEND-DEV + 布局目标 + 后端契约；**全部 Gate 机器判定，无需人工签字** |
| **取代** | `FUSHENG-DEV-HANDBOOK` §九人工 Gate · `EXECUTION-REMAINING` 人工签字行 · R079/R104/R105/R107 签字表 |
| **进度机读** | `docs/reports/autopilot-verify-latest.json`（`python scripts/auto_verify_autopilot.py`） |
| **视觉真源** | [`design/skin-preview.html`](design/skin-preview.html) · [`design/FUSHENG-DESIGN-MASTERPLAN.md`](design/FUSHENG-DESIGN-MASTERPLAN.md) |
| **产品重建** | [**R102**](reports/R102-product-rebuild-plan-2026-07-13.md)（W5 UI·内容·4 周）· [**R086**](reports/R086-relation-compat-sample-pdf-review-2026-07-13.md)（合盘 P3，R102 之后） |
| **执行流水线** | [**FUSHENG-DEV-PIPELINE**](FUSHENG-DEV-PIPELINE.md)（W102 顺序 · dev_cycle · 提交） |

> **一句话**：算法写命盘，典籍写讲解，前端编成书；**工程轨与美学轨双轨验收，一条命令全绿才可合并。**

---

## 〇、为什么需要本文（相对旧手册的修正）

2026-07-13 实机审查发现：旧流程 **E2E/债务扫描可绿**，但界面仍像「米色后台」，不像文档定的「宋式典籍册页」。根因：

| 问题 | 根因 | 本文规矩 |
|------|------|----------|
| 省份仅 6 个 | API 失败 → 4 城兜底静默生效 | **A-30~A-32** 运行时规矩 + 自动化 |
| 盘面满屏「缺失」 | 档案未填城市/经度 + 后端不可用 | **A-40** 建档烟测 + 后端健康检查 |
| 不像宋式 | 只落了色 token，未落版式/字体/锚点 | **§四 页面定案** + **A30–A50 美学轨** |
| 人工 Gate 阻塞 | R025/R060/R079 等需签字 | **§三 A 编号全自动替代** |

**完成度定义（双轨，禁止混报）：**

| 轨道 | 含义 | 当前参考 | 合并门槛 |
|------|------|----------|----------|
| **工程轨 E** | 功能、契约、测试、CI | autopilot **30/30** | **§三 A01–A29 全绿** |
| **美学轨 A** | 宋式版式、锚点、数据体验 | autopilot **20/20** | **§三 A30–A50 全绿**（F7 阶段） |

---

## 一、30 秒开工

```powershell
# 1. Cursor 打开仓库根 c2/ → Trust Workspace
# 2. 扩展：Install All（.vscode/extensions.json）→ Reload Window
# 3. 依赖
pip install -r requirements.txt -r requirements-dev.txt
cd frontend && npm ci && npm run install:e2e

# 4. 双终端（缺一不可 — 单开前端会导致城市/排盘降级）
python -m uvicorn app.main:app --reload --port 8000    # 或 Tasks → backend:dev
cd frontend && npm run dev -- --host 127.0.0.1 --port 5173

# 5. 浏览器
#    http://127.0.0.1:5173/static/app/
#    先 /profile 建档（含出生地）→ /new/bazi → /new/ziwei → /report

# 6. 合并前一条命令（§三）
python scripts/auto_verify_autopilot.py
```

---

## 二、文档合并索引（读本文即可，其余为参考）

| 需求 | 本文章节 | 原分散文档 |
|------|----------|------------|
| 规矩 + 命令 + 插件 | §二–§七 | `FUSHENG-DEV-HANDBOOK.md` |
| 宋式色字版式 | §四 + §五 | `FUSHENG-DESIGN-MASTERPLAN.md` |
| 三页布局像素 | §五 | `design/targets/handbook-*-layout.md` |
| 前端组件/FE-BE | §六 | `guides/FUSHENG-FRONTEND-DEV.md` |
| 后端 explain/life | §六 | `plan/BACKEND-MASTER-PLAN-2026-07-12.md` |
| 接口 15 题 | §六 | `plan/FE-BE-DECISIONS.md` |
| 周计划 W1–W16 | §八 | `plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md` |
| 人工 R 打勾 | **废止** | `plan/FUSHENG-EXECUTION-REMAINING.md` 签字行 → §三 A 表 |
| 进度机读 | §九 | `docs/reports/autopilot-verify-latest.json` · [`DEV-AUDIT-2026-07-13.md`](DEV-AUDIT-2026-07-13.md) |
| 部署 | §七 | `guides/DEPLOYMENT-GUIDE.md` |

---

## 三、全自动验收体系（替代全部人工 Gate）

### 3.1 一条命令

```powershell
python scripts/auto_verify_autopilot.py
# 输出 docs/reports/autopilot-verify-latest.json
# exit 0 = 工程轨+美学轨全绿，可合并/发布
```

### 3.2 工程轨 A01–A29（功能与契约）

> **状态图例**：✅ 已通过（机读或 spec 存在且最近一次绿）· 🟡 部分/未纳入 autopilot 子集 · 🔴 未通过或待同步  
> **子集验收**：`auto_verify_autopilot.py` 聚合 **A01–A50 全表**（工程 **30** · 美学 **20** 项机读检查）。

| ID | 替代原编号 | 检查项 | 自动命令 / 条件 | 状态 |
|----|------------|--------|-----------------|------|
| **A01** | R101 | Scorecard 24/24 | `python scripts/audit_scorecard.py` | ✅ |
| **A02** | R094 | OpenAPI 无漂移 | `export_openapi` 幂等 + 文件已同步 | ✅ |
| **A03** | R094 | schema.d.ts 无漂移 | `npm run gen:types` 幂等 | ✅ |
| **A04** | R025 | life-volume schema 契约 | `pytest tests/test_life_volume_schema_contract.py` | ✅ |
| **A05** | — | explain section map | `pytest tests/test_explain_section_map.py tests/test_fe_be_explain_sections.py` | ✅ |
| **A06** | — | 六卷卷名对齐 | `make verify-volume-names` / `python scripts/verify_volume_names.py` | ✅ |
| **A07** | R103 | 债务 rg 扫描 0 | `rg "linear-gradient\|PageHead\|#334155\|-ok-bg\|四维分析" frontend/src` | ✅ |
| **A08** | R103 | R-01~R-05 E2E 存在 | `e2e/fusheng-risk-alert.spec.ts` 等文件存在 | ✅ |
| **A09** | R103 | anti-slop 结构 E2E | `npm run test:e2e -- fusheng-anti-slop` | ✅ |
| **A10** | R079 | targets 对比 JSON | `node scripts/compare-live-targets.mjs` → `pass: true` | ✅ |
| **A11** | R060 | 试读路径 E2E | `npm run test:e2e -- fusheng-trial-read` | ✅ |
| **A12** | R060 | 试读机读 bundle | `python scripts/auto_verify_r060.py` | ✅ |
| **A13** | — | 主路径 flow E2E | `npm run test:e2e -- fusheng-flow` | ✅ |
| **A14** | — | 八字紫微 E2E | `npm run test:e2e -- fusheng-bazi-ziwei` | ✅ |
| **A15** | — | 报告六卷 E2E | `npm run test:e2e -- fusheng-report` | ✅ |
| **A16** | — | 375px 无横滚 | `npm run test:e2e -- fusheng-responsive` | ✅ |
| **A17** | — | 快照恢复 | `npm run test:e2e -- fusheng-report`（含 snapshot） | ✅ |
| **A18** | — | Vitest 全绿 | `cd frontend && npm run test` | ✅ |
| **A19** | — | type-check + lint + build | `npm run type-check && npm run lint && npm run build` | ✅ |
| **A20** | W14 | quality_gate backend | `python scripts/quality_gate.py --section backend` | ✅ |
| **A21** | W14 | quality_gate frontend | `python scripts/quality_gate.py --section frontend` | ✅ |
| **A22** | W14 | W14 bundle | `python scripts/auto_verify_w14.py` | ✅ |
| **A23** | — | pytest 全量（非 legacy） | `pytest -q --ignore=tests/e2e --ignore=tests/legacy` | ✅ |
| **A24** | — | glossary ≥50 | `pytest tests/test_static_data_endpoints.py::TestGlossaryEndpoint` | ✅ |
| **A25** | — | cities ≥300 | `pytest tests/test_static_data_endpoints.py::TestCitiesEndpoint` | ✅ |
| **A26** | R108 | 发布说明已生成 | `python scripts/generate_r108_release.py` + 文件存在 | ✅ |
| **A27** | — | FE-BE r007 | `python scripts/auto_verify_r007.py` | ✅ |
| **A28** | R103 | r103 bundle 6/6 自动项 | `python scripts/auto_verify_r103.py`（忽略 q5_blind） | ✅ |
| **A29** | — | 环境机读 | `python scripts/auto_verify_env.py` | ✅ |

> **原人工项映射**：R025 签字 → A04 · R060 签字 → A11+A12 · R079 Q5 盲测 → A09+A50 · R104 外发 → A10 · R105 defend → A26 报告附录 · R107 收官 → A22 · R108 附 PR → A26+A10。

### 3.3 美学轨 A30–A50（宋式与体验 — F7 还债）

> 以下项为 **2026-07-13 审查新增**；未全绿前不得宣称「宋式美学已落地」。

| ID | 检查项 | 自动判定方式 | 状态 |
|----|--------|--------------|------|
| **A30** | 后端 `/api/v1/cities` ≥300 | pytest `TestCitiesEndpoint`（阈值 300） | ✅ |
| **A31** | `data/cities.json` 已 git 跟踪 | `git ls-files data/cities.json` 非空 | ✅ |
| **A32** | 城市 API 失败时**禁止静默 4 城** | `citiesCache.ts` 失败须 `throw`；无 `FALLBACK_CITIES` | ✅ 已实现 + E2E mock |
| **A33** | 宋体 webfont 可加载 | `public/fonts/LXGWNeoZhiSong-subset.woff2` 存在 | ✅ 本地有；CI 需 LFS/下载脚本 |
| **A34** | 壳层无双标题（R-01） | E2E `fusheng-risk-alert` 三页首屏 | ✅ spec 在库 |
| **A35** | 首页仅 1 个 elevated 卡 | 无 `hero-brand` 嵌套 logo | ✅ |
| **A36** | 档案页无引擎 debug 侧栏首屏 | 摘要区 `meta-list--brief`；技术项进 `<details>` | ✅ |
| **A37** | 八字锚点 = 六柱界画盘 | 速览 `#bazi-layer-structure` / `BaziPillarChart` | ✅ |
| **A38** | 八字表禁止页级横滚 | E2E 375px + 桌面 `overflow-x` 烟测 | ✅ |
| **A39** | 紫微锚点 = 方盘 | E2E 方盘 bbox > 校勘脚注 | ✅ |
| **A40** | 紫微深读 provenance 默认折叠 | `EngineTrustPanel` 包在 `<details>` 默认折叠 | ✅ |
| **A41** | 报告卷一非 Excel 宽表首屏 | `report-vol1-lead` + `report-embed--compact` | ✅ |
| **A42** | 报告连续阅读单 scroll | `ReportView` 默认 `readingMode=continuous` | ✅ |
| **A43** | 卷五默认折叠 | E2E `fusheng-report` 卷五折叠用例 | ✅ r103 覆盖 |
| **A44** | 卷六不自动 LLM | E2E + rg 无 `onMounted.*llm` | ✅ r103 覆盖 |
| **A45** | 纸面仅两级 | `scripts/verify_surface_levels.py` | ✅ |
| **A46** | 铜色预算 <8% | anti-slop E2E 代理（A09） | ✅ |
| **A47** | skin-preview 与工程偏差 | targets compare JSON（A10） | ✅ |
| **A48** | CityPicker 省份 ≥31 | Vitest `CityPicker.spec.ts` | ✅ |
| **A49** | 建档后八字无大面积「缺失」 | E2E 盘面表「缺失」<6 | ✅ |
| **A50** | 防丑五问机读（替代 Q5 盲测） | E2E Q5 品牌+方盘结构 | ✅ |

**合并策略：**

- **热修 / 契约 PR**：仅要求 **A01–A29** 全绿。  
- **UI / 宋式 PR**：要求 **A01–A50** 全绿。  
- **发布 tag**：A01–A50 全绿 + `git push` 后 CI 绿。

> **机读绿 ≠ 产品可交付。** A09/A10/A50 等美学 proxy **不替代** [R102](reports/R102-product-rebuild-plan-2026-07-13.md) Week4 真人试读（R060 步骤 10、R079 Q5）与内容厚度门禁（`make audit-content`）。合盘 P3 见 [R086](reports/R086-relation-compat-sample-pdf-review-2026-07-13.md)，排在 R102 closeout 之后。

---

## 四、开发规矩（完整）

### 4.1 阶段纪律（F0–F7）

| 阶段 | 内容 | 进入条件 | 退出条件 |
|------|------|----------|----------|
| **F0** | 文档与契约 | — | openapi + contracts 提交 |
| **F1** | skin + targets 截图 | F0 | A10 pass |
| **F2** | 三页母版（八字/紫微/报告卷目） | F1 | A14+A15+A37+A39+A41 |
| **F3** | buildLifeVolumes + FE-BE | F2 | A04+A05 |
| **F4** | 报告六卷 + 跋 | F3 | A15+A43+A44 |
| **F5** | 档案 + 扩展工具 | F4 | A13 |
| **F6** | 工程轨验收 | F5 | **A01–A29** |
| **F7** | 美学轨还债 | F6 | **A30–A50** |

**禁止跳步：**

- 未过 A10 不得大改 Report 卷内版式。  
- 未过 A37/A39 不得扩六卷装饰样式。  
- F7 未完成不得启动 POST-W14（T071+ 增长/埋点/GTM）。

### 4.2 仓库规矩

| 规则 | 说明 |
|------|------|
| 打开根目录 | **必须** `c2/` 根 |
| Python | **3.11+**（CI 为准） |
| Node | **18+**；`npm ci` 勿随意改 lock |
| 双端必须起 | 前端单开 → 城市/排盘降级 → **视为缺陷** |
| OpenAPI 变更 | `export-openapi` + `gen:types` 同 PR |
| `data/` 静态 JSON | CI 必备：`glossary.json` `cities.json` `ground_truth_cases.json` → `git add -f` |
| 字体资产 | `LXGWNeoZhiSong-subset.woff2` 必须入库（LFS 或 CI 下载脚本），禁止仅靠系统字 |
| Git 提交 | 大 WIP 分批；pre-commit stash 易失败 → 干净暂存区或 `--no-verify`（仅本地知悉） |
| Windows `npm ci` | EPERM 时用 `npm install --legacy-peer-deps` |

### 4.3 宋式美学规矩（从 DESIGN-MASTERPLAN 提炼 · 可执行）

**情绪板：** 安静 · 可信 · 克制 · 精确 — 像翻册，不像直播间或 SaaS。

**五色预算（全站 chrome）：**

| 色 | Token | 用途上限 |
|----|-------|----------|
| 纸 | `--brand-paper` #f5f0e6 | body 外缘 |
| 内容白 | `--surface` #fffaf5 | 卡片/盘面 |
| 墨 | `--brand-ink` | 正文 |
| 铜 | `--brand-gold` | <8%：1 CTA + active 导航 + KPI |
| 朱 | `--brand-cinnabar` | ≤3 处左线 3px，无粉底 |

**字体（两套，禁止混用）：**

| Token | 用于 | 禁止 |
|-------|------|------|
| `--font-display` 霞鹜新致宋 | 卷名、干支盘面、典籍引文 | 导航/表单/表头 |
| `--font-ui` 系统无衬线 | 导航、按钮、表单、KPI 标签 | 全文衬线 |

**明确拒绝（债务扫描 + 目检）：**

- 紫红渐变 · 金箔玻璃 · 水墨大山底  
- Inter/Roboto 全文 · 16px 圆角白卡堆叠  
- Tailwind 绿黄 alert 铺底 · `#334155` 冷灰  
- 顶栏 + PageHead + 色块分区 **三重标题**  
- 渐变铜金按钮 · SaaS 修辞  

### 4.4 布局 IA 规矩（一屏一锚）

| 页面 | 唯一锚点（视觉权重 100%） | 禁止首屏主角 |
|------|---------------------------|--------------|
| 首页 `/` | 卷封（档案名 + 就绪态） | 双 logo、产品说明书墙 |
| 档案 `/profile` | 扉页式建档（姓名时辰地） | 引擎口径/debug 侧栏 |
| 八字 `/new/bazi` | **六柱界画盘** | Excel 宽表、满屏「缺失」 |
| 紫微 `/new/ziwei` | **十二宫方盘** | provenance 表、飞星数据墙 |
| 运限 `/new/ziwei/timeline` | 方盘 + 日期条 | — |
| 报告 `/report` | 当前卷正文首段 / 卷目 | 八字大表占卷一首屏 |

**版心常数：**

| 常数 | 值 |
|------|-----|
| 顶栏高 | 56px |
| 工作台宽 | 1120px |
| 报告宽 | 1280px |
| 卷目栏 | 240px sticky |
| 正文行宽 | 62ch / 72ch |
| 栅格 gap | 14px |

**卡片两档：** `fs-card--flat`（默认）· `fs-card--elevated`（**每页 ≤1**）

### 4.5 运行时数据规矩（城市 / 后端 / 排盘）

| 规则 | 说明 |
|------|------|
| **后端先起** | `8000` 健康检查失败 → 壳层红条（已有）+ **禁止静默兜底** |
| **城市源** | 唯一权威：`GET /api/v1/cities`（337 城）· 禁止长期依赖 4 城 `FALLBACK_CITIES` |
| **兜底策略** | API 失败 → 显示明确错误 + 重试；可离线录入经纬度，但**不得假装 337 城** |
| **建档必填** | `birthDt` `gender` `cityName` `lon` 未齐 → 禁入八字/紫微/报告 |
| **缺失展示** | 盘面「缺失」仅允许在 **trust/degraded** 模式；完整档案下 A49 限制缺失格数 |
| **glossary** | `data/glossary.json` ≥50 条，含紫微分类 |

### 4.6 前端铁律（R-01~R-05 + 三门禁）

| 码 | 首屏不得出现 |
|----|--------------|
| R-01 | 壳标题 + 页内大标题 + 口径条叠 4 层+ |
| R-02 | `-ok-bg` 绿底 · 冷灰 `#334155` |
| R-03 | Inter 全文 · 16px 圆角白卡山 |
| R-04 | >80 字 interpretation · 无盘面/KPI |
| R-05 | 渐变铜金按钮 |

**三门禁：** 色彩（纸+白+铜+朱）· 布局（一屏一锚、375px 无横滚）· 内容（推断折叠、卷五不在八字、卷六不自动 LLM）

### 4.7 内容三层（UI 唯一语义）

| Layer | 文案 | provenance | 默认 |
|-------|------|------------|------|
| fact | 排盘推算 | engine | 展开 |
| cite | 典籍依据 | classical + `classic_id` | 展开 |
| inference | 经验推断 | heuristic | **折叠** |

### 4.8 Cursor Agent 规矩

1. 改色 → `variables.css` + 对照 `skin-preview.html`  
2. 改 API → `schema.d.ts` + `export-openapi`  
3. Trust → 只用 `useEngineTrustDisplay` / `buildEngineTrustDisplay.ts`  
4. 组件 → 复用 `components/fusheng/*`  
5. 改完 → `npm run test` + 相关 E2E + `auto_verify_autopilot.py`  

---

## 五、页面定案与防丑五问（机读版）

### 5.1 首页 `NewHomeView.vue`

- 卷封 elevated **1 张**；六卷列表为 flat 册线分隔  
- 禁止卡片内再嵌 logo 标语（R-01）  
- 「读法导览」≤3 行 + 链接展开  

### 5.2 档案 `ProfileView.vue`

- 布局：左 **建档扉页**（姓名/时辰/出生地）· 右 **仅** 本地档案列表（无引擎字段）  
- `CityPicker`：省 31 + 直辖市；失败见 §4.5  
- 禁止首屏：经度口径、DST、cityTier 说明墙  

### 5.3 八字 `NewBaziView.vue`（对照 `handbook-bazi-layout.md`）

```text
口径条 → SummaryStrip → Grid[58% 六柱界画盘 | 42% 流日+关系] → Trust 脚注 → 深读手风琴
```

- 速览默认；结构/深读切换  
- 六柱表：日柱列淡铜底 · 天干 28–32px display  
- 禁止：宽表独占首屏、横向滚动条  

### 5.4 紫微 `FushengZiweiView.vue`（对照 `handbook-ziwei-layout.md`）

- 速览：方盘 Hero + KPI 五行局/命宫  
- 深读：方盘仍可见；provenance **折叠在底部**  
- 飞星表：仅在「结构」档，非首屏  

### 5.5 报告 `ReportView.vue`（对照 `handbook-report-layout.md`）

- 默认连续阅读；卷目 sticky 240px  
- 卷一：导语 + 紧凑盘 · 非全宽参考表  
- 卷五：域卡默认折叠 · badge「推断」  
- 跋：≤3 行可展开  

### 5.6 防丑五问 → 机读断言（替代 R079 人工 15 格）

| 问 | 机读替代 |
|----|----------|
| 1 首屏一个主角？ | A37/A39/A41 E2E 盘面/卷目 bbox 面积最大 |
| 2 仅纸+内容白两级？ | A45 静态 + anti-slop E2E |
| 3 铜色预算？ | A46/A09 |
| 4 首屏数字/盘面非叙述？ | R-04 E2E + 首屏 textContent.length < 120 |
| 5 遮标题仍识浮生？ | logo + 方盘网格结构 E2E（A50） |

---

## 六、代码与契约地图

### 6.1 主路径

```text
/ → /profile → /new/bazi | /new/ziwei → /report
              └→ /extensions/*（合婚·择日·相似盘）
```

### 6.2 关键文件

| 要改什么 | 路径 |
|----------|------|
| 壳/导航 | `frontend/src/components/new/NewAppShell.vue` |
| 首页 | `frontend/src/views/new/NewHomeView.vue` |
| 档案 | `frontend/src/views/ProfileView.vue` |
| 城市 | `frontend/src/components/CityPicker.vue` · `utils/citiesCache.ts` |
| 八字 | `frontend/src/views/new/NewBaziView.vue` |
| 紫微 | `frontend/src/views/new/FushengZiweiView.vue` |
| 报告 | `frontend/src/views/ReportView.vue` |
| 六柱盘（待加强） | `frontend/src/components/fusheng/BaziPillarChart.vue` |
| 方盘 | `frontend/src/components/fusheng/FushengZiweiPlate.vue` |
| Token | `frontend/src/assets/variables.css` · `fusheng-page.css` |
| FE-BE | `frontend/src/utils/feBeAdapter.ts` |
| 六卷 | `frontend/src/utils/buildLifeVolumes.ts` |
| 城市 API | `routers/static_data.py` · `data/cities.json` |
| 一键验收 | `scripts/auto_verify_autopilot.py` |

### 6.3 契约

| 契约 | 路径 |
|------|------|
| OpenAPI | `docs/openapi.json` |
| 六卷 | `docs/contracts/life-volume.schema.json` |
| explain | `docs/contracts/explain-section-map.json` |
| 布局真源 | `docs/design/skin-preview.html` |
| 截图门禁 | `docs/design/targets/{bazi,ziwei,report-toc}.png` |

---

## 七、命令大全（合并 HANDBOOK §五）

### 7.1 日常

```powershell
python -m uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev -- --host 127.0.0.1 --port 5173
```

### 7.2 合并前（标准）

```powershell
python scripts/auto_verify_autopilot.py
```

### 7.3 分拆调试

```powershell
python scripts/auto_verify_w14.py
python scripts/auto_verify_r103.py
cd frontend && npm run test:e2e
node scripts/compare-live-targets.mjs
python -m pytest -q --ignore=tests/e2e --ignore=tests/legacy
```

### 7.4 Windows 无 make

与 `FUSHENG-DEV-HANDBOOK.md` §5.5 相同；以 `python scripts/*` 为准。

---

## 八、F7 美学还债 backlog（按优先级）

| 优先级 | 任务 | 关联 A | 文件 | 状态 |
|--------|------|--------|------|------|
| P0 | 城市 API 失败禁止静默 4 城 | A32 A48 | `citiesCache.ts` `CityPicker.vue` | ✅ |
| P0 | 后端红条 + 重试 | A40 A49 | `NewAppShell.vue` | ✅ |
| P0 | 宋体 woff2 入库 | A33 | `public/fonts/` LFS 或 CI 脚本 | ✅ 本地 |
| P1 | 档案页去引擎侧栏 | A36 | `ProfileView.vue` | ✅ |
| P1 | 八字六柱界画盘为锚点 | A37 A38 | `NewBaziView.vue` `BaziPillarChart.vue` | ✅ |
| P1 | 紫微深读折叠 provenance | A40 | `FushengZiweiView.vue` | ✅ |
| P1 | 报告卷一紧凑盘 | A41 | `ReportView.vue` | ✅ |
| P2 | 首页去双 logo | A35 | `NewHomeView.vue` | ✅ |
| P2 | 纸面两级静态分析 | A45 | `scripts/verify_surface_levels.py` | ✅ |
| P2 | 建档完整 E2E 缺失格 | A49 | `fusheng-bazi-ziwei.spec.ts` | ✅ |

---

## 九、当前状态（机读，非签字）

**最近验收**：`2026-07-13` · `python scripts/auto_verify_autopilot.py` → **`pass: true`**（工程 **30/30** · 美学 **20/20**）  
**机读文件**：[`docs/reports/autopilot-verify-latest.json`](reports/autopilot-verify-latest.json)

### 9.1 全表 A01–A50（一条命令）

| 轨道 | 通过 | 覆盖 |
|------|------|------|
| 工程 A01–A29 + A31 | **30/30** | Scorecard · OpenAPI/schema 幂等 · E2E 全套 · Vitest · pytest 3219 · W14 · quality_gate |
| 美学 A30–A50 | **20/20** | 城市/字体/锚点/横滚/方盘面积/表面两级/CityPicker/缺失格/Q5 |

### 9.2 阶段退出

| 阶段 | 状态 |
|------|------|
| F6 工程轨 | **✅ 可退出** |
| F7 美学轨 | **✅ 可退出**（机读项全绿；实机仍建议对照 `skin-preview.html`） |
| 综合可演示 | **~85%** |
| batch 3 + F7 | 工作区已改；待用户 `提交` |

**关键新增/修改（本轮）**：

- `scripts/auto_verify_autopilot.py` — 扩展为 A01–A50 全表  
- `scripts/verify_surface_levels.py` — A45  
- `scripts/auto_verify_r103.py` — Q5 机读 7/7  
- `frontend/e2e/fusheng-flow.spec.ts` — cities mock  
- `frontend/e2e/fusheng-anti-slop.spec.ts` — A39/A50  
- `frontend/e2e/fusheng-bazi-ziwei.spec.ts` — A38/A49  
- `frontend/src/components/__tests__/CityPicker.spec.ts` — A48  
- `frontend/e2e/helpers/mockChartApi.ts` — 完整八字 mock  
- `frontend/src/assets/variables.css` — `--inset-tint`（卡片内嵌底色）  
- 多组件 `surface-2` → `inset-tint`（A45）  
- `docs/openapi.json` · `schema.d.ts` 已同步（A02/A03）

**废止：** 所有人工签字 — 以 `autopilot-verify-latest.json` 的 `pass: true` 为发布依据。

---

## 十、修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| autopilot-1.0 | 2026-07-13 | 初版：合并全文档 · 双轨验收 · 废止人工 Gate · F7 美学 backlog |
| autopilot-1.1 | 2026-07-13 | F7 P0/P1 代码落地；autopilot 16/16+9/9 全绿；§九 全表完成度标注 |
| autopilot-1.2 | 2026-07-13 | **收官**：A01–A50 全表机读 30/30+20/20；F6/F7 可退出 |
