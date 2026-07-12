# 浮生 · 全自动开发流水线（自检 · 顺序 · 提交）

| 字段 | 内容 |
|------|------|
| **版本** | pipeline-1.2 |
| **日期** | 2026-07-13 |
| **定位** | **唯一执行流水线** — 把「全自动验收 + 自检 + 按序开发 + 自动提交」合成一条可重复的日常循环 |
| **上位** | [FUSHENG-DEV-AUTOPILOT](FUSHENG-DEV-AUTOPILOT.md)（规矩与 A 表）· [DEV-AUDIT-2026-07-13](DEV-AUDIT-2026-07-13.md)（问题清单） |
| **当前阶段** | **W5 产品重建 · Week1 进行中** → [R102](reports/R102-product-rebuild-plan-2026-07-13.md) |
| **机读进度** | `docs/reports/dev-cycle-latest.json`（`python scripts/dev_cycle.py`） |
| **W102 进度** | **6/24**（00a · 00b · 06 · 07 · 02 · 03 ☑）→ 下一项 **W102-01** 或 **W102-04** |

> **一句话**：**按 W102 编号顺序做 → 改完跑 dev_cycle → 全绿再提交 → 每周五 audit-content。** 不聊天也能推进；聊天只发 §六 固定句。

---

## 〇、四象限（本文解决什么）

| 象限 | 含义 | 真源 | 通过标准 |
|------|------|------|----------|
| **① 全自动** | 工程 + 美学机读 Gate | [AUTOPILOT §三](FUSHENG-DEV-AUTOPILOT.md#三全自动验收体系替代全部人工-gate) | `auto_verify_autopilot.py` → **30/30 + 20/20** |
| **② 自检** | 仓库 / 内容 / 产品厚度 | [DEV-AUDIT](DEV-AUDIT-2026-07-13.md) · R102 | `dev_cycle.py` 三节全绿 + P 轨 advisory |
| **③ 按顺序开发** | 免对话任务队列 | 本文 **§四** W102 表 | 严格 W102-01→…，禁止跳号 |
| **④ 自动提交** | 验收通过后入库 | 本文 **§五** | `dev_cycle.py --commit` 或手动按模板 |

**禁止混报：**

| 轨道 | 绿 ≠ |
|------|------|
| 工程轨 E（A01–A29） | 产品可交付 |
| 美学轨 A（A30–A50） | 宋式目检签字 · R079 Q5 真人 |
| 产品轨 P（R102） | autopilot 全绿 |

---

## 一、30 秒：今日循环

```powershell
# 0. 双端（改 UI 前必开）
python -m uvicorn app.main:app --reload --port 8000
cd frontend && npm run dev -- --host 127.0.0.1 --port 5173

# 1. 看当前该做哪一条
#    → 本文 §四 W102 表第一个 ☐

# 2. 做完该条「验收命令」

# 3. 一条命令：自检 + 机读（不写 --commit 则只报告）
python scripts/dev_cycle.py

# 4. 全绿后自动提交（消息见 §五）
python scripts/dev_cycle.py --commit -m "W102-03: 紫微去重复 h2"
```

**Windows 无 make 时**：凡文档写 `make audit-content`，等价于 `python scripts/audit_content_hollowness.py`。

---

## 二、文档真源（只记这一张表）

| 你要… | 只看 |
|--------|------|
| **日常循环（本文）** | **FUSHENG-DEV-PIPELINE.md** |
| 规矩 · A 表 · 页面定案 | [FUSHENG-DEV-AUTOPILOT](FUSHENG-DEV-AUTOPILOT.md) |
| 文档地图 · 周计划索引 | [DEVELOPMENT](DEVELOPMENT.md) |
| 问题清单 · W1–W5 状态 | [DEV-AUDIT](DEV-AUDIT-2026-07-13.md) |
| UI 差距 · 内容 · 4 周细节 | [R102](reports/R102-product-rebuild-plan-2026-07-13.md) |
| T001–T070 历史顺序（已完结） | [EXECUTION-PRIORITY](plan/FUSHENG-EXECUTION-PRIORITY.md) |
| 八字紫微 BZ 细项 | [BAZI-ZIWEI-POLISH](plan/FUSHENG-BAZI-ZIWEI-POLISH-CHECKLIST.md) |
| 合盘 P3（R102 之后） | [R086](reports/R086-relation-compat-sample-pdf-review-2026-07-13.md) |
| Cursor 对话模板 | [CURSOR-AGENT-USAGE](guides/CURSOR-AGENT-USAGE.md) |

---

## 三、全自动 + 自检：三轨验收

### 3.1 工程轨 E（合并前必绿）

```powershell
python scripts/auto_verify_autopilot.py
# → docs/reports/autopilot-verify-latest.json
# 工程 A01–A29 · 美学 A30–A50（共 50 项；文档旧称 A59 已废止，以脚本为准）
```

| 子集 | 何时跑 | 命令 |
|------|--------|------|
| 热修 / 契约 | 改 BE schema、OpenAPI | A01–A07 对应单测 + `export-openapi` + `sync-frontend-types` |
| UI / 宋式 PR | 改 fusheng 页面 | **全量 autopilot** |
| 本地快检 | 迭代中 | `python scripts/auto_verify_w14.py`（CI 当前跑此项，≠ 全量 autopilot） |

### 3.2 产品轨 P（W5 必跑，advisory）

```powershell
python scripts/audit_content_hollowness.py
# → docs/reports/content-hollowness-audit-latest.json
```

| 指标 | Week1 基线 | 当前（2026-07-13） | Week4 目标 |
|------|-------------|-------------------|------------|
| 六卷 thin 合计 | ~72% | ~77% 🟡 | ≤35% |
| vol2 relations fallback | 33% | **0%** ✅ | 0% |
| vol4 均字 | ~10 | ~10 🟡 | ≥40 |

**每周五额外：** `node scripts/compare-live-targets.mjs` + skin-preview 并排目检。

### 3.3 自检轨 S（dev_cycle 聚合）

`python scripts/dev_cycle.py` 依次执行：

| 节 | 内容 | 失败则 |
|----|------|--------|
| S1 | `auto_verify_env.py` | 缺依赖 / 路径 |
| S2 | `auto_verify_autopilot.py` | 不可 `--commit` |
| S3 | `audit_content_hollowness.py` | 可 `--commit` 但 JSON 标 `product_advisory: fail` |

输出：`docs/reports/dev-cycle-latest.json`

### 3.4 提交前本地 hook（可选）

```powershell
pip install -r requirements-dev.txt
pre-commit install
pre-commit run --all-files   # 首次或大改后
```

---

## 四、按顺序开发：W102 任务队列（当前主清单）

> **T001–T070 已 ☑**（见 EXECUTION-PRIORITY）。**现从 W102 表第一个 ☐ 顺序执行**。  
> **规则**：严格编号；标 `∥` 可与上一条并行；做完改 `☐→☑` 并 `dev_cycle --commit`。

**已完成（6）：** W102-00a · W102-00b · W102-06 · W102-07 · W102-02 · W102-03  
**进行中：** Week1（W102-01 · 04～05 · 08 待做）

### 块 0 · 基线入库（Day 0，先于 Week1）

| 状态 | ID | 角色 | 任务 | 验收 | 参考 |
|------|-----|------|------|------|------|
| ☑ | **W102-00a** | ALL | R102 + audit 脚本 + JSON + DEV-AUDIT 1.3 入库 | `git ls-files` 含 R102 | `dd0725a` |
| ☑ | **W102-00b** | ALL | DEV-AUDIT / R102 补 P3-5～TD-29 第二轮遗漏 | audit-1.4 · r102-1.2 | gap 审查 |

### 块 1 · Week1 — 对齐真源 + 视觉减法

| 状态 | ID | 角色 | 任务 | 验收命令 | 参考 |
|------|-----|------|------|----------|------|
| ☐ | **W102-01** | DS | skin-preview 与实机三页并排目检 + 截图 | `docs/design/audit-screenshots/` | R102 §一 |
| ☑ | **W102-02** | FE | 八字速览：Trust 降为 colophon，不抢首屏 | E2E anti-slop 绿 | R102 B2 · footnote `<details>` |
| ☑ | **W102-03** | FE | 紫微：去掉 VolumeHead + section 重复 h2 | E2E risk-alert 绿 | R102 Z2 · `fs-section-kicker` |
| ☐ | **W102-04** | FE | 报告卷首：封面-only，meta 下沉 | E2E report 绿 | R102 R1 |
| ☐ | **W102-05** | FE | 三页 flat 卡 ≤4（含首页 KPI 降权） | 目检 + anti-slop | R102 B9/H2 |
| ☑ | **W102-06** | FE+BE | 修 `formatRelationsSummaryText` fallback | audit vol2 fallback 0% | `eee738f` · TD-08 |
| ☑ | **W102-07** | BE | audit 脚本 vol2 对齐 FE `relations_summary` | 脚本与 UI 一致 | `eee738f` · TD-27 |
| ☐ | **W102-08** | PM | R060 15 分钟试读 + 记录 ≥7/10 或 TOP3 | 试读笔记 | R102 Week1 |

**Week1 出口：** W102-01～08 全 ☑ + `dev_cycle` 绿。

### 块 2 · Week2 — 内容灌满

| 状态 | ID | 角色 | 任务 | 验收 | 参考 |
|------|-----|------|------|------|------|
| ☐ | **W102-09** | FE | 八字页接 `BAZI_PAGE_EXPLAIN_SECTIONS` batch | explain 非空 + 失败 banner | TD-14 · Q12 |
| ☐ | **W102-10** | FE | 紫微页接 `ZIWEI_PAGE_EXPLAIN_SECTIONS` batch | 同上 | R102 Z7 |
| ☐ | **W102-11** | FE | `ReadingGuide` 改读 explain `reading` | 非静态模板 | R102 H4 |
| ☐ | **W102-12** | FE | 卷三/四 buildLifeVolumes 加厚；大运年龄格式化 | 无 `0.0岁起` | TD-09 |
| ☐ | **W102-13** | BE | ziwei explain ≥40 字/宫；卷三 dayun explain | audit 均字 | R102 Week2 |
| ☐ | **W102-14** | ALL | audit thin ≤50% | content JSON | R102 Week2 出口 |

### 块 3 · Week3 — 报告辑录化 + 契约

| 状态 | ID | 角色 | 任务 | 验收 | 参考 |
|------|-----|------|------|------|------|
| ☐ | **W102-15** | BE | `FushengReportPdfRequest` 补 algo 字段并贯通 PDF | PDF=屏幕口径 | TD-11 |
| ☐ | **W102-16** | BE | `archive-bundle` 参数对齐 + gender 男/女 | bundle=分接口 | TD-03/12 |
| ☐ | **W102-17** | FE | 报告改走 `archive-bundle` + explain batches | 请求数 ≤4 | TD-04 |
| ☐ | **W102-18** | FE | `buildBaziRequest` 传 `birth_time_precision` | OpenAPI 一致 | TD-01 |
| ☐ | **W102-19** | DS | 报告 print/PDF 样张 | handbook-report | R102 Week3 |

### 块 4 · Week4 — 收口

| 状态 | ID | 角色 | 任务 | 验收 | 参考 |
|------|-----|------|------|------|------|
| ☐ | **W102-20** | ALL | audit thin ≤35%；`dev_cycle` 进 CI advisory | CI 绿 | R102 Week4 |
| ☐ | **W102-21** | PM+DS | R060 step10 + R079 Q5 真人签字 | 信心 ≥7/10 | R102 Week4 |
| ☐ | **W102-22** | ALL | R102 closeout PR + 更新 DEV-AUDIT W5 ☑ | 文档一致 | DEV-AUDIT §五 |

### 块 5 · P3 后置（R102 closeout 后）

| 状态 | ID | 任务 | 参考 |
|------|-----|------|------|
| ☐ | **W102-P3-01** | 合盘 FE / PDF / multi_compat | [R086 §五](reports/R086-relation-compat-sample-pdf-review-2026-07-13.md) |
| ☐ | **W102-P3-02** | CI 改跑 `auto_verify_autopilot.py` | TD-16 |

---

## 五、自动提交规范

### 5.1 何时可以提交

| 场景 | 最低 Gate | 命令 |
|------|-----------|------|
| 文档 only | pre-commit 可选 | 直接 commit |
| 改前端 fusheng | S2 autopilot 全绿 | `dev_cycle.py --commit` |
| 改 BE schema | S2 + OpenAPI 幂等 | 同上 + 检查 A02/A03 |
| 改 R102 / 审计脚本 | S3 可 advisory fail | `--commit` 允许 P 轨黄 |

**禁止：** autopilot 红、pre-commit 红、`--no-verify`（除非用户明确要求）。

### 5.2 提交信息模板

```text
<W102-ID>: <一句 why（中文）>

- 验收: dev_cycle pass / autopilot 50/50
- 任务: W102-03
```

示例：

```text
W102-03: 紫微页去掉与 VolumeHead 重复的 section 标题

- 验收: autopilot 50/50, anti-slop E2E 绿
- 任务: W102-03 · R102 Z2
```

### 5.3 分层 commit 建议（W102-00 批次）

```text
1. docs: W102-00 真源入库（R102 · DEV-AUDIT · PIPELINE · audit 脚本）
2. feat: W102-06 relations summary 修复
3. fix: W102-07 audit 脚本 vol2 路径对齐
… 每条 W102 独立 commit，便于 bisect
```

### 5.4 自动提交命令

```powershell
# 只自检，不提交
python scripts/dev_cycle.py

# 快检（跳过 autopilot 全量，仅 env + audit-content）— 迭代中用
python scripts/dev_cycle.py --quick

# 自检通过后提交（S2 必须绿；S3 黄灯仍提交但写入 JSON 警告）
python scripts/dev_cycle.py --commit -m "W102-06: 修复 relations summary fallback"

# 指定只跑某一节
python scripts/dev_cycle.py --only autopilot
python scripts/dev_cycle.py --only audit-content
```

**Agent 固定句（复制到 Cursor）：**

```text
执行 docs/FUSHENG-DEV-PIPELINE.md 的 W102-XX，按该条验收命令收尾，然后 python scripts/dev_cycle.py --commit -m "W102-XX: …"
```

---

## 六、阶段地图（避免跳阶段）

```text
Phase A  T001–T070     ☑ 打磨期工程任务（EXECUTION-PRIORITY）
Phase B  W102-00–22    🟡 产品重建（R102）← 6/24 完成
Phase C  W15–W16       ⏸ life/volumes 权威化 · GTM 预备
Phase D  W102-P3       ⏸ 合盘 · CI autopilot 对齐
Phase E  W17+          ⏸ 平台演进
```

**纪律：**

- Phase B 未完成 → 不开 Phase D 合盘大功能
- 增长/平台文档（BOOK-GTM / PLATFORM）→ **只读参考，禁止提前做**

---

## 七、CI 与本地差异（已知）

| 项 | 本地 dev_cycle | GitHub CI |
|----|----------------|-----------|
| 全量 autopilot | ✅ S2 | ⏸ 当前仅 `auto_verify_w14.py` |
| audit-content | ✅ S3 | ⏸ 未接入 |
| E2E | autopilot 内 | ✅ test job |

**W102-P3-02** 目标：CI 与本地 S2 对齐。

---

## 八、修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| pipeline-1.0 | 2026-07-13 | 初版：四象限 · W102 顺序表 · dev_cycle · 提交规范 |
| pipeline-1.1 | 2026-07-13 | W102-00a/06/07 ☑ · 进度 3/24 · vol2 fallback 0% |
| pipeline-1.2 | 2026-07-13 | W102-00b/02/03 ☑ · 进度 6/24 · audit-1.4 |

---

**下一步：** **W102-01**（skin-preview 目检）或 **W102-04**（报告卷首）→ `python scripts/dev_cycle.py --quick`
