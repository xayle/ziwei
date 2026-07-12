# 浮生 · 后端后续开发文档

| 字段 | 内容 |
|------|------|
| **版本** | v1.4（紫薇资产对照 + 方案优化） |
| **制定日期** | 2026-07-12 |
| **基线** | ENGINE-CORE ✅ · P0–P1 + P2-02 ✅ · Scorecard **24/24** |
| **pytest** | **3135 passed** |
| **黄金盘** | **GT 50 · ZW 20 · DV 10** |
| **北极星** | 引擎可信 + **市面可售体验**；优先「移植已有」而非「重写后端」 |

**关联：** [ENGINE-CORE-FIX-PLAN](./ENGINE-CORE-FIX-PLAN-2026-07-11.md) · [PRODUCT-P-ROADMAP](./PRODUCT-P-ROADMAP-2026-07-12.md) · [八字 Gap](../design/bazi/bazi-gap-audit.md) · [紫微 Gap](../design/ziwei/ziwei-gap-audit.md) · [方法注册表](../design/bazi/ENGINE-METHOD-REGISTRY.md) · [结项](../reports/BACKEND-FOLLOWUP-CLOSEOUT-2026-07-12.md) · **姊妹库** `../紫薇`（v8 全量 SPA，前端可移植源）

---

## 一、文档定位

前端 P 路线图（`PRODUCT-P-ROADMAP`）已把主路径「算到了、用得浅」抬到 **P≈9.36**。  
**本文件**覆盖 **后端独有** 的后续工作：引擎加深、语料门禁、API/编排、PDF/异步、平台能力与 Scorecard 补洞。

| 维度 | 前端路线图 | 本后端文档 |
|------|------------|------------|
| 主战场 | UI 上浮、E2E、档案 | 引擎、语料、Schema、回归、CI |
| 改动范围 | `frontend/` | `services/`、`routers/`、`app/schemas/`、`data/`、`tests/`、`scripts/` |
| 已完成 | 8 周 P 计划 | ENGINE-CORE + 流日三维 + patterns tier |

---

## 二、当前架构（后端分层）

```
请求
  └─ routers/*.py          # HTTP 边界、参数校验、权限
       └─ services/*_service.py / bazi_full_service.py   # 编排、enrich、provenance
            └─ services/bazi_engine/   # 八字权威算法
            └─ services/ziwei_engine/ # 紫微权威算法
            └─ services/name_engine/ | fengshui_engine/ | liuyao_engine/ …
       └─ app/schemas/*.py  # Pydantic 契约 → OpenAPI
       └─ app/models/*.py    # 持久化（Case、Member、Audit…）
```

| 层 | 规模（约） | 原则 |
|----|------------|------|
| `services/bazi_engine/` | 30+ 模块 | 单轨计算；`missing_fields` 显式 |
| `services/ziwei_engine/` | 20+ 模块 | dataclass + `engine_warnings` |
| `routers/` | 36 文件 | 薄路由；算法不进 router |
| `tests/` | 127 文件 | 黄金回归 + boost 覆盖 + 引擎单测 |

**禁止：** 新代码引用 `app/core/solar_time.py`（废弃）；`bazi_full_service` 内联五行/强弱（已删，统一 `compute_core_metrics()`）。

---

## 三、工具链与插件（开发日常）

### 3.1 本地 IDE

| 工具 | 用途 | 配置 |
|------|------|------|
| **Ruff** | lint + format | 改 `.py` 后 **Ctrl+S** 自动 format（项目已配） |
| **Pyright** | 类型检查 | `make lint` / CI `lint` job |
| **pre-commit** | 提交前钩子 | `make dev-install` 安装 |
| **Cursor Agent** | 多文件重构 | 引擎任务限定目录见 §八 |

### 3.2 Makefile 命令（后端必记）

| 命令 | 何时跑 |
|------|--------|
| `make format` | 批量整理 Python |
| `make lint` | PR 前（ruff + pyright） |
| `make test` | 改引擎/路由后 |
| `make test-fast` | 大改动（pytest `-n auto`） |
| `make scorecard` | 语料/黄金盘/门禁改动后 |
| `make export-openapi` | 改 `app/schemas/*` 后 |
| `make sync-frontend-types` | Schema 变更 **必须**（生成 `frontend/src/api/schema.d.ts`） |
| `make verify-classics-ctext` | B-07 语料门禁 |
| `make spotcheck-ctext` | 人工 spotcheck 清单 |
| `make verify-iztro` / `verify-iztro-hour` | 紫微 iztro 交叉（advisory） |
| `make quality-gate-backend` | 对齐 CI test job |

### 3.3 CI（`.github/workflows/ci.yml`）

| Job | 后端相关 |
|-----|----------|
| `lint` | ruff、pyright、bandit |
| `test` | `quality-gate-backend` + `test-fast` + sxtwl + iztro advisory |
| `test-postgres` | Case/DB 集成 |

### 3.4 MCP / 辅助（可选）

| 能力 | 场景 |
|------|------|
| **cursor-ide-browser** | 本地起服务后冒烟 `/docs`、`/health` |
| **Explore 子代理** | 大范围 `services/` 摸底 |
| **Task + shell** | 跑 `make test` / `scorecard` 批量验证 |

---

## 四、基线与 Scorecard 缺口

### 4.1 已通过（24 项）

八字 B-01~B-10；紫微 Z-01~Z-10；交叉 X-01~X-04。  
黄金：**GT 50 + ZW 20**，对齐率 **100%**；双验 **DV 10**。

### 4.2 未通过（2 项 · stretch_perfect）— ✅ 已于 2026-07-12 修复

| ID | 分数 | 失败检查 | 根因 | 修复 |
|----|------|----------|------|------|
| **B-07** | ~~9.5~~ **10.0** | `stretch_perfect` | `audit_scorecard.py` 以 `scripts/` 为 `sys.path[0]`，`services` 导入静默失败 | `sys.path.insert(0, ROOT)`；语料数据已满足（ctext 47、ziwei 122） |
| **Z-07** | ~~8.5~~ **10.0** | `stretch_perfect` | 同上 `ziwei_ref_ok=False` | 同上 |

**Scorecard 判定逻辑**（`scripts/audit_scorecard.py`）：

```python
# B-07 stretch
ziwei_ref_ok and classics_ctext_n >= 40 and ctext_verify.exists()

# Z-07 stretch  
ziwei_ref_ok  # catalog_self_check: count>=100 and with_ctext_page==count
```

### 4.3 引擎 Gap（审计文档残留）

| 来源 | 项 | 严重度 | 后端动作 |
|------|-----|--------|----------|
| bazi-gap-audit §4.1 | 流日深度联动 | 低 | ✅ 三维分 + `missing_fields`（2026-07-12）；可继续 LR 黄金例扩面 |
| bazi-gap-audit §4.2 | CLS `source_page` 人工核 | 中 | `scripts/spotcheck_ctext_pages.py` + `verification_status` |
| closeout residual | ZW13–16 iztro pending | 中 | `scripts/verify_ziwei_iztro.mjs` 校准 |
| closeout residual | PDF 双轨附录 | 低 | ✅ POC（`fusheng_report_service`） |
| bazi.py 注释 | 流年报告任务内存 dict | 中 | Redis/DB 任务队列（P2-01） |

---

## 四之二、竞品对照与产品缺陷（2026-07-12）

> 对照对象：**文墨天机**（专业紫微标杆）、**测测**（泛心理+社区+AI）、**灵机妙算/天乙八字**（术数聚合+教学）、**紫微派/iztro**（在线排盘工具）。  
> 内部 UI 调研见 [FUSHENG-FRONTEND-HANDBOOK §1.5](../guides/FUSHENG-FRONTEND-HANDBOOK.md)。

### 4.2.1 能力矩阵（浮生 vs 市面）

| 维度 | 文墨天机 | 测测 | 灵机/天乙 | 浮生现状 | 缺口 | 后端相关度 |
|------|----------|------|-----------|----------|------|------------|
| **排盘精度/流派可配** | ★★★★★ 北南派、童限、全运限 | ★★★ 娱乐向 | ★★★★ 多术数 | ★★★★★ 引擎+黄金回归 | 流时/童限产品化弱 | 中 |
| **流月流日流时** | Pro 全链路切换 | 运势摘要 | 部分有 | API 有、主路径展示浅 | 时间轴「用得浅」 | 中 |
| **八字×紫微同屏** | 中宫显四柱大运 | 分工具 | 部分同屏 | 分模块+Report 合章 | 缺「一屏双盘」API 编排 | 中 |
| **跨端** | Web+Win/Mac+iOS+Android | 原生 App | App 为主 | **响应式 Web only** | **无原生/PWA/小程序** | 低（前端为主） |
| **AI 解读** | 结构化文本→第三方 LLM | **AI 聊天+达人 1v1** 主导 | 断法对照+提示词 | Report 嵌入；dev 默认 Mock | **无对话式 AI、无达人撮合** | **高** |
| **社区/社交** | 弱 | **动态/小组/悬赏问答** | 论坛式 | share-token API **无 UI** | **无社区、无裂变** | 中 |
| **付费/变现** | Pro 买断 | 订阅+咨询抽成 | 广告+解锁 | **无支付链路** | 无商业化基础设施 | 中 |
| **合盘/缘分** | 专业合参 | **连线合盘+微信好友**  viral | 有 | Extension 合盘 | 缺「一键分享合盘结果」 | 中 |
| **个人档案** | 多盘本地 | **多档案+关系图谱** | 案例库 | Profile+云同步 | 家庭成员 API 未产品化 | 中 |
| **分享传播** | 弱 | 测试卡片/合盘分数 | 截图 | PNG 卡 API **未接 UI** | **分享闭环断裂** | 中 |
| **择日/扩展术数** | — | MBTI/塔罗等 | 奇门六爻等 | 择日 Extension；**六爻/风水/西方 API 无页** | 术数超市缺失 | 低（有意收窄） |
| **推送/日运** | — | **日运提醒** | 流年推送 | **无通知中心** | 留存手段缺失 | 中 |
| **可信度/双轨** | 无公开 | 无 | 无 | **recorded vs engine + iztro** | — | **差异化优势** |
| **典籍出处** | 断语内置 | 模板化 | 教学对照 | **classical layer + ctext** | 人工 verified 仅 4% | 中 |
| **工程回归** | 不公开 | 不公开 | 不公开 | **3135 pytest + 黄金盘** | — | **差异化优势（ToB/执业）** |

### 4.2.2 缺陷分级（结合代码库实证）

#### A. 致命差距（影响「能不能当商品卖」）

| ID | 缺陷 | 竞品参照 | 浮生现状 | 建议优先级 |
|----|------|----------|----------|------------|
| **MKT-A01** | 无原生 App / 小程序 | 文墨、测测均为 App 主战场 | 仅 Web | P3 产品；后端保持 API-first |
| **MKT-A02** | AI 体验断层 | 测测：档案底座 + 多轮对话 + 备案模型 | `llm.py` 完备，**仅 Report 嵌入**；无 key 时 Mock | **P2-03 必做** + P3 对话 API |
| **MKT-A03** | 分享/裂变未闭环 | 测测：微信合盘、测试卡片 | `share-token`、`export/png` **有 API 无 UI** | P3：薄路由 + 前端 1 周 |
| **MKT-A04** | 无付费与权益 | 全行业 freemium | 零支付/webhook | P3 商业化；后端需 quota 中间件 |

#### B. 体验差距（影响留存与口碑）

| ID | 缺陷 | 说明 | 后端动作 |
|----|------|------|----------|
| **MKT-B01** | 「算到了、用得浅」 | 合冲刑害、神煞、pattern tier 仍在 Trust 折叠区 | 编排层把 `relations`/`shensha` 提升为 first-class enrich |
| **MKT-B02** | 流年报告同步阻塞 | 竞品多为异步+推送 | **P2-01** Redis/DB 队列 |
| **MKT-B03** | 流月流日「专业感」不足 | 文墨 Pro 一键切换运限 | `ziwei/full` + timeline 统一 `target_date` 链；补流时 API 文档 |
| **MKT-B04** | 家庭成员/多档案 | 测测多档案；文墨多盘 | `members` API 存在，前端仅云同步 | P3 编排 `members` ↔ cases |
| **MKT-B05** | 术数扩展入口缺失 | 竞品为「超市」 | 六爻/风水/西方 **API 存量**；新产品化见 §十一 |
| **MKT-B06** | 典籍 verified 比例低 | 天乙强调断法对照 | `verification_status` 4% → 目标 20%+ spotcheck | 脚本+人工批次 |

#### C. 相对优势（应持续放大，勿丢）

| 优势 | 市面稀缺性 | 巩固动作 |
|------|------------|----------|
| 双轨格局 + ZIP 漂移清单 | 竞品几乎不展示口径冲突 | Report/PDF 双轨表已 POC；API 保持 `recorded_geju` |
| iztro 交叉核验 + `engine_warnings` | 专业用户可核对 | 保持 advisory CI；右弼口径文档化 |
| `missing_fields` 显式 | 竞品常静默省略 | 契约测试 + 前端 Trust 层 |
| 黄金回归 + Scorecard | 执业/开发者信任 | GT/ZW 继续扩面；align ≥99% |
| 分层断语 classical/engine/heuristic | 测测偏模板 AI | LLM 必须引用 `provenance.layer`（P2-03） |

### 4.2.3 缺陷 → 开发编号映射

```
竞品缺口                后端文档编号          主战场
─────────────────────────────────────────────────────
AI 对话 + 引擎引用      BE-P2-03, BE-P3-01   services/llm_service
流年报告异步            BE-P2-01             routers/bazi.py
分享 PNG/合盘卡片       BE-P3-02             routers/export + share
结构化导出(LLM)         BE-P3-03             bazi_full + ziwei router
配额/限流商业化         BE-P2-04, BE-P3-04   middleware + batch
神煞/关系上浮           BE-P3-05             bazi_full_service enrich
典籍 verified 提升      BE-P3-06             classics pipeline
推送/日运(可选)         BE-P3-07             新 notification 模块
```

### 4.2.4 原方案不足（v1.3 审阅 · 2026-07-12）

对照姊妹库 `d:\Users\Administrator\Desktop\紫薇` 后，v1.3 竞品方案需修正：

| 原假设 | 实际情况 | 修正 |
|--------|----------|------|
| MKT-A03 需新建 `routers/share.py` | c2 **已有** `cases` share-token + `export/card` PNG | **前端移植优先**；后端仅补 OpenAPI 示例与限流 |
| 缺口主要靠后端新 API | **后端 32 路由与 c2 同集**，c2 还多 `fusheng_report` | 瓶颈在 **Fusheng v3 前端裁剪**，非引擎 |
| 术数/AI/分享要从零做 | 紫薇 **legacy SPA 已完整承接**（见其 `FRONTEND-FEATURE-MATRIX`） | 选择性回迁 Extension + AI 面板 |
| 引擎可从紫薇回迁 | 紫薇 `services/` 为 c2 **子集**（无 dual_track/iztro/provenance） | **禁止**回迁引擎；c2 为权威后端 |
| `scripts/seed_data.py` 在紫薇可抄 | **两库均只有引用、无实体文件**（`start-local.ps1` 断链） | 新增 BE-P3-08 统一 seed 脚本 |
| P3 与前端解耦可并行 | MKT-A02/A03/B04/B05 **80% 是前端工作** | 增加 FE-PORT 编号，与 BE 任务绑定验收 |

---

## 四之三、姊妹库「紫薇」可复用资产（2026-07-12）

> 路径：`d:\Users\Administrator\Desktop\紫薇`（BaZi v8.0.10 · 910 tests · 全量 legacy SPA）  
> 对照清单：`紫薇/docs/reports/FRONTEND-FEATURE-MATRIX-2026-04-29.md`（**c2 已删页面的能力地图**）

### 4.3.1 仓库关系结论

```
紫薇 (v8 SPA)                    c2 / 浮生 (v3)
─────────────────────────────────────────────────────────
32 routers  ≈ 同集              + fusheng_report.py
services/   ⊂ c2 子集            + provenance/dual_track/iztro
data/       ⊂ c2 子集            + GT/ZW/DV 黄金盘
frontend/   全量 20+ 视图         14 视图（Fusheng 主路径）
monitoring/ ≡ 相同               docker-compose 相同
```

**结论：** 从紫薇「挖」的价值 = **前端工作区 + 少量脚本/测试**；**不要**回迁 `services/` / `routers/`。

### 4.3.2 可直接移植（高价值 · 低风险）

| 来源（紫薇） | 能力 | 填补缺口 | 迁入 c2 目标 |
|--------------|------|----------|--------------|
| `frontend/src/api/export.ts` | JSON/PDF/**PNG 卡片**下载 | **MKT-A03** | `frontend/src/api/export.ts` |
| `frontend/src/components/report/ReportTopBar.vue` | 分享链接 + PDF + 卡片按钮 | **MKT-A03** | `ReportView` 顶栏或 `NewAppShell` |
| `frontend/src/api/report.ts`（`createShareToken`） | share-token 客户端 | **MKT-A03** | 合并进 `api/cases.ts` 或独立 `share.ts` |
| `tests/test_share_card_exporter.py` | PNG 卡回归 | API 已有、专测缺失 | `tests/` |
| `scripts/check_day_gz.py` | 日柱 sxtwl 诊断 | 边界回归工具 | `scripts/` |
| `docs/reports/FRONTEND-FEATURE-MATRIX-*.md` | API→页面映射 | 扩展规划索引 | 复制到 `docs/reports/` 作 **PORT 清单** |

### 4.3.3 适配后移植（中价值）

| 来源 | 能力 | 适配要点 | 缺口 |
|------|------|----------|------|
| `AppRightPanel.vue` + `stores/ai.ts` | 流式 AI 侧栏、模板、草稿 Tab | 接入 Trust/provenance；挂 `NewAppShell` | **MKT-A02** |
| `views/LlmDraftsView.vue` | 草稿管理页 | 路由 `/extensions/ai`；档案守卫 | **MKT-A02** |
| `views/MemberView.vue` + `api/members.ts` | 家庭成员 | 与 Profile 云同步合并 | **MKT-B04** |
| `views/ZiweiBatchView.vue` | 批量紫微 CSV | + `routers/ziwei batch` 限流（P2-04） | 执业场景 |
| `composables/ziwei/useZiweiTimelineControls.ts` 等 | 运限 overlay 控件 | 对照 `FushengZiweiTimeline.vue` 补缺口 | **MKT-B03** |
| `views/LiuyaoView` / `FengshuiView` / `WesternView` / `TarotView` | 扩展术数页 | ExtensionHub 新卡片 + fusheng 样式 | **MKT-B05** |
| `views/WorkbenchView.vue` + `workbench/*` | 案例枢纽 | **勿整页回迁**；抽取 CRUD/导出流进 Profile | 执业 |
| `views/AdminView.vue` | 运营后台 | 薄管理页或保持 API-only | 低优 |

### 4.3.4 明确不迁移

| 类别 | 原因 |
|------|------|
| `services/*`、`routers/*`（紫薇版） | c2 超集且带 Scorecard 门禁 |
| `AppNav` / `AppShell` / `BaziView` / `ZiweiView` 整页 | 与 Fusheng v3 信任层冲突 |
| `scripts/archive/_mlk_*`、`_els_*`、`_swf_*` | 逆向工程垃圾 |
| `data/*.json` | c2 已更多 |
| `HumanDesignView` / `NumerologyView` | 占位模块，竞品也不靠此取胜 |

### 4.3.5 紫薇 × 竞品 × 方案 三联缺口（仍缺）

| 缺口 | 紫薇 | c2 | 市面 | 下一步 |
|------|------|-----|------|--------|
| 原生 App | ❌ | ❌ | ✅ | PWA/小程序壳（前端） |
| 付费/配额 | ❌ | ❌ | ✅ | **BE-P3-04** 两库皆需新建 |
| 推送通知 | ❌ | ❌ | ✅ | **BE-P3-07** 两库皆需新建 |
| 社区 Feed | ❌ | ❌ | ✅测测 | 不做重社区；轻分享优先 |
| 分享裂变 UI | ✅ legacy | ❌ v3 | ✅ | **FE-PORT-01**（1 周） |
| AI 对话工作区 | ✅ 侧栏+草稿 | ⚠️ Report only | ✅ | **FE-PORT-02** + P2-03 |
| 双轨/iztro/Scorecard | ❌ | ✅ | ❌ | **保持 c2 优势，勿回迁** |

---

## 五、后续开发优先级（P0 → P2）

### P0 — Scorecard 24/24（估 2–3 周）— ✅ 已完成

| 编号 | 任务 | 主要文件 | 验收 | 状态 |
|------|------|----------|------|------|
| **BE-P0-01** | 紫微语料 100+ 全量 ctext | `services/ziwei_classic_refs.py` | `catalog_self_check().ok == True` | ✅ 122/122 |
| **BE-P0-02** | 八字 classics ctext 标注 ≥40 | `data/classics.json` | B-07 stretch | ✅ 47 条 |
| **BE-P0-03** | `verification_status` 管线固化 | `scripts/batch_classics_verification.py`、`scripts/verify_classics_ctext.py` | `verify-classics-ctext` 绿 | ✅ verified=20 |
| **BE-P0-04** | ZW13–16 iztro 校准 | `data/ziwei_ground_truth.json` | 主星 14/14 + `iztro_calibration` | ✅ `main_match`（右弼 hour 与 iztro 仍有已知辅煞差） |
| **BE-P0-05** | Scorecard 导入路径 | `scripts/audit_scorecard.py` | `python scripts/audit_scorecard.py` → 24/24 | ✅ `sys.path` 修复 |

### P1 — 引擎加深（估 4–6 周）— ✅ 已完成

| 编号 | 任务 | 主要文件 | 验收 | 状态 |
|------|------|----------|------|------|
| **BE-P1-01** | 流日 enrich 流年上下文 | `services/bazi_full_service.py` | LR 用例 `flow_score_liunian` 非空 | ✅ |
| **BE-P1-02** | 格局 tier 引擎巩固 | `tests/test_ziwei_pattern_false_positive.py` | ZW01–ZW16 负例全绿 | ✅ |
| **BE-P1-03** | forecast evidence 链稳定 | `app/schemas/ziwei.py`、`routers/ziwei.py` | API tier + layer + evidence_chain | ✅ |
| **BE-P1-04** | 黄金盘扩面 | `scripts/expand_golden_cases.py` | GT≥50、ZW≥20、DV≥10 | ✅ |
| **BE-P1-05** | OpenAPI 与引擎同步 CI | `.github/workflows/ci.yml`、`tests/test_openapi_sync.py` | export drift + schema 字段测试 | ✅ |

### P2 — 平台与扩展 API（估 6–10 周）

| 编号 | 任务 | 主要文件 | 验收 | 状态 |
|------|------|----------|------|------|
| **BE-P2-01** | 流年报告异步队列 | `routers/bazi.py`、Redis/DB worker | 生产可水平扩展 | 待办 |
| **BE-P2-02** | PDF 双轨附录 | `services/fusheng_report_service.py` | 服务端 PDF 含双轨表 | ✅ POC |
| **BE-P2-03** | LLM 解读与引擎 provenance 对齐 | `services/llm_service.py` | 草稿带 `layer` 引用 | 待办 |
| **BE-P2-04** | 相似盘 / 批量 v2 硬化 | `routers/v2/batch.py` | 限流 + 回归 | 待办 |
| **BE-P2-05** | RBAC 审计性能 | `services/permission_cascade_service.py` | 权限测试无回归 | 待办 |

### P3 — 竞品缺口与商业化（估 8–12 周 · v1.4 优化）

> **策略调整：** 先 **FE-PORT（紫薇前端移植）** 填 MKT-A02/A03，再补后端绿字段（配额/通知/结构化导出）。  
> 避免重复建设已有 API。

| 编号 | 任务 | 主要文件 | 验收 | 状态 |
|------|------|----------|------|------|
| **FE-PORT-01** | 分享/export 前端（紫薇移植） | `export.ts`、`ReportTopBar` 逻辑 | PNG 卡 + share-token + PDF 一键；E2E | **优先** |
| **FE-PORT-02** | AI 侧栏 + 草稿页（紫薇适配） | `AppRightPanel` → `NewAppShell` | 流式 SSE + provenance 提示 | 待办 |
| **FE-PORT-03** | Extension 扩展 4 模块 | 紫薇 `Liuyao/Fengshui/Western/Tarot` views | ExtensionHub 4 卡片可算 | 待办 |
| **FE-PORT-04** | 家庭成员页 | 紫薇 `MemberView` + `members` API | Profile 子 Tab 或 `/extensions/family` | 待办 |
| **FE-PORT-05** | 时间轴控件补强 | 紫薇 `useZiweiTimelineControls` | 对照 `FushengZiweiTimeline` diff 为 0 交互回归 | 待办 |
| **BE-P3-01** | LLM 对话 API 硬化 | `routers/llm.py` | 多轮 SSE + `layer` 引用（侧栏消费） | 待办 |
| **BE-P3-02** | 分享 API 文档+限流 | `routers/export.py`、`cases.py` | OpenAPI 示例；**不新建** share 路由 | 待办 |
| **BE-P3-03** | 结构化命盘导出 | `routers/bazi.py`、`ziwei.py` | Markdown/JSON（文墨式 LLM 工作流） | 待办 |
| **BE-P3-04** | 配额 Freemium | `middleware/quota.py` | batch/llm/export 分档 | 待办 |
| **BE-P3-05** | 关系/神煞 enrich 上浮 | `bazi_full_service.py` | `relations_summary` 默认返回 | 待办 |
| **BE-P3-06** | 典籍 verified ≥20% | `batch_classics_verification.py` | ≥20% verified | 待办 |
| **BE-P3-07** | 日运/换运提醒 | 新 `notifications` 模块 | 邮件/WebPush stub | 待办 |
| **BE-P3-08** | 本地 seed 脚本修复 | 新 `scripts/seed_data.py` | `start-local.ps1` 绿；admin+样例案 | 待办 |
| **BE-P3-09** | 分享卡/导出回归 | 紫薇 `test_share_card_exporter.py` | 并入 c2 pytest | 待办 |

**推荐执行顺序（修订）：**

```
W13  FE-PORT-01 分享/export UI     ← 紫薇移植，最快填 MKT-A03
W14  FE-PORT-02 AI 侧栏            ← 紫薇 + P2-03 provenance
W15  P2-01 流年报告异步
W16  FE-PORT-03/04 Extension+家庭
W17  BE-P3-03 结构化导出 + BE-P3-05 enrich
W18  BE-P3-04 配额
W19–20  BE-P3-06/07/08 典籍+通知+seed
```

## 六、按周计划（12 周 · 后端专轨）

> 与前端解耦；可与 `PROJECT-PLAN-9.5-TARGET` 并行。

| 周 | 主题 | 交付 | Gate |
|----|------|------|------|
| **W1** | 语料 P0 | BE-P0-01/02：`ziwei_classic_refs` ctext 补全 | `catalog_self_check` |
| **W2** | 语料 P0 | BE-P0-03：top-50 verified + batch 脚本 | B-07 stretch |
| **W3** | iztro | BE-P0-04：ZW13–16 校准 | `make verify-iztro-hour` |
| **W4** | Scorecard | 复跑 scorecard → **24/24** | `make scorecard` |
| **W5** | 流日 | BE-P1-01：liunian 上下文 + LR 扩例 | `test_liuri_flow_score` |
| **W6** | 紫微格局 | BE-P1-02：patterns tier 负例包扩面 | golden + false_positive |
| **W7** | forecast | BE-P1-03：evidence_chain API 稳定 | `test_ziwei_engine` |
| **W8** | 黄金盘 | BE-P1-04：GT/ZW/DV 扩面 | align ≥99% |
| **W9** | OpenAPI | BE-P1-05：CI 强制 sync-frontend-types | `test_openapi_sync` |
| **W10** | PDF | BE-P2-02：双轨附录 POC | `test_fusheng_report_pdf` |
| **W11** | 异步 | BE-P2-01：liunian-report 队列设计 | 压测 |
| **W12** | 结项 | `BACKEND-FOLLOWUP-CLOSEOUT.md` + 全量回归 | pytest + scorecard |
| **W13** | **FE-PORT-01** | 紫薇 `export.ts` + 分享顶栏移植 | E2E 分享/PNG |
| **W14** | **FE-PORT-02** | AI 侧栏 + P2-03 provenance | SSE + layer |
| **W15** | P2-01 | 流年报告异步队列 | 压测 |
| **W16** | FE-PORT-03/04 | Extension 四模块 + 家庭成员 | ExtensionHub |
| **W17** | BE-P3-03/05 | 结构化导出 + 神煞上浮 | OpenAPI |
| **W18** | BE-P3-04 | 配额中间件 | 限流测试 |
| **W19–20** | BE-P3-06/07/08 | 典籍 verified + 通知 stub + seed | pytest |

---

## 七、模块任务清单（按目录）

### 7.1 `services/bazi_engine/`

| 模块 | 状态 | 后续 |
|------|------|------|
| `pillars.py` | ✅ v2 权威 | 边界用例文档化 |
| `geju.py` / `yongshen.py` | ✅ 子平链 | 外格语料软链扩面 |
| `liuri.py` | ✅ 三维分 + missing | enrich 流年上下文（P1） |
| `dual_track.py` | ✅ ZIP 登记 | 与 GT 四柱键一致性测试 |
| `classic_refs.py` | ✅ 480+ | ctext `source_page` 人工核 |
| `strength.py` | ✅ factors | 文档进 ENGINE-METHOD-REGISTRY |
| `analysis/*` | ✅ | LLM 引用 provenance（P2） |

### 7.2 `services/ziwei_engine/`

| 模块 | 状态 | 后续 |
|------|------|------|
| `patterns.py` | ✅ tier | 余格负例持续收紧 |
| `forecast.py` | ✅ | API 与 Timeline 字段对齐 |
| `iztro_crosscheck.py` | ✅ advisory | ZW13–16 纳入 CI |
| `compatibility.py` | ✅ heuristic | 保持 `layer=heuristic` |
| `liuri.py` | ✅ 可选 | 与八字流日互证（低优） |

### 7.3 `services/` 编排层

| 文件 | 后续 |
|------|------|
| `bazi_full_service.py` | liuri enrich、classic_refs、provenance 单点 |
| `bazi_engine_service.py` | enrich 失败 → `missing_fields` 不吞异常 |
| `fusheng_report_service.py` | PDF 双轨、服务端模板 |
| `pdf_exporter.py` | 附录表、字体/分页 |
| `llm_service.py` | 模块解读引用 `analysis_structured` |

### 7.4 `routers/`（高流量）

| 路由 | 后续 |
|------|------|
| `bazi.py` | 流年报告异步化；`liuri-liushi` 文档示例 |
| `ziwei.py` | `batch` 限流；`multi_compat` 产品化前保持 API |
| `fusheng_report.py` | PDF 双轨附录 |
| `cases.py` / `compute.py` | ZiweiAlgo 一等字段全量同步 |
| `llm.py` | provenance 回写 drafts |

### 7.5 `data/` + `scripts/`

| 资产/脚本 | 后续 |
|-----------|------|
| `ground_truth_cases.json` | LR/GT 扩面；ZIP 四柱键审计 |
| `ziwei_ground_truth.json` | ZW17+ 边界盘 |
| `dual_verify_cases.json` | DV09+ |
| `classics.json` | verification_status 比例提升 |
| `audit_scorecard.py` | stretch 条件文档化 |
| `verify_ziwei_iztro.mjs` | ZW13–16 纳入默认跑 |

---

## 八、单任务工作流（引擎改动模板）

> 适用于「只改引擎」类 PR；摘自团队约定。

```
【任务】{具体一项，如：补 liuri 流年上下文 / 修 ZIP09 四柱键 / 扩 ziwei_classic_refs ctext}

1. 改动范围
   - 优先 services/bazi_engine/ 或 services/ziwei_engine/
   - 编排变更 → bazi_full_service.py / ziwei 路由薄层
   - Schema 变更 → app/schemas/*.py

2. 契约
   - missing_fields 显式登记；禁止静默 50 分 / 空字符串占位
   - provenance.layer 保持 classical | engine | heuristic

3. 验证（顺序）
   make format          # 或 Ctrl+S Ruff
   make test            # 或 pytest tests/test_xxx.py
   make scorecard       # 语料/黄金盘相关必跑

4. API 变更时
   make sync-frontend-types
   tests/test_openapi_sync.py

5. PR 描述
   - 任务编号 BE-Px-xx
   - Scorecard ID（B-xx / Z-xx）
   - 黄金例是否新增/变更
```

### 8.1 示例：仅 `services/bazi_engine/`（2026-07-12 已做）

| 项 | 内容 |
|----|------|
| 任务 | liuri 三维分禁止静默占位 |
| 文件 | `liuri.py`、`dual_track.py` |
| 测试 | `tests/test_liuri_flow_score.py`、`tests/test_bazi_dual_track.py` |
| API | 无 schema 变更 → **无需** sync-frontend-types |
| 结果 | pytest +6；scorecard 仍 22/24（语料项未动） |

---

## 九、测试矩阵（后端回归必跑子集）

| 场景 | 命令 |
|------|------|
| 引擎全量 | `make test` |
| 八字黄金 | `pytest tests/test_golden_regression.py tests/test_golden.py -q` |
| 紫微黄金 | `pytest tests/test_ziwei_golden_regression.py -q` |
| 流日 | `pytest tests/test_liuri_flow_score.py -q` |
| 双轨 | `pytest tests/test_bazi_dual_track.py -q` |
| 格局 tier | `pytest tests/test_ziwei_pattern_false_positive.py -q` |
| OpenAPI | `pytest tests/test_openapi_sync.py -q` |
| Scorecard | `make scorecard` |

---

## 十、API / Schema 变更协议

1. 改 `app/schemas/*.py` → `make export-openapi` → diff `docs/openapi.json`
2. `make sync-frontend-types` → 提交 `frontend/src/api/schema.d.ts`
3. 新增字段：`missing_fields` / `provenance` / `layer` 优先于可选 null
4. Breaking change：保留 `*_method` 参数或 bump `engine_version`
5. 路由仅做参数透传，**禁止**在 `routers/` 写命理算法

---

## 十一、范围边界（更新）

### 仍不在主计划

- **整页回迁** 紫薇 legacy SPA（`BaziView`/`ZiweiView`/`AppShell`）— 破坏 Fusheng 信任层
- **引擎/路由** 从紫薇回迁 — c2 为权威后端
- **重社区/达人市场** — 测测模式，单独立项
- 原生客户端源码 — PWA/小程序壳即可

### 由「不做」调整为「PORT / P3」

| 项 | 紫薇资产 | 新结论 |
|----|----------|--------|
| 分享 UI | `ReportTopBar` + `export.ts` | **FE-PORT-01**（1 周，后端已就绪） |
| AI 工作区 | `AppRightPanel` + `LlmDraftsView` | **FE-PORT-02** + P2-03 |
| 扩展术数 | 4 个 legacy views | **FE-PORT-03** |
| 移动端 | 两库皆 Web | PWA；不做原生除非单独立项 |
| 付费 | 两库皆无 | **BE-P3-04** 新建 |
| 社区 | 两库皆无 | 轻分享优先，不做 Feed |

## 十二、关键文件索引

```
services/bazi_engine/          # 八字权威
services/ziwei_engine/         # 紫微权威
services/bazi_full_service.py  # full 编排
services/bazi_engine_service.py
services/ziwei_classic_refs.py # Z-07 语料
routers/bazi.py routers/ziwei.py
app/schemas/bazi.py app/schemas/ziwei.py
data/ground_truth_cases.json data/ziwei_ground_truth.json data/classics.json
scripts/audit_scorecard.py scripts/verify_classics_ctext.py
tests/test_golden_regression.py tests/test_ziwei_golden_regression.py
Makefile .github/workflows/ci.yml
```

---

## 十三、修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-07-12 | 初版：基线 3109 pytest、Scorecard 22/24、P0–P2 + 12 周计划 |
| v1.1 | 2026-07-12 | 执行 P0 全项 + BE-P1-01 |
| v1.2 | 2026-07-12 | P1 全项 + P2-02；结项 [BACKEND-FOLLOWUP-CLOSEOUT-2026-07-12](../reports/BACKEND-FOLLOWUP-CLOSEOUT-2026-07-12.md) |
| v1.3 | 2026-07-12 | 竞品对照 §四之二；P3 路线图 |
| v1.4 | 2026-07-12 | 姊妹库 `紫薇` 资产对照 §四之三；修正 v1.3 方案偏差；**FE-PORT-01~05** + BE-P3-08/09；执行顺序重排 |
