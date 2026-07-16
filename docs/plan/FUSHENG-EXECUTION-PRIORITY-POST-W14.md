# 浮生 · 顺序执行优先级（W14 后 · 免对话开发清单）

| 字段 | 内容 |
|------|------|
| **版本** | post-w14-2.15 |
| **日期** | 2026-07-16 |
| **定位** | **T070 完成后**按编号依次做；无需每次对话 |
| **当前优先级** | ▶ **Phase F GTM** — T086–T100 ☑ → **下一项 T101** |
| **前置** | [**EXECUTION-PRIORITY**](FUSHENG-EXECUTION-PRIORITY.md) **T001–T070 全部 ☑** |
| **上级** | [INTEGRATED §十二](FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md#十二增长期与平台演进w15) · [BOOK-GTM](FUSHENG-BOOK-GTM-DEV-PLAN-2026-07-12.md) · [PLATFORM-EVOLUTION](PLATFORM-EVOLUTION-ROADMAP.md) |
| **入口** | [DEVELOPMENT.md](../DEVELOPMENT.md) · [PIPELINE](../FUSHENG-DEV-PIPELINE.md) |

---

## 开工状态

```text
前置  T070 ☑（W14 · W102-22 closeout）
门禁  T071 / T071-BE / T071-FE ☑（2026-07-14）
BE+FE T072–T084 ☑
U5    T085 ☑（2026-07-14）
GTM   T086–T100 ☑ → 下一项 **T101**
五书  M0–M3 机读 ☑ · E-04 可选
```

| 里程碑 | 做完到 | 含义 |
|--------|--------|------|
| **U5** | T085 | 六卷 API 权威；废弃 Adapter |
| **GTM-Ready** | T105 | 可试投抖音（归因+权益+落地页） |
| **Ext-Ready** | T115 | Extension 三卡（合盘/择日/相似） |
| **E1-Gate** | T135 | 平台 Registry 双轨一致 |
| **Post-Launch** | T140 | 上线评估签字 |

---

## 零、怎么用本文

1. **从 T071 做到 T140**，严格按编号；标 `∥` 可与主轨并行。
2. 每完成一条：`☐` → `☑`，提交信息写 `T0XX: 简述`。
3. **禁止跳号**：尤其 **T071 门禁**、**T085 前不得全量 GTM**、**T126 前不得迁 Registry 业务代码**。
4. Cursor 一句话：

   ```text
   执行 docs/plan/FUSHENG-EXECUTION-PRIORITY-POST-W14.md 的 T088，按该条验收命令收尾。
   ```

5. 细节查上级文档，勿在对话里重贴全套方案。

---

## 一、优先级总览

```text
P8   门禁      T071
P9   权威化    T072–T085     ← W15–W16 · U5
P10  GTM       T086–T105     ← 增长（可砍支付留试投）
P11  Extension T106–T115     ← 合盘/择日/相似
P12  内容引擎  T116–T125 ∥  ← 校勘/运限/童限
P13  平台 E0–E1 T126–T135   ← W17+ 架构
P14  上线评估  T136–T140
```

**与 W 周对照：**

| 周次 | 本清单块 | 用户里程碑 |
|------|----------|------------|
| W15 | T072–T080 | life/volumes 开发 |
| W16 | T081–T085 | **U5** 权威切换 |
| W17–W20 | T086–T105 | GTM 试投预备 |
| W19–W22 | T106–T115 | Extension |
| 持续 | T116–T125 | 信任加深 |
| W23–W28 | T126–T135 | 平台 E0–E1 |

---

## 二、顺序任务表

> **角色**：`FE` · `BE` · `DS` · `ALL` · `∥` 可并行

### 块 I · 前置门禁（必做，Day 0）

| ☐ | ID | 角色 | 任务 | 验收 |
|---|-----|------|------|------|
| ☑ | **T071** | ALL | 确认 [EXECUTION-PRIORITY](FUSHENG-EXECUTION-PRIORITY.md) **T063–T070 全 ☑**；§六 W14 终验 11+7 项已勾 | [T071 门禁报告](../reports/T071-phase-e-gate-2026-07-14.md) |
| ☑ | **T071-BE** | BE | `make scorecard` 24/24 · explain/schema · `test_zw18_trust` 绿 | 2026-07-14 复验 |
| ☑ | **T071-FE** | FE | `npm run test:e2e -- fusheng-report` 绿 · Report 无「四维分析」 | 11/11 passed |

**T071 已过 → 进入 T072+。**

---

### 块 J · P3 权威化 W15–W16（U5）

| ☐ | ID | 角色 | 任务 | 主要文件 | 验收 |
|---|-----|------|------|----------|------|
| ☑ | **T072** | BE | **P3-01** `GET /api/v1/life/volumes/{case_id}` 返回 life-volume@1.0 | `routers/life.py` · `services/life_volume_service.py` | schema 契约绿 |
| ☑ | **T073** | BE | colophon 后端聚合（iztro/wenmo/missing/disclaimer） | `_build_colophon` | 响应含 colophon |
| ☑ | **T074** | BE | explain 结果写入 volume sections（非 FE 拼 cite） | `life_volume_service` | 卷一/二/四/五 explain 来自 BE |
| ☑ | **T075** | BE | **P3-03** liunian Redis worker 生产配置 | `liunian_queue.py` · `run_liunian_worker.py` · compose profile | 可观测 enqueued/done/poison · 无 Redis 回退 asyncio |
| ☑ | **T076** | BE | **P3-02** `GET /api/v1/life/snippets/{case_id}`（hooks 3–5 条） | `life_snippets_service` · BOOK-GTM §5.3 | schema `life-snippets@0.1` · 单测绿 |
| ☑ | **T077** | BE | **P3-04** archive-bundle 可选 name/zeri 指针 | `fusheng_archive.py` | `include_*_pointer` · OpenAPI · 单测 |
| ☑ | **T078** | ALL | OpenAPI export + `npm run gen:types`；life-volume 契约测试双端 | [T078 报告](../reports/T078-openapi-types-2026-07-14.md) · CI drift | PR diff 阻断 |
| ☑ | **T079** | FE | `api/life.ts` 真 API；flag=`VITE_USE_LIFE_VOLUMES_API` / localStorage `fusheng-use-life-volumes-api=1` | `api/life.ts` · `ReportView` | flag 开且 remote 成功 → 跳过 explain/batch |
| ☑ | **T080** | FE | Report 主路径优先 `GET life/volumes`；权威态无 explain/batch 瀑布 | `ReportView.vue` · E2E | `fusheng-life-volumes` 2/2 |
| ☑ | **T081** | FE | `buildLifeVolumes.ts` 标 **deprecated**；remote 成功时生产路径不调用 | 注释 + `shouldBuildLifeVolumesAdapter` + FE-DEV | Vitest + Report 门控 |
| ☑ | **T082** | FE | remote volumes 成功则跳过 explain/batch；卷内已有 explain 段时隐藏对应 AnalysisPanel | `ReportView.vue` | 无双重 cite · waterfall archive+volumes |
| ☑ | **T083** | ALL | E2E：volumes API 路径六卷+跋断言 | `e2e/fusheng-life-volumes.spec.ts` | 3/3 + report 11/11 |
| ☑ | **T084** | BE | Compute **legacy 瘦化收尾**：`interpretation_text` 默认 off；文档迁移说明 | [T084 报告](../reports/T084-legacy-slim-2026-07-14.md) | Q4 闭环 |
| ☑ | **T085** | ALL | **U5 签字**：15 分钟建档→报告；数据来自 **life/volumes**；跋权威 | [T085 门禁](../reports/T085-u5-gate-2026-07-14.md) | **P3 Gate** |

**J-验收命令：**

```powershell
pytest tests/test_life_volume*.py tests/test_explain_*.py
cd frontend && npm run test:e2e -- fusheng-report
make scorecard
```

---

### 块 K · GTM 增长 W17–W20（BOOK-GTM）

> **可砍序**：无支付先做的试投 = T086–T092 + T096–T098；T093–T095 后置。

| ☐ | ID | 角色 | 任务 | 主要文件 | 验收 |
|---|-----|------|------|----------|------|
| ☑ | **T086** | BE | **BE-GTM-05** entitlement 模型：`free` / `volume_pass` / `full_book` | [T086 报告](../reports/T086-entitlement-2026-07-14.md) · `quota_service` · schemas | `enforce_entitlement` · auth/me · 单测 |
| ☑ | **T087** | BE | 卷目 `locked` 规则（Q2：卷0–1 免费，2–4 pass，5–6 pro） | [T087 报告](../reports/T087-volume-locks-2026-07-14.md) · `life_volume_service` | free/pass/full_book fixture |
| ☑ | **T088** | BE | **BE-GTM-02** 注册/案例 `utm_source` `utm_campaign` `content_id` | [T088 报告](../reports/T088-utm-attribution-2026-07-14.md) · Case/User · auth | 抖音视频 ID 可存 |
| ☑ | **T089** | BE | **BE-GTM-01** `POST /api/v1/analytics/events` 批量事件 | [T089 报告](../reports/T089-analytics-events-2026-07-14.md) · `analytics_events` | 卷目阅读/术语点击 · PII scrub |
| ☑ | **T090** | FE | **FE-GTM-06** `utils/analytics.ts` 封装；**禁**姓名/生日进 payload | [T090 报告](../reports/T090-fe-analytics-2026-07-14.md) | Vitest 隐私评审 |
| ☑ | **T091** | FE | **FE-GTM-01** `LandingVolume.vue` 卷首摘要 + CTA 建档 | [T091 报告](../reports/T091-landing-volume-2026-07-14.md) · `/landing` | 375px 无横滚 E2E |
| ☑ | **T092** | FE | **FE-GTM-03** 卷锁定态 UI + 付费墙文案（可 mock 支付） | [T092 报告](../reports/T092-volume-paywall-2026-07-14.md) · VolumePaywall | locked 卷显示锁+说明 |
| ☑ | **T093** | BE | **BE-GTM-06** 支付 webhook → 写 entitlement | [T093 报告](../reports/T093-payment-webhook-2026-07-14.md) · payment.py | 沙箱回调通 |
| ☑ | **T094** | FE | 支付成功刷新 entitlement；解锁卷三~五 | [T094 报告](../reports/T094-payment-callback-2026-07-14.md) · PaymentCallback | 卷目可展开 |
| ☑ | **T095** | BE | **BE-GTM-07** H5 短 token 读卷一摘要（可选） | [T095 报告](../reports/T095-h5-preview-token-2026-07-14.md) · `auth` · `life/preview` | 落地页免登录试读 |
| ☑ | **T096** | FE | **FE-GTM-04** 钩子句复制（接 T076 snippets） | [T096 报告](../reports/T096-snippet-copy-2026-07-14.md) · SnippetHooksPanel | 一键复制拍视频 |
| ☑ | **T097** | BE | **BE-GTM-11** `export/card?layout=douyin` 9:16 | [T097 报告](../reports/T097-douyin-share-card-2026-07-14.md) · `pdf_exporter` | PNG 输出 |
| ☑ | **T098** | FE | **FE-GTM-07** 竖版分享预览 + 导出 | [T098 报告](../reports/T098-douyin-share-preview-2026-07-14.md) · DouyinShareCard | 纸纹+卷名+事实句 |
| ☑ | **T099** | BE | **BE-GTM-08** 创作者统计 API（topic→注册 cohort） | [T099 报告](../reports/T099-creator-stats-2026-07-14.md) · `creator_stats` | 仅管理员 RBAC |
| ☑ | **T100** | FE | **FE-GTM-05** 创作者 Dashboard（仅你） | [T100 报告](../reports/T100-creator-dashboard-2026-07-16.md) · `/creator` | 转化表可读 |
| ☐ | **T101** | BE | **BE-GTM-10** 私域留资 stub（可选手机号） | `routers/leads.py` | CSV 导出 |
| ☐ | **T102** | ALL | GTM 合规：落地页+报告 disclaimer 双显；禁「改命」文案扫描 | 文案 lint | 无违规词 |
| ☐ | **T103** | ALL | 试投演练：模拟 utm 注册→读卷一二→锁卷三 | 手工 | 漏斗可走通 |
| ☐ | **T104** | DS | 抖音素材模板 3 套（卷一/运之波/校勘）文档化 | `docs/guides/` | 可拍 |
| ☐ | **T105** | ALL | **GTM-Ready 签字**；是否开启真实投放 | — | 产品决策 |

**K-禁止：** 达人撮合 · 直播占卜话术 · LLM 替代排盘（BOOK-GTM §2.1）

---

### 块 L · Extension 扩展 W19–W22

| ☐ | ID | 角色 | 任务 | 主要文件 | 验收 |
|---|-----|------|------|----------|------|
| ☐ | **T106** | FE | ExtensionHub 三卡：**合盘** · **择日** · **相似盘** | `ExtensionHubView.vue` | 主路径可达 |
| ☐ | **T107** | FE | 合盘页接 `POST /compat/full`；叙事标「经验推断」 | `ZiweiCompatView.vue` | 无假典籍 |
| ☐ | **T108** | FE | 择日页接 `GET /zeri/recommend`；与卷三运限文案一致 | `ZeriView.vue` | 用途列表可见 |
| ☐ | **T109** | FE | 相似盘结果表 + 跳转对比 | `SimilarityView.vue` | 空态友好 |
| ☐ | **T110** | FE | 首页/报告 **Extension 入口卡**（不打断六卷阅读） | `NewHomeView` | 一屏仍一锚 |
| ☐ | **T111** | BE | compat/zeri/similarity OpenAPI 进 CI；quota 限制 | routers | 滥用防护 |
| ☐ | **T112** | ALL | E2E：Extension 三路径 smoke | `e2e/` | 最小集绿 |
| ☐ | **T113** | BE | 合盘结果写入可选 `life/volumes` 附录卷（非主卷） | 设计决议 | 不破坏六卷 IA |
| ☐ | **T114** | DS | Extension 页视觉对齐 T014 targets（纸墨，无新 hex） | — | R-01~05 复查 |
| ☐ | **T115** | ALL | **Ext-Ready 签字** | — | Extension 可对外 |

**L-明确不做（本阶段）：** 六爻大全科 · 姓名商业化主流程 · 术数超市  
**L′ 修订（2026-07-16）：** 奇门/河洛可作为大运卡「互证参考轨」分期研发（见 `docs/superpowers/specs/2026-07-16-dayun-multi-track-roadmap.md`），**仍不做**奇门全科产品化主流程；无引擎前仅 `not_implemented` 占位。

---

### 块 M · 内容与引擎加深（并行轨 ∥）

可与 J/K/L 并行，**不得**阻塞 T085。

| ☐ | ID | 角色 | 任务 | 主要文件 | 验收 |
|---|-----|------|------|----------|------|
| ☐ | **T116** ∥ | BE | **SRC-08** `verify_ziwei_horoscope_iztro.mjs` | `scripts/` | 抽样 3 盘 diff 报告 |
| ☐ | **T117** ∥ | BE | **SRC-09** 文墨 WM01 大限/流年表 horoscope diff | 脚本 + 文档 | advisory only |
| ☐ | **T118** ∥ | BE | **P2-04** 宫位宫干/十神补齐 | `ziwei_engine` | API 非空 |
| ☐ | **T119** ∥ | BE | 童限 Z-11 REGISTRY 与产品口径文档 | `ENGINE-METHOD-REGISTRY` | 与 Timeline 一致 |
| ☐ | **T120** ∥ | 校勘 | classics **verified 40%→50%**（每周 8h） | `data/classics.json` | Scorecard 无跌 |
| ☐ | **T121** ∥ | BE | `content_policy` 生产日志 + 拒 cite 指标 | monitoring | 可告警 |
| ☐ | **T122** ∥ | BE | quota Redis 生产 + 公测限额文档 | `quota_service` | 压测 advisory |
| ☐ | **T123** ∥ | BE | PDF 全书六卷 + 校勘附录 CI 快照 | `pdf_exporter` | U4 可复现 |
| ☐ | **T124** ∥ | ALL | 生产部署清单：CSP · backup · env · health | `docs/guides/` | 运维可执行 |
| ☐ | **T125** ∥ | ALL | 引擎边角复盘：ZW03 双轨页 · youbi 脚注 · ZIP 外格 UI | 跋/卷一 | 用户可理解 |

---

### 块 N · 平台演进 E0–E1 W23–W28

> **前置：** T085 ☑。本块 **不改** Scorecard 行为，E1 需双轨测试。

| ☐ | ID | 角色 | 任务 | 主要文件 | 验收 |
|---|-----|------|------|----------|------|
| ☐ | **T126** | BE | **E0-01** `MetaphysicsEngine` Protocol | `app/platform/engine_protocol.py` | 文档评审 |
| ☐ | **T127** | ALL | **E0-02** 架构文档 v2 + **E0-03** `engines.manifest.json` | `docs/design/02-architecture.md` | bazi/ziwei 元数据 |
| ☐ | **T128** | BE | **E0-04** `services/application/` 占位；snapshot 迁入计划 | 目录 | 零行为变更 |
| ☐ | **T129** | BE | **E1-01** `EngineRegistry` 注册 bazi/ziwei | `engine_registry.py` | 单元测试 |
| ☐ | **T130** | BE | **E1-02** `ziwei/full` 经 registry（双轨开关） | `routers/ziwei.py` | 输出与直连一致 |
| ☐ | **T131** | BE | **E1-03** `KnowledgeStore` 读 classics/glossary/GT/rules | `knowledge_store.py` | explain 改读 store |
| ☐ | **T132** | BE | **E1-04** content_policy 迁 KnowledgeStore | `content_policy.py` | 测试绿 |
| ☐ | **T133** | BE | **E1-05** `GET /api/v1/engines` capabilities | router | OpenAPI |
| ☐ | **T134** | BE | **E1-06** Benchmark 基线 GT01 full + explain/batch | pytest-benchmark | 报告归档 |
| ☐ | **T135** | ALL | **E1-Gate**：registry 与直连 **2 周双轨** 一致；Scorecard 24/24 | — | 平台签字 |

**N-明确不做：** Workflow DAG · Mutation Test · 奇门全科引擎注册进主菜单（参考轨分期见多轨规划，不视为本阶段 N 阻断）

---

### 块 O · 上线评估与后续分叉（T136–T140）

| ☐ | ID | 角色 | 任务 | 验收 |
|---|-----|------|------|------|
| ☐ | **T136** | ALL | 全站回归：`make quality-gate-frontend` + `make quality-gate-backend` | 绿 |
| ☐ | **T137** | ALL | 安全扫：依赖 audit · RBAC 复核 · 埋点无 PII | 清单 ☑ |
| ☐ | **T138** | 产品 | 定价与权益表终稿（对齐 T086 档位） | 文档 |
| ☐ | **T139** | ALL | **Post-Launch 演练**：新用户 utm→建档→读卷→付费（或试投） | 录屏 |
| ☐ | **T140** | ALL | **阶段收官签字**；分叉决策：加大 GTM / 先做 E2 / 校勘优先 | 会议纪要 |

**T140 后可选路线（不在本清单编号内）：**

| 路线 | 文档 |
|------|------|
| E2 Pipeline + liuyao 插件 | [PLATFORM §E2](PLATFORM-EVOLUTION-ROADMAP.md#e2--pipeline--rule-扩面--extensionw25w32约-68-周) |
| 六爻占事 Extension | INTEGRATED §12.3 |
| classics 60% + CMS 校勘 | PLATFORM E3-04 |
| App 双端 / 出海 | 另开计划（本清单不做） |

---

## 三、禁止跳步

| 禁止 | 原因 |
|------|------|
| 未 T071 就 T072 | 打磨期未真正收官 |
| 未 T085 就 T093 真实收费 | 报告仍可能走 Adapter |
| 未 T085 就 T126 迁 Registry 业务 | 双真源爆炸 |
| GTM 加达人撮合/直播占卜 | BOOK-GTM 红线 |
| Extension 升主 IA（六爻当第二主页） | 赛道偏离 |
| narrative/文墨全文标典籍 | 内容宪法 |
| T140 前全量 E2 Pipeline | 过度工程 |

---

## 四、与 T001–T070 的衔接

| T070 交付 | 本清单承接 |
|-----------|------------|
| 六卷+跋 FE Adapter | T072–T085 → **life/volumes 权威** |
| explain/batch | T074 并入 volumes 生成 |
| MVP-20 verified | T120 继续扩面 |
| 跋 iztro/wenmo UI | T073 后端权威 colophon |
| 打磨期不做 GTM | **T086–T105** 专块 |
| T070-BE 草案 | T075–T076 生产化 |

**开新对话时只需说：**

```text
前置：FUSHENG-EXECUTION-PRIORITY T070 已完成。
执行 FUSHENG-EXECUTION-PRIORITY-POST-W14.md 的 T0XX。
```

---

## 五、终验勾选（T136 对照）

```markdown
### P3 权威（U5）
- [x] GET life/volumes 为报告唯一数据源
- [x] buildLifeVolumes 已 deprecated
- [x] colophon 含 wenmo/iztro/disclaimer（BE 聚合）
- [x] waterfall ≤2–4

### GTM（若做 T086–T105）
- [x] entitlement 中间件生效（T086 · `enforce_entitlement`）
- [x] utm 归因入库（T088）
- [x] analytics 无 PII（T089 BE scrub；T090 FE 封装）
- [x] 落地页（T091 LandingVolume · 375 无横滚）
- [x] 锁卷 UI（T092 VolumePaywall · mock 解锁）
- [ ] disclaimer 合规

### Extension（若做 T106–T115）
- [ ] 合盘/择日/相似 三卡可用
- [ ] 不打断六卷主阅读

### 平台（若做 T126–T135）
- [ ] Registry 双轨与直连一致
- [ ] GET /engines 可查
```

---

## 六、文档索引

| 任务块 | 细节 |
|--------|------|
| T071–T085 | INTEGRATED §4.5 P3 · FE-BE Q1/Q3/Q9 |
| T086–T105 | BOOK-GTM §四–§六 · BE-GTM-01~12 |
| T106–T115 | INTEGRATED §12.3 · MARKET-ENTRY |
| T116–T125 | CONTENT-SOURCES §8.4 · BACKEND-MASTER P2 |
| T126–T135 | PLATFORM-EVOLUTION E0–E1 |
| 战略边界 | MARKET-ENTRY · PRODUCT.md |

---

## 七、修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| post-w14-2.15 | 2026-07-16 | **T100 ☑** · 创作者 Dashboard `/creator` · 下一项 T101 |
| post-w14-2.14 | 2026-07-16 | **五书可验 M1** · T100 暂停至 M2 · E-01/E-03 机读轨 ☑ |
| post-w14-2.13 | 2026-07-14 | **T099 ☑** · 创作者统计 API · 下一项 T100 |
| post-w14-2.12 | 2026-07-14 | **T098 ☑** · 竖版分享预览+导出 FE · 下一项 T099 |
| post-w14-2.11 | 2026-07-14 | **T097 ☑** · douyin 9:16 分享卡 PNG · 下一项 T098 |
| post-w14-2.10 | 2026-07-14 | **T096 ☑** · 钩子句一键复制 · 下一项 T097 |
| post-w14-2.9 | 2026-07-14 | **T095 ☑** · H5 短 token 卷一试读 · 下一项 T096 |
| post-w14-2.8 | 2026-07-14 | **T094 ☑** · 支付回调刷新 entitlement · 下一项 T095 |
| post-w14-2.7 | 2026-07-14 | **T093 ☑** · 支付 webhook 写 entitlement · 下一项 T094 FE |
| post-w14-2.6 | 2026-07-14 | **T092 ☑** · 卷锁定态/付费墙 mock · 下一项 T093 支付 |
| post-w14-2.5 | 2026-07-14 | **T091 ☑** · LandingVolume 抖音落地 · 下一项 T092 锁卷 UI |
| post-w14-2.4 | 2026-07-14 | **T090 ☑** · FE analytics.ts 隐私守卫 · 下一项 T091 LandingVolume |
| post-w14-2.3 | 2026-07-14 | **T089 ☑** · analytics/events 批量埋点 · 下一项 T090 FE |
| post-w14-2.2 | 2026-07-14 | **T088 ☑** · utm 归因注册/建档 · 下一项 T089 analytics |
| post-w14-2.1 | 2026-07-14 | **T087 ☑** · volumes locked Q2 · 下一项 T088 utm |
| post-w14-2.0 | 2026-07-14 | **T086 ☑** · entitlement free/pass/full_book · 下一项 T087 locked |
| post-w14-1.9 | 2026-07-14 | **T085 U5 ☑** · P3 Gate 通过 · 下一项 T086 GTM |
| post-w14-1.8 | 2026-07-14 | **T078 ☑** · OpenAPI/types 双端契约 · 下一项 T085 U5 |
| post-w14-1.7 | 2026-07-14 | **T077 ☑** · archive name/zeri 指针 · 下一项 T078/T085 |
| post-w14-1.6 | 2026-07-14 | **T076 ☑** · life/snippets §5.3 · 下一项 T077/T085 |
| post-w14-1.5 | 2026-07-14 | **T075 · T084 ☑** · liunian Redis 队列/worker · Q4 legacy 收尾 · 下一项 T076/T085 |
| post-w14-1.4 | 2026-07-14 | **T082–T083 ☑** · 无双重 cite · volumes E2E 六卷+跋 · 下一项 T075/T084 |
| post-w14-1.3 | 2026-07-14 | **T081 ☑** · buildLifeVolumes deprecated · remote 成功跳过 Adapter · 下一项 T075/T082 |
| post-w14-1.2 | 2026-07-14 | **T079–T080 ☑** · volumes flag + 跳过 explain/batch · 下一项 T075/T081 |
| post-w14-1.1 | 2026-07-14 | **T071 ☑** · T072–T074 机读落地 · 下一项 T079 |
| post-w14-1.0 | 2026-07-12 | 初版：T071–T140；P3·GTM·Extension·平台·上线评估 |
