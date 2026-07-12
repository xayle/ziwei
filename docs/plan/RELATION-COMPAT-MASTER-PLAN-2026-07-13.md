# 浮生 · 个人档案与关系合盘统一开发文档

| 字段 | 内容 |
|------|------|
| **版本** | relation-master-1.0 |
| **日期** | 2026-07-13 |
| **状态** | **Implemented · relation-master-1.2** |
| **上位** | [`PRODUCT.md`](../PRODUCT.md) · [`FUSHENG-INTEGRATED-DEV-PLAN`](./FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md) · [`BACKEND-MASTER-PLAN`](./BACKEND-MASTER-PLAN-2026-07-12.md) |
| **契约** | [`relation-compat.schema.json`](../contracts/relation-compat.schema.json) · [`relation-type-registry.json`](../contracts/relation-type-registry.json) |
| **触发** | 个人盘 / 情侣 / 友人 / 亲子 / 同事 / 合伙 / 上下级 输出分散、模板错用、内容不丰满 |

> **一句话**：**个人单盘只算一次（ChartSnapshot）；关系合盘按 `relation_type` 换尺子，统一 `POST /relation/full`，首屏卡片 + 分维得分 + 共运时间轴，长文默认折叠。**

---

## 〇、问题陈述（为何需要本文）

### 0.1 现状：入口多、尺子乱、内容薄

| 场景 | 现有入口 | 问题 |
|------|----------|------|
| **个人档案** | `POST /bazi/full` · `POST /ziwei/full` · `GET /life/volumes` | 域分析长文泛滥；与合盘 **字段重复**；缺「一人一句摘要」 |
| **情侣合盘** | `POST /compat/full` · `POST /ziwei/compatibility` · `POST /bazi/compatibility` | **三套 API**；`/compat/full` 紫微 import 曾失败；**固定夫妻宫维** |
| **友人/亲子/同事** | `POST /relations/compat`（需 case_id + 登录） | 与 `/compat/full` **未统一**；**无紫微宫位专维**；文案仍偏婚恋 |
| **合作伙伴** | 无 | `RelationType` **无** `business_partner` |
| **多人团队** | `POST /ziwei/multi_compat` | 仅紫微矩阵；**无关系类型**；与双人合盘 **模型不一致** |

### 0.2 已验证的内容缺陷（2026-07-13 刘博×程安东案例）

| 缺陷 | 影响 |
|------|------|
| 八字合盘 **不算日支冲**（丑未冲） | 情侣/合伙 **核心矛盾被低估** |
| 同午年支标「三合」 | 概念错误，损 **可信度** |
| 仅「夫妻宫↔命宫」 | 友人/亲子/合伙 **用错尺子** |
| 无 **双人共运时间轴** | 用户感「不够丰满」 |
| `interpretation_text` 与 `wealth_hint` **可矛盾** | 损 **Trust 层** |
| summary 默认「婚后」 | 非婚恋关系 **误导** |

### 0.3 产品目标（完成定义）

1. **6 类关系** + **个人单盘** 共用同一套 **fact/cite/inference** 语义。  
2. 任意双人合盘：**≤5 次 HTTP**（见 §四）。  
3. 首屏：**综合分 + 3–5 张 summary_card + 分维表**；推断 **默认折叠**。  
4. 每种 `relation_type` 有 **独立维度权重与宫位对**（见 registry）。  
5. OpenAPI + `relation-compat@1.0` **CI 阻断**；黄金案例 **≥6 对** 回归。

---

## 一、范围与关系类型

### 1.1 在范围内

| 模块 | 说明 |
|------|------|
| **P0** | 个人单盘「摘要层」；统一 `POST /api/v1/relation/full`；6 种双人关系 |
| **P1** | 共运时间轴；`tensions[]`；case 档案合盘 UI |
| **P2** | 多人合盘（2–4 人）矩阵 + 关系边属性 |
| **P3** | 分享 PNG / 合盘报告卷（GTM） |

### 1.2 关系类型枚举（冻结）

| `relation_type` | 中文 | 典型用户 |
|-----------------|------|----------|
| `couple` | 情侣合盘 | 婚恋、同居 |
| `friend` | 友人合盘 | 闺蜜、兄弟、知己 |
| `parent_child` | 亲子合盘 | 父母与子女 |
| `colleague` | 同事合盘 | 同僚、项目组 |
| `business_partner` | 合作伙伴合盘 | 生意、投资、合伙 |
| `supervisor_subordinate` | 上下级合盘 | 上司与下属（需 `supervisor_id`） |

**注册表权威**：[`relation-type-registry.json`](../contracts/relation-type-registry.json)

### 1.3 明确不做（打磨期）

- 付费墙 / entitlement 锁合盘  
- LLM 自动生成合盘长文（卷六问书除外）  
- 替用户判定「该不该分手/离职」（仅 heuristic + 免责声明）

---

## 二、目标架构

```
                    ┌─────────────────────────────────────┐
                    │  ChartSnapshot（每人只算一次）        │
                    │  bazi + ziwei · chart_hash          │
                    └──────────────┬──────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
  GET /profile/{id}/summary   POST /relation/full      GET /life/volumes
  （个人首屏卡片）              （双人合盘权威）           （六卷·不含合盘长文）
         │                         │
         │                         ├── RelationEngine
         │                         │     ├── BaziRelationScorer (registry)
         │                         │     ├── ZiweiRelationScorer (palace_pairs)
         │                         │     ├── TimelineMerger
         │                         │     └── CopyTemplate (relation_type)
         │                         │
         └─────────────────────────┴── explain/batch（可选 cite 层）
```

### 2.1 与六卷的关系

| 内容 | 归属 |
|------|------|
| 个人四柱、紫微盘面 | 现有 **卷一 / 卷四** |
| 个人域分析（财业婚健） | **卷五** · 默认折叠 |
| **双人合盘** | **新视图** `/relation/:type` · **不**硬塞进六卷 IA |
| 合盘典籍句 | **cite 层** · 有 `classic_id` 才展示 |

---

## 三、个人单盘（Individual Profile）改造

### 3.1 问题

- `bazi/full` 一次返回 **过大 JSON**（milestones + dayun narrative + domains）。  
- 报告页与用户「先懂自己」路径 **缺少 3 句摘要**。  
- 同一人在合盘中 **重复 compute**。

### 3.2 目标 API

| 端点 | 说明 |
|------|------|
| `GET /api/v1/profile/{case_id}/summary` | 首屏：四柱、格局一句、用神、命宫一句、2026 太岁一句 |
| `POST /api/v1/bazi/full?profile=slim` | **slim 模式**：无 `interpretation_text`、无 dayun narrative 全文 |
| 内部 | `ChartSnapshot` 缓存 `{chart_hash → bazi_raw, ziwei_raw}` |

### 3.3 个人 summary 字段（fact 为主）

```json
{
  "schema_version": "profile-summary@1.0",
  "case_id": "...",
  "pillars_primary": { "year": "...", "month": "...", "day": "...", "hour": "..." },
  "geju_one_liner": "七杀格·杀印相生（engine）",
  "yongshen_favor": ["metal", "water"],
  "strength_tier": "极弱",
  "ziwei_ming_one_liner": "己丑·紫微破军",
  "current_dayun": "己卯",
  "liunian_2026_tag": "值太岁",
  "disclaimer_block": { "text": "...", "version": "..." }
}
```

### 3.4 任务

| ID | 任务 | 优先级 |
|----|------|--------|
| IND-01 | 实现 `ChartSnapshot` 内部 DTO（对齐 BACKEND-MASTER §1.1） | P0 |
| IND-02 | `profile/summary` 路由 + schema | P0 |
| IND-03 | `bazi/full` slim profile 开关 | P1 |
| IND-04 | FE Profile 页顶部 summary 卡（替代长文首屏） | P1 |

---

## 四、统一关系合盘 API

### 4.1 权威端点

```
POST /api/v1/relation/full
```

**弃用路径（保留 6 个月 deprecated header）**：

- `POST /api/v1/compat/full` → 转发至 `/relation/full?relation_type=couple`  
- `POST /api/v1/relations/compat` → 合并；case 模式改为 body 传 `case_id` 或 `person`  

### 4.2 请求体

```json
{
  "relation_type": "couple",
  "supervisor_id": "a",
  "person_a": {
    "case_id": "optional-uuid",
    "birth_datetime": "1990-07-17T12:25:00",
    "tz": "Asia/Shanghai",
    "longitude": 117.18,
    "latitude": 34.26,
    "gender": "female",
    "label": "刘博"
  },
  "person_b": {
    "birth_datetime": "1990-06-17T20:15:00",
    "tz": "Asia/Shanghai",
    "longitude": 117.49,
    "gender": "male",
    "label": "程安东"
  },
  "options": {
    "include_bazi": true,
    "include_ziwei": true,
    "timeline_years": [-1, 2],
    "liunian_year": 2026
  }
}
```

| 字段 | 说明 |
|------|------|
| `relation_type` | **必填**；决定 registry 维度与文案 |
| `supervisor_id` | `supervisor_subordinate` 时 **必填**：`"a"` \| `"b"` |
| `person_*` | case_id 与 birth 二选一；有 case_id 则读 Snapshot |

### 4.3 响应体

权威 schema：[`relation-compat.schema.json`](../contracts/relation-compat.schema.json)

**首屏必填**：

- `combined_score` · `grade` · `summary`（≤280 字，**按 relation_type 模板**）  
- `summary_cards[]`（3–5 条，120 字/条）  
- `dimensions[]`（带 `weight` · `engine` · `layer`）  
- `timeline[]`（双人节点）  
- `action_items[]`（≤8 条，可执行）  
- `missing_fields[]` · `disclaimer_block`  

### 4.4 HTTP 预算

| 场景 | 请求 |
|------|------|
| 无 case（纯 birth） | `relation/full` 1 次（内嵌双盘 compute） |
| 有 case | `relation/full` 1 次（读 Snapshot） |
| 需典籍 cite | + `explain/batch` sections=`relation_reading` 1 次 |

**禁止**：合盘页再各打一次 `bazi/full` + `ziwei/full`。

---

## 五、评分引擎（按关系类型换尺子）

### 5.1 模块位置

```
services/relation_engine/
  __init__.py
  registry.py          # 读 relation-type-registry.json
  bazi_scorer.py       # 八字分维（含 day_branch 必填）
  ziwei_scorer.py      # 宫位对 + 飞星忌
  timeline.py          # 双人流年/大运节点合并
  copy_templates.py    # 各 relation_type 文案
  composer.py          # 合成 RelationCompatResponse
```

### 5.2 八字分维（相对 `services/compatibility.py` 的变更）

| 维度 ID | 说明 | 变更 |
|---------|------|------|
| `day_master` | 日干五行 | 保留 |
| **`day_branch`** | **日支合冲害刑** | **新增必填**，单独占权重 |
| `year_branch` | 年支 | **同支走 same**，禁止标三合 |
| `yongshen_cross` | 甲喜忌 vs 乙五行 | 从 relations 路由提升 |
| `wuxing_complement` | 互补 | 保留 |
| `stem_interaction` | 天干合冲 | 保留 |
| `ten_god_cross` | 十神交叉（亲子/上下级） | 亲子/上级加权 |
| `wealth_cross` | 财层交叉（合伙） | 合伙专用 |

### 5.3 紫微分维（相对 `ziwei_engine/compatibility.py` 的变更）

| 原维度 | 问题 | 新逻辑 |
|--------|------|--------|
| 固定「夫妻宫缘」 | 仅适用 couple | 改为 `palace_cross_score`，按 registry **palace_pairs** 动态算 |
| 命宫相合 | 保留 | 权重随 relation_type 调整 |
| 五行局 | 保留 | 合伙/同事降权 |
| 飞星忌 | 保留 | 写入 `conflict_points` + `palace_cross` |

**宫位对示例（情侣）**：

- A 夫妻宫 ↔ B 命宫  
- B 夫妻宫 ↔ A 命宫  
- 财帛 ↔ 财帛  

**宫位对示例（友人）**：

- A 交友宫 ↔ B 命宫  
- 兄弟宫 ↔ 命宫  

**宫位对示例（合伙）**：

- 财帛 ↔ 财帛  
- 官禄 ↔ 官禄  
- 田宅 ↔ 田宅  

### 5.4 综合分公式

```
combined_score = round( Σ (dim.score / dim.max_score * dim.weight) / Σ dim.weight * 100 )
```

- `bazi` 与 `ziwei` 维度 **统一汇入** `dimensions[]`，用 `engine` 字段区分。  
- 不再隐藏权重；FE 可展示「为何 59 分」。

### 5.5 矛盾显式化（Trust）

当检测到：

- 大运 `wealth_hint` 与 `wealth_analysis.trend` 相反  
- 日主 `strength_tier` 与 geju 文案冲突  

→ 写入 `tensions[]`，UI **朱线单行** 展示（对齐 MASTERPLAN）。

---

## 六、内容与文案规范

### 6.1 三层与折叠

| 层 | 合盘内容 | UI |
|----|----------|-----|
| **fact** | 四柱、宫位、冲合、分维得分 | 首屏 |
| **cite** | 典籍句（`classic_id` verified） | 卷式折叠 |
| **inference** | 相处建议、域预测 | **默认折叠** |

### 6.2 文案禁令（按 relation_type）

registry 中 `forbidden_copy`：**生成时校验**，CI grep 禁止串台。

| 类型 | 禁止出现 |
|------|----------|
| friend | 婚后、嫁娶、桃花 |
| parent_child | 夫妻、桃花、婚嫁 |
| business_partner | 感情保鲜、第三者 |
| colleague | 婚配、同居 |

### 6.3 summary 模板键

| relation_type | 模板键 |
|---------------|--------|
| couple | `relation.summary.couple` |
| friend | `relation.summary.friend` |
| … | 见 registry |

示例（couple）：  
> 「有缘相聚，宜沟通与规则；分维见日支与财帛。」

**禁止**固定使用「婚后共同努力可白头」 unless `relation_type=couple` **且** 用户标记 `cohabiting|married`。

### 6.4 丰满度标准（验收）

合盘页 **必须** 包含：

1. **综合分 + 等级**  
2. **≥6 个分维**（含日支、至少 2 个宫位对）  
3. **≥3 张 summary_card**（support / conflict / action 各至少 1）  
4. **timeline ≥4 节点**（含当年太岁）  
5. **action_items ≥3 条**（可执行，非空泛）  
6. **palace_cross ≥2 对**（fact 层）

---

## 七、前端 IA 与路由

### 7.1 新路径

```text
/profile/:caseId                    # 个人摘要 + 入口
/relation/new?type=couple           # 选关系 → 选人/录入
/relation/:relationId               # 合盘结果页
/relation/:relationId/timeline       # 共运轴（可 Tab）
```

### 7.2 合盘结果页布局（对齐 MASTERPLAN）

```text
┌─────────────────────────────────────────┐
│ VolumeHead · 情侣合盘 · 刘博 × 程安东    │
├─────────────────────────────────────────┤
│ [综合 59.5] [中签]  一句话 summary        │
│ ┌──────┐ ┌──────┐ ┌──────┐  summary_cards│
├─────────────────────────────────────────┤
│ 分维表（fact）· 日支冲 · 财帛六合 …       │
├─────────────────────────────────────────┤
│ 宫位互涉（fact）· 折叠                    │
├─────────────────────────────────────────┤
│ 共运时间轴 2025–2028（fact+inference）    │
├─────────────────────────────────────────┤
│ 相处建议 action_items（inference·折叠）   │
├─────────────────────────────────────────┤
│ 跋 · disclaimer · tensions · missing     │
└─────────────────────────────────────────┘
```

### 7.3 FE 任务

| ID | 任务 |
|----|------|
| FE-R01 | `RelationCompatView.vue` + `buildRelationCompat.ts` |
| FE-R02 | 关系类型选择器（6 类） |
| FE-R03 | `supervisor_subordinate` 上级选择 UI |
| FE-R04 | 类型 `npm run gen:types` 同步 |
| FE-R05 | E2E `fusheng-relation-couple` / `friend` / `partner` |

---

## 八、后端任务分解

### 8.1 P0（2 周，阻断发布）

| ID | 任务 | 文件/模块 |
|----|------|-----------|
| BE-R01 | 新建 `services/relation_engine/` + registry loader | 新包 |
| BE-R02 | `bazi_scorer.day_branch` 日支冲合害刑 | `bazi_scorer.py` |
| BE-R03 | 修复 `year_branch` same vs sanhe | `bazi_scorer.py` |
| BE-R04 | `ziwei_scorer.palace_pairs` 按 type | `ziwei_scorer.py` |
| BE-R05 | `POST /api/v1/relation/full` | `routers/relation_compat.py` |
| BE-R06 | 修复 `/compat/full` import → 委托新路由 | `routers/compat.py` |
| BE-R07 | OpenAPI + schema test | `tests/test_relation_compat_contract.py` |
| BE-R08 | 黄金案例 6 对 JSON | `data/relation_golden_cases.json` |

### 8.2 P1（2 周）

| ID | 任务 |
|----|------|
| BE-R09 | `timeline.py` 双人节点合并 |
| BE-R10 | `tensions[]` 检测器 |
| BE-R11 | `GET /profile/{id}/summary` |
| BE-R12 | case 模式合盘（合并旧 `/relations/compat`） |
| BE-R13 | `business_partner` 写入 `RelationType` enum |

### 8.3 P2

| ID | 任务 |
|----|------|
| BE-R14 | `multi_compat` 对齐 `relation/full` 分维 |
| BE-R15 | explain section `relation_reading` + cite |
| BE-R16 | 合盘 Snapshot 持久化 `kind=relation` |

---

## 九、测试与黄金案例

### 9.1 黄金案例（`data/relation_golden_cases.json`）

| ID | 关系 | 用途 |
|----|------|------|
| RG-COUPLE-01 | 刘博 × 程安东 · couple | 日支丑未冲必须出现在 `day_branch` 维 |
| RG-FRIEND-01 | 合成或真实 · friend | 不得出现「婚后」 |
| RG-PARENT-01 | 亲子 · parent_child | 子女宫↔命宫对有内容 |
| RG-BIZ-01 | 合伙 · business_partner | 财帛对权重最高 |
| RG-COLLEAGUE-01 | 同事 | 官禄对 |
| RG-SUP-01 | 上下级 | supervisor_id 生效 |

### 9.2 CI 门禁

```powershell
python -m pytest tests/test_relation_compat_contract.py -q
python -m pytest tests/test_relation_golden_cases.py -q
python scripts/quality_gate.py --section backend
cd frontend && npm run test:e2e -- fusheng-relation
```

### 9.3 回归断言示例

```python
def test_couple_liubo_chen_day_branch_chong():
    resp = client.post("/api/v1/relation/full", json=RG_COUPLE_01)
    dims = {d["id"]: d for d in resp.json()["dimensions"]}
    assert dims["day_branch"]["score"] <= 5
    assert any("丑未" in c["text"] for c in resp.json()["summary_cards"] if c["tone"] == "conflict")
```

---

## 十、FE-BE 新决议（追加 FE-BE-DECISIONS）

| # | 问题 | 决议 |
|---|------|------|
| Q16 | 合盘权威端点？ | **`POST /api/v1/relation/full`**；`/compat/full` deprecated |
| Q17 | 关系类型枚举？ | registry **6 类**；扩展只改 JSON + 测试 |
| Q18 | 个人 vs 合盘内容边界？ | 个人 **summary**；合盘 **不进六卷 IA** |
| Q19 | 合盘首屏？ | **cards + 分维**；inference 默认折叠 |
| Q20 | 日支冲是否进分？ | **是**；所有双人关系 **必填维** |

---

## 十一、里程碑与排期（建议）

| 周 | 交付 |
|----|------|
| **W1** | BE-R01–R04 · registry · 日支维 · 单元测试 |
| **W2** | BE-R05–R08 · `/relation/full` · 黄金 6 对 · OpenAPI |
| **W3** | FE-R01–R04 · 情侣页 · E2E couple |
| **W4** | BE-R09–R12 · timeline · profile summary · 其余 5 类型文案 |
| **W5** | 全类型 E2E · 文档 · 弃用 compat 公告 |

---

## 十二、文档与索引更新

| 文档 | 动作 |
|------|------|
| [`docs/README.md`](../README.md) | 增加本文链接 |
| [`docs/contracts/README.md`](../contracts/README.md) | 增加 relation-compat · registry |
| [`docs/plan/FE-BE-DECISIONS.md`](./FE-BE-DECISIONS.md) | 追加 Q16–Q20 |
| [`FUSHENG-DEV-HANDBOOK.md`](../FUSHENG-DEV-HANDBOOK.md) | §六 代码地图增加 `relation_engine` |

---

## 十三、附录 A · 现状端点对照表

| 端点 | 保留 | 迁移至 |
|------|------|--------|
| `POST /compat/full` | deprecated | `/relation/full?type=couple` |
| `POST /ziwei/compatibility` | deprecated | `/relation/full` |
| `POST /bazi/compatibility` | deprecated | `/relation/full` |
| `POST /relations/compat` | merge | `/relation/full` + case_id |
| `POST /ziwei/multi_compat` | P2 对齐 | 矩阵 + `relation_type` on edges |

---

## 十四、附录 B · 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| relation-master-1.0 | 2026-07-13 | 初稿：问题陈述、统一 API、registry、P0–P2、测试 |
| relation-master-1.1 | 2026-07-13 | **已实现 P0+P1 后端/前端**：relation_engine、/relation/full、profile/summary、黄金案例、FE RelationCompatView |
| relation-master-1.2 | 2026-07-13 | **P1 收尾**：case_id 解析、relations/compat 合并、slim bazi、Profile 引擎摘要、deprecated 端点、E2E fusheng-relation |

---

## 十五、实现进度快照（2026-07-13）

### 已完成 ✅

| 任务 ID | 说明 |
|---------|------|
| BE-R01–R08 | relation_engine、/relation/full、compat 委托、黄金案例、契约测试 |
| BE-R09–R13 | timeline、tensions、profile/summary、business_partner、case 模式 |
| BE-R12+ | `case_id` 解析（`case_resolver.py`）、`relation_v1` snapshot 持久化 |
| IND-01–02 | ChartSnapshot 复用 + profile/summary |
| IND-03 | `POST /bazi/full?profile=slim` |
| IND-04 | Profile 页引擎摘要条 + 关系合盘入口 |
| FE-R01–R05 | RelationCompatView、6 类选择器、E2E fusheng-relation |
| 附录 A | `/compat/full`、`/bazi/compatibility`、`/ziwei/compatibility`、`/relations/compat` 已标 deprecated |

### 待办（P2/P3）⏳

| 任务 ID | 说明 |
|---------|------|
| BE-R14 | `multi_compat` 对齐 relation/full 分维 |
| BE-R15 | explain section `relation_reading` + cite 层 |
| FE 路由 | `/relation/:relationId` 持久化结果页（当前仅 `/relation/new`） |
| FE-R04 | `npm run gen:types` 同步 OpenAPI 类型（需本地跑一遍） |
| P3 | 分享 PNG / 合盘报告卷 · 样例评审见 [`R086`](../reports/R086-relation-compat-sample-pdf-review-2026-07-13.md) |
| CI | `quality_gate.py --section backend` 纳入 relation 测试（可选） |
