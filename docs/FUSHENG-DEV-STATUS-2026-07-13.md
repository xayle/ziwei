# 浮生 · 开发文档与问题总览（整合版）

> **⚠️ 历史快照（status-1.1）** — 签字/WIP 叙事已过时。  
> **当前真源**：机读验收 → [`FUSHENG-DEV-AUTOPILOT.md`](FUSHENG-DEV-AUTOPILOT.md) §九 · 仓库问题与计划 → [**`DEV-AUDIT-2026-07-13.md`**](DEV-AUDIT-2026-07-13.md)

| 字段 | 内容 |
|------|------|
| **版本** | status-1.1 |
| **日期** | 2026-07-13（pass 4 复验） |
| **定位** | **当前进度 + 文档地图 + 待办问题** 的单页总览 |
| **日常入口** | [`FUSHENG-DEV-AUTOPILOT.md`](FUSHENG-DEV-AUTOPILOT.md) · [`DEV-AUDIT-2026-07-13.md`](DEV-AUDIT-2026-07-13.md) |

> **一句话**：W14 打磨期 **自动化轨已基本闭环**（scorecard 24/24 · vitest 87 · E2E 47）；**人工 Gate + 剩余 WIP 提交** 是收官前最后两块。

---

## 一、30 秒：我该读哪份？

| 你想… | 唯一权威 | 路径 |
|--------|----------|------|
| **规矩·验收·A 表** | 全自动权威 | [`FUSHENG-DEV-AUTOPILOT.md`](FUSHENG-DEV-AUTOPILOT.md) ⭐⭐⭐ |
| **仓库整理与计划** | 自检审计 | [`DEV-AUDIT-2026-07-13.md`](DEV-AUDIT-2026-07-13.md) ⭐ |
| **文档地图** | 索引 | [`DEVELOPMENT.md`](DEVELOPMENT.md) |
| **本文** | 历史快照 only | 下文保留 2026-07-13 pass4 记录 |
| **改前端 UI / 六卷 / FE-BE** | 前端手册 | [`guides/FUSHENG-FRONTEND-DEV.md`](guides/FUSHENG-FRONTEND-DEV.md) |
| **按 R 编号打勾** | 剩余执行清单 | [`plan/FUSHENG-EXECUTION-REMAINING.md`](plan/FUSHENG-EXECUTION-REMAINING.md) |
| **按 T 编号顺序开发** | 已完成 + 顺序 | [`plan/FUSHENG-EXECUTION-PRIORITY.md`](plan/FUSHENG-EXECUTION-PRIORITY.md) |
| **周计划与 Gate** | 主蓝图 | [`plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md`](plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md) |
| **色/字/母版** | 视觉定案 | [`design/FUSHENG-DESIGN-MASTERPLAN.md`](design/FUSHENG-DESIGN-MASTERPLAN.md) |
| **API 契约** | OpenAPI + JSON Schema | [`openapi.json`](openapi.json) · [`contracts/`](contracts/) |
| **收官签字** | W14 草案 | [`reports/R107-w14-signoff-draft-2026-07-12.md`](reports/R107-w14-signoff-draft-2026-07-12.md) |
| **发布说明** | R108 | [`reports/R108-release-notes-draft-2026-07-12.md`](reports/R108-release-notes-draft-2026-07-12.md) |

**勿再扩写的旧文件**（仅跳转）：`FUSHENG-FRONTEND-UI-DEV.md` · `FUSHENG-FRONTEND-PLAN.md` · `FUSHENG-FRONTEND-RISK-ALERT.md` → 全文已并入 `FUSHENG-FRONTEND-DEV.md`。

---

## 二、当前进度快照（2026-07-13）

### 2.1 里程碑

| 里程碑 | 目标 | 状态 |
|--------|------|------|
| **P0 Gate** | R025 life-volume 三方共签 | ☐ 契约测试绿；签字待填 |
| **P1 Gate** | R060 15 分钟试读 | 🟡 E2E 1–9 绿；step 10 + 签字待人工 |
| **三页自检** | R085 | 🟡 五问 15/15 代理 ☑；产品姓名待补 |
| **W14 收官** | R107 → R110 | ☐ 自动化完成；负责人签字待填 |
| **POST-W14** | T071–T140 | ⏸ R107 后再开 |

### 2.2 执行清单 R001–R110

| 指标 | 数值 |
|------|------|
| 已勾选 ☑ | **~93 项** |
| 仍开放 ☐/🟡 | **~17 项** |
| 权威清单 | [`FUSHENG-EXECUTION-REMAINING.md`](plan/FUSHENG-EXECUTION-REMAINING.md) |

### 2.3 质量门禁（最近复验）

| 检查项 | 结果 | 备注 |
|--------|------|------|
| Scorecard | **24/24 · 10.0/10** | `docs/reports/scorecard-latest.json` |
| Vitest | **87/87** | `cd frontend && npm test` |
| Playwright E2E | **47/47** | 复验 2026-07-13 02:43；无 skip |
| OpenAPI sync | **27/27** | `tests/test_openapi_sync.py` |
| R101 产品 11 项 | **11/11 auto** | `reports/R101-auto-verify-2026-07-12.md` |
| R103 预警 7 项 | **6/7 auto ☑** | debt scan 0；Q5 防丑五问待正式 DS/产品签 |
| W14 auto bundle | **PASS** | `python scripts/auto_verify_w14.py` |
| R106 pass 4 | **绿** | [`R106-final-verify-2026-07-13-pass4.md`](reports/R106-final-verify-2026-07-13-pass4.md) |
| 债务扫描 | **0 命中** | `VolumeHead` 重命名 + 去 gradient |
| targets compare | **PASS** | `scripts/compare-live-targets.mjs` |
| 最近提交 | `a6a78be` · `d9b25d8` · `4733964` | status 更新 + SPA + handbook pass4 |
| pytest 全量 | **3205 passed · 22 skipped** | glossary 恢复 + `紫微` 分类扩展 |

### 2.4 Git / 工程态

| 项 | 状态 |
|----|------|
| 已提交（batch 1–2） | `4733964` handbook · `d9b25d8` SPA · `a6a78be` status |
| **batch 3 已暂存** | **334 files** — `Makefile` · `app/core` · explain/life services · `scripts/auto_verify_*` · CI · contracts · `data/glossary.json` |
| 未纳入 batch 3 | 截图/tmp · 大字体 woff2 · `docs/design` 资产 · `static/` 构建产物 |
| pre-commit | 大 WIP 时 stash 致 smoke 失败；batch 3 建议 `--no-verify` 或干净工作区 |
| 待推 | `main` **ahead 23**；batch 3 提交后 `git push` 跑远程 CI |

---

## 三、文档分层地图

### 3.1 执行层（日常必读）

```text
DEVELOPMENT.md（总入口）
├── DEV-READINESS.md          开工前一次性自检
├── EXECUTION-PRIORITY.md     T001–T070 顺序（主轨已完成）
├── EXECUTION-REMAINING.md    R001–R110 剩余打勾 ⭐
├── INTEGRATED-DEV-PLAN.md    W1–W16 周计划
├── BAZI-ZIWEI-POLISH.md      BZ 细节索引
└── EXECUTION-PRIORITY-POST-W14.md  T071+（禁止提前）
```

### 3.2 前端层

```text
FUSHENG-FRONTEND-DEV.md（唯一权威）
├── 快速上手 / 改什么去哪
├── 视觉 token · 组件库 · 六卷 IA
├── FE-BE 适配（feBeAdapter · explain map · life volumes）
├── 预警三门禁 · 防丑五问 · 验收命令
└── 外链：DESIGN-MASTERPLAN · handbook-* · targets/
```

| 辅助 | 路径 |
|------|------|
| 30 分钟跑项目 | `guides/FUSHENG-QUICKSTART.md` |
| 节点 + 插件 | `guides/FUSHENG-NODE-CHECKLIST.md` |
| Cursor 扩展 | `guides/CURSOR-FRONTEND-EXTENSIONS.md` |
| 八字紫微对话模板 | `guides/CURSOR-BAZI-ZIWEI-PLAYBOOK.md` |
| 73 条问题台账（归档） | `archive/appendices/FUSHENG-FRONTEND-PLAN-full-2026-07-12.md` |

### 3.3 后端层

| 文档 | 用途 |
|------|------|
| `plan/BACKEND-MASTER-PLAN-2026-07-12.md` | ChartSnapshot · explain · life/volumes |
| `plan/FE-BE-DECISIONS.md` | 15 项接口决议 |
| `design/bazi/` · `design/ziwei/` | 引擎知识库 |
| `design/bazi/ENGINE-METHOD-REGISTRY.md` | 八字方法表 |
| `reports/ENGINE-CORE-PROGRESS-2026-07-11.md` | 引擎进度 |
| `guides/BACKEND-INTEGRATION-GUIDE.md` | 接入说明 |

### 3.4 契约与 API

| 产物 | 路径 |
|------|------|
| OpenAPI（150 paths） | `docs/openapi.json` |
| 前端生成类型 | `frontend/src/api/schema.d.ts` |
| 六卷 schema | `docs/contracts/life-volume.schema.json` |
| explain 映射 | `docs/contracts/explain-section-map.json` |
| 契约说明 | `docs/contracts/README.md` |

### 3.5 设计层

| 文档 | 用途 |
|------|------|
| `design/FUSHENG-DESIGN-MASTERPLAN.md` | 色 · 字 · 母版定案 |
| `design/skin-preview.html` | 样张真源 |
| `design/targets/*.png` | 冻结截图 baseline |
| `design/targets/handbook-*.md` | 三页像素手册 |
| `design/SONG-AESTHETICS-REFERENCES.md` | 宋式美学参考 |

### 3.6 验收与签字（reports/）

| 编号 | 文档 | 用途 |
|------|------|------|
| R025 | `R025-life-volume-schema-cosign-draft` | schema 三方共签 |
| R060 | `R060-trial-read-checklist` | 试读 step 10 |
| R079 | `R079-anti-slop-five-questions` | 防丑五问 15 格 |
| R084/R102 | `R084-self-check` · `R102-design-spotcheck` | 三页自检 |
| R094 | `R094-openapi-sync` | OpenAPI 双端 |
| R096 | `R096-life-volumes-draft` | life API 草案 |
| R100–R106 | F6 / 终验复跑 | 自动化签收 |
| R104/R105 | M4/M5 产品试 | 能传 / 能辩 |
| R107 | `R107-w14-signoff-draft` | **收官签字表** |
| R108 | release-notes draft/generated | PR 发布说明 |
| R109 | POST-W14 决议 | 默认选项 A 延后 GTM |

### 3.7 归档（勿作执行依据）

| 目录 | 说明 |
|------|------|
| `archive/superseded/dev-consolidation-2026-07-12/` | 16 份冗余开发文档 |
| `archive/appendices/*-full-2026-07-12.md` | UI-DEV / PLAN / RISK 全文备份 |
| `archive/history/` | 阶段周报 |
| 索引 | `DOCS-AUDIT.md` |

---

## 四、待办与问题清单（按角色）

### 4.1 产品 / PM

| ID | 问题 | 状态 | 动作 |
|----|------|------|------|
| R060 | 15 分钟试读主观评分 | 🟡 | 填 `R060-trial-read-checklist` step 10 |
| R104 | M4「能传」外发试读 | 🟡 3/4 | 发 `live-report-toc.png` 给非开发者；#3 签字 |
| R105 | M5「能辩」 | 🟡 | 4 维已记录；产品正式签字 |
| R109 | POST-W14 决议 | ☐ | 默认 **选项 A**：继续打磨，不启 GTM |

### 4.2 设计 / DS

| ID | 问题 | 状态 | 动作 |
|----|------|------|------|
| R079 Q5 | 防丑五问盲测 | 🟡 | 15/15 代理 ☑；**产品姓名行**待正式补签 |
| R102 | live vs frozen 并排 | ☑ compare | height 差为 advisory（viewport vs skin-preview） |
| R085 | 三页+报告自检签字 | 🟡 | 依赖 R079 正式签 |

### 4.3 前端

| ID | 问题 | 状态 | 动作 |
|----|------|------|------|
| — | 主路径 UI / 六卷 / FE-BE | ✅ | lint 0 warning · debt scan 0 |
| — | Legacy `ZiweiView.css` 旧色 | 🟡 低 | 非 `/new/*` 主路径；可后置清理 |
| R108 | 发布说明附 PR | 🟡 草案就绪 | attach 截图 + generated md |

### 4.4 后端

| ID | 问题 | 状态 | 动作 |
|----|------|------|------|
| R025 | life-volume schema 共签 | ☐ | 契约测试绿；三方签字 |
| — | 未提交 WIP | 🔴 | schemas · explain · life_volume · 大量 services 待分批 commit |
| — | `make` on Windows | 🟡 | 用 `python scripts/*.py` 替代；CI 为准 |

### 4.5 工程 / DevOps

| ID | 问题 | 状态 | 动作 |
|----|------|------|------|
| — | 推 PR 清 CI drift | ☐ | `git push` + OpenAPI job 绿 |
| — | 剩余 WIP 分批提交 | 🔴 | 避免单 commit 夹带半套迁移 |
| — | pre-commit 本地 | 🟡 | 需 Python 3.11 或干净暂存区；大 WIP 时易失败 |
| R107 | W14 负责人签字 | ☐ | 填 `R107-w14-signoff-draft` |
| R110 | 标 T070 ☑ | ☐ | R107 后更新 `EXECUTION-PRIORITY` 顶部 |

### 4.6 全员 onboarding（仍 ☐，不阻塞自动化）

| ID | 任务 |
|----|------|
| R001–R006 | 环境 · 扩展 · 通读 `DEVELOPMENT.md` + 执行清单 §一 |

---

## 五、已完成项摘要（勿返工）

| 域 | 已完成 |
|----|--------|
| **前端主路径** | `/` · `/profile` · `/new/bazi` · `/new/ziwei` · `/report`；宋式 token；六卷+跋 |
| **FE-BE** | `feBeAdapter` · explain batch · life volumes 可选远程路径 |
| **E2E** | 47 项全绿（试读 · anti-slop · snapshot · life-volumes · targets） |
| **引擎** | scorecard 24/24；ZW03/iztro 对照轨 CI advisory |
| **文档整合** | `DEVELOPMENT` + `FRONTEND-DEV` 单入口；16 份旧文档归档 |
| **OpenAPI** | 150 paths 已导出并提交 `cd366bd` |

---

## 六、推荐执行顺序（收官前）

```text
1. 提交 batch 3（backend + Makefile + scripts + CI + data/glossary + data/cities）
2. git push → 确认远程 CI 全绿（OpenAPI · test-fast · E2E 47）
3. R104 #3 外发截图 → R104/R105 产品签字
4. R025 三方共签 + R060 step 10
5. R079 正式姓名补签 → R085 ☑
6. R107 负责人签字 → R110 标 T070 ☑
7. 再评估 R109（默认仍选项 A，不开 POST-W14）
```

**batch 3 提交前自检（均已绿）：**

| 检查 | 命令 |
|------|------|
| pytest | `python -m pytest -q --ignore=tests/e2e --ignore=tests/legacy` → 3205 passed |
| W14 | `python scripts/auto_verify_w14.py` → 7/7 |
| OpenAPI | `make export-openapi` + `npm run gen:types`（已同步入暂存） |
| 前端 | `python scripts/quality_gate.py --section frontend` |

---

## 七、验收命令速查

```powershell
# 引擎
python scripts/audit_scorecard.py

# 后端 smoke
python scripts/quality_gate.py --section backend
python -m pytest -q tests/test_openapi_sync.py tests/test_explain_*.py

# 前端
cd frontend
npm run type-check
npm run test
npm run test:e2e

# 设计对比
node scripts/compare-live-targets.mjs

# W14 -bundle
python scripts/auto_verify_w14.py
python scripts/auto_verify_r103.py
python scripts/generate_r108_release.py
```

---

## 八、与旧审计文档的关系

| 文档 | 说明 |
|------|------|
| `DEV-AUDIT-2026-07-12.md` | **历史中期审计**（多处已过时，如 E2E 红、explain 未建） |
| **本文** | **2026-07-13 现状**；冲突时以本文 + `EXECUTION-REMAINING` 为准 |

---

## 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| status-1.0 | 2026-07-13 | 整合文档地图、进度、问题、收官顺序；commit cd366bd 后 |
