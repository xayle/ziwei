# 浮生 · 东方命理计算平台演进路线图

| 字段 | 内容 |
|------|------|
| **版本** | platform-1.0 |
| **日期** | 2026-07-12 |
| **定位** | **打磨期（W1–W16）之后** 的平台化演进；**不替代** [INTEGRATED-DEV-PLAN](./FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md) |
| **原则来源** | GPT 平台化评审（已过滤过度工程项）+ 代码库现状审计 |
| **前置完成** | INTEGRATED 打磨期收官（六卷、explain/batch、life/volumes、MVP-20/35% verified） |

---

## 〇、一句话

> **不推翻 Scorecard 引擎与 Router 结构，在 ChartSnapshot / Explain / Content 之上，用插件化 Engine、薄 Knowledge、显式 Pipeline 把「命理后端」演进为「东方命理计算平台」。**

---

## 一、与打磨期的关系（必读）

```text
W1–W16   INTEGRATED 打磨期（产品 + 编排 + 契约）  ← 唯一当前执行火车表
W17+     本文 E0–E3 平台演进                      ← 打磨期收官后才启动
```

| 打磨期已在做的「平台化 1.0」 | 本文后续演进 |
|------------------------------|--------------|
| ChartSnapshot（只算一次） | → Application 层正式命名 + PipelineStep |
| Explain Service | → Workflow 显式步骤（非 DAG 引擎） |
| content_policy + classics@ | → KnowledgeStore 接口 |
| life-volume.schema.json | → Capability 只读 API |
| METHOD-REGISTRY | → Engine Registry 运行时（bazi/ziwei 先行） |
| rule_matches + bazi_rules.json | → Rule JSON 扩面（不替代 geju 核心） |

**打磨期严禁：** 全量 Engine Registry 迁移 · Workflow DAG · Knowledge ORM · Evidence Graph DB · Mutation Test

---

## 二、现状基线（2026-07-12 代码事实）

| 已有 | 路径/说明 |
|------|-----------|
| 八字引擎 | `services/bazi_engine/`（30+ 模块） |
| 紫微引擎 | `services/ziwei_engine/` |
| 六爻/姓名/风水引擎 | `liuyao_engine/`、`name_engine/`、`fengshui_engine/` |
| 编排（过重） | `bazi_full_service.py`、`bazi_engine_service.py` |
| 规则 JSON | `bazi_rule_engine.py` + `data/bazi_rules.json` |
| 口径文档注册表 | `docs/design/bazi|ziwei/ENGINE-METHOD-REGISTRY.md` |
| 质量 | Scorecard 24/24 · GT50/ZW20/DV10 · pytest 3000+ |
| 工具插件设计稿 | `docs/design/02-architecture.md`（**未落地**） |
| 统一 Engine Registry | **无** |
| 通用 Workflow 框架 | **无** |

**诊断：** Engine 层成熟；**Application 编排层**和**知识/content 统一访问层**是主要演进面。

---

## 三、目标架构（演进终态）

```
┌─────────────────────────────────────────────────────────────┐
│ API Layer          routers/  （薄：校验、鉴权、HTTP）          │
├─────────────────────────────────────────────────────────────┤
│ Application        snapshot · explain · life_volumes · report │
│                    PipelineRunner（显式步骤，非 DAG 产品）      │
├─────────────────────────────────────────────────────────────┤
│ Domain             ChartSnapshot DTO · LifeVolume · Explain   │
├─────────────────────────────────────────────────────────────┤
│ Engine Platform    EngineRegistry → MetaphysicsEngine 插件    │
│                    bazi · ziwei · liuyao · …                  │
├─────────────────────────────────────────────────────────────┤
│ Knowledge          KnowledgeStore（classics/glossary/GT/rules）│
├─────────────────────────────────────────────────────────────┤
│ Infrastructure     db · redis · cache · metrics               │
└─────────────────────────────────────────────────────────────┘
```

**铁律（与 GPT 一致，与 INTEGRATED 一致）：**

- Engine **禁止** import HTTP、SQLModel、Redis、前端类型  
- 新增术数优先 **注册插件**，避免改 `bazi_full_service` 上帝文件  
- 黄金盘 / Scorecard **不回归**

---

## 四、八项演进对照（采纳 / 延后 / 拒绝）

| # | GPT 方向 | 裁决 | 阶段 |
|---|----------|------|------|
| 1 | Engine Platform + Registry | **采纳**（先 bazi/ziwei） | E1 |
| 2 | Workflow Engine | **采纳薄版** PipelineStep | E2 |
| 3 | Knowledge Layer | **采纳** KnowledgeStore 薄封装 | E1 |
| 4 | Capability Registry | **采纳** 只读 `GET /engines` | E1–E2 |
| 5 | Rule Engine | **部分采纳** 扩 JSON；**不**重写 geju | E2 |
| 6 | Evidence Graph | **延后** 列表 evidence 先达标 | E3 |
| 7 | Domain 分层 | **采纳** 命名与目录收敛 | E0–E1 |
| 8 | Benchmark + Mutation | **Benchmark 采纳**；**Mutation 拒绝** | E1 |

---

## 五、阶段路线图 E0–E3

### E0 · 协议与分层命名（W17–W18，约 1–2 周）

**目标：** 只写协议与目录约定，**几乎不迁业务代码**。

| ID | 任务 | 产出 |
|----|------|------|
| E0-01 | `MetaphysicsEngine` Protocol | `app/platform/engine_protocol.py` |
| E0-02 | 分层文档 | 更新 `docs/design/02-architecture.md` v2 |
| E0-03 | `engines.manifest.json` | bazi/ziwei 元数据（version、capabilities 草案） |
| E0-04 | Application 目录 | `services/application/` 占位；snapshot 迁入计划 |

**Protocol 草案：**

```python
class MetaphysicsEngine(Protocol):
    engine_id: str
    rule_version: str

    def compute(self, request: BaseModel) -> BaseModel: ...
    def validate(self, request: BaseModel) -> list[str]: ...  # warnings
    def metadata(self) -> EngineMetadata: ...
```

**Gate：** 文档评审；**零** Scorecard 回归要求（无行为变更）

---

### E1 · Registry + Knowledge + Capability（W19–W24，约 4–6 周）

| ID | 任务 | 产出 |
|----|------|------|
| E1-01 | `EngineRegistry` | `app/platform/engine_registry.py`；注册 bazi、ziwei |
| E1-02 | Router 薄化试点 | `ziwei/full` 经 registry 调用（bazi 第二） |
| E1-03 | `KnowledgeStore` | `services/knowledge_store.py` 统一读 classics/glossary/GT/rules |
| E1-04 | `content_policy` 迁入 | 引用 KnowledgeStore，不直读 JSON 散落 |
| E1-05 | `GET /api/v1/engines` | 返回 id、version、capabilities[] |
| E1-06 | Benchmark 基线 | `pytest-benchmark` GT01 full + explain/batch |

**Capability 枚举（初版）：**

```json
["compute_full", "verify", "liunian", "liuyue", "liuri", "structured_export", "iztro_crosscheck", "explain"]
```

**Gate：** Scorecard 24/24；GT01/GT02 registry 路径与直连路径 **输出一致**（双轨测试 2 周）

---

### E2 · Pipeline + Rule 扩面 + Extension（W25–W32，约 6–8 周）

| ID | 任务 | 产出 |
|----|------|------|
| E2-01 | `PipelineRunner` | 显式步骤：snapshot → explain → export（可配置列表） |
| E2-02 | 拆掉 enrich 硬编码链 | `_enrich_v2_analysis` 拆为命名 step；失败进 missing_fields |
| E2-03 | 扩 `bazi_rules.json` | 产品可配规则；**不**动 geju/yongshen 核心 if 链 |
| E2-04 | liuyao 注册试点 | 第三枚引擎插件；ExtensionHub 读 capability |
| E2-05 | PDF/通知挂 Pipeline | 新能力 = 新 Step，不改 router 主链 |
| E2-06 | Locust 进 advisory CI | batch explain p95 |

**明确不做：**

- 自研 DAG / Temporal  
- 奇门引擎一并注册（除非有产品需求）  
- Rule JSON 替代 `geju.py`

**Gate：** Pipeline 与旧 orchestrator 黄金盘一致；Locust 报告进 `docs/reports/`

---

### E3 · Evidence Graph + 新术数（W33+，持续）

| ID | 任务 | 说明 |
|----|------|------|
| E3-01 | Evidence 专家 API | `GET /evidence/trace?chart_hash=&field=` 列表级追溯 |
| E3-02 | 可选 Graph 存储 | 仅审计/校勘模式；**非**主站热路径 |
| E3-03 | 奇门 / 更多引擎 | 按产品排期注册 |
| E3-04 | CMS 校勘 | classics verified → 60%+；Knowledge 写路径 |

**Gate：** 主站响应仍 ≤ INTEGRATED SLO；Graph 不拖慢 full/explain

---

## 六、领域分层迁移计划

| 当前 | 目标 | 阶段 |
|------|------|------|
| `routers/bazi.py` | API only | 保持 |
| `bazi_full_service.py` | `services/application/bazi_orchestrator.py` | E1–E2 |
| `chart_snapshot_service.py` | `application/snapshot.py` | E0 已建（INTEGRATED P0） |
| `explain_service.py` | `application/explain.py` | E1 |
| `bazi_engine/*` | `engines/bazi/`（物理迁移可选） | E2+ |
| `data/classics.json` | KnowledgeStore 后端 | E1 |
| `bazi_rule_engine.py` | `knowledge/rules.py` | E2 |

**物理迁目录可选：** E2 前允许 **逻辑分层**（import 路径不变），避免大爆炸 PR。

---

## 七、质量策略

| 类型 | 工具 | 阶段 | 说明 |
|------|------|------|------|
| 黄金回归 | GT/ZW/DV + explain fixtures | 持续 | **主门禁** |
| Scorecard | `audit_scorecard.py` | 持续 | 24/24 |
| 契约 | life-volume schema + OpenAPI | 持续 | |
| Benchmark | pytest-benchmark | E1 | GT01 p95 基线 |
| 压测 | Locust advisory | E2 | 公测前 |
| Mutation | — | **不做** | 命理输出不适配 |

---

## 八、与 GPT 八条原则的符合性自检

| GPT 原则 | 本文 |
|----------|------|
| 不推翻现有架构 | ✅ E0 仅协议；E1 双轨验证 |
| Router / Schema / Engine 基本结构保持 | ✅ |
| 优先抽象，不重复开发 | ✅ Registry 包装现有 engine |
| 插件化、低耦合 | ✅ E1 Registry + E2 Pipeline |
| Engine 纯算法 | ✅ Protocol 禁止 IO |

---

## 九、文档与索引

| 文档 | 关系 |
|------|------|
| [FUSHENG-INTEGRATED-DEV-PLAN](./FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md) | W1–W16 主执行 |
| [BACKEND-MASTER-PLAN](./BACKEND-MASTER-PLAN-2026-07-12.md) | 编排/Explain/Content 细节 |
| [02-architecture](../design/02-architecture.md) | E0 更新 Tool Plugin 为 Platform |
| [METHOD-REGISTRY](../design/bazi/ENGINE-METHOD-REGISTRY.md) | 口径；非运行时 Registry |

---

## 十、修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| platform-1.0 | 2026-07-12 | 初版 E0–E3；过滤 GPT 过度项；挂钩 INTEGRATED W17+ |
