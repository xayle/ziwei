# 前后端协作决策表（已决议）

| 字段 | 内容 |
|------|------|
| **版本** | fe-be-1.0 |
| **日期** | 2026-07-12 |
| **权威** | [FUSHENG-INTEGRATED-DEV-PLAN](./FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md) |
| **契约** | [life-volume.schema.json](../contracts/life-volume.schema.json) · [explain-section-map.json](../contracts/explain-section-map.json) |

| # | 问题 | 决议 | 目标日期 | 负责人 |
|---|------|------|----------|--------|
| Q1 | `life/volumes` 何时上线？FE 拼装过渡期？ | **W16** 上线 GET；**W3–W15** FE 用 `buildLifeVolumes` Adapter | W16 | BE |
| Q2 | 六卷 `locked` 规则？ | **打磨期恒 false**；GTM W17+ 按 entitlement（卷0–1 免费，2–4 pass，5–6 pro） | W17+ | 产品+BE |
| Q3 | `colophon` 后端聚合 vs FE？ | **W3–W15** FE `buildColophonSummary`；**W16+** 后端 `life/volumes.colophon` 权威 | W16 | BE |
| Q4 | `interpretation_text` 限长/迁出？ | Compute **W8 起**默认不返回长文；Explain 承载；FE **W3 起**截断 80 字兜底 | W8 | BE+FE |
| Q5 | `provenance.layer` 枚举？ | API 保留 `classical\|engine\|heuristic`；**UI 仅** fact/cite/inference（映射表见集成文档 §3.1） | W3 冻结 | FE |
| Q6 | `evidence_chain.source_page`？ | **P2** verified 条目必填；FE 卷二/跋 W12 前展示页码 | W12 | BE+校勘 |
| Q7 | explain sections 与六卷映射？ | **[explain-section-map.json](../contracts/explain-section-map.json)** 权威 | W3 | BE |
| Q8 | 大运叙事默认加载？归哪卷？ | **默认不加载** `loadDayunNarratives`；叙事归 **卷三** explain `dayun` section | W8 | FE |
| Q9 | 报告页请求策略？ | **W8–W15**：`archive-bundle` + `bazi/ziwei explain/batch`；**W16+**：`GET life/volumes` 单请求 | W8 | FE+BE |
| Q10 | ZW18 degraded 运限 API？ | **200** + `trust_level: degraded` + warnings；**不** 403 | W3 | BE |
| Q11 | `monthly_fortune` 保证？ | **不保证**；有则卷三 3.3 节展示，无则 `missing_fields` 明示 | W8 | BE |
| Q12 | `reading_guide` 谁下发？ | **P1** `explain` section=`reading`；八字/紫微 **分轨** 两个 model | W8 | BE |
| Q13 | `last_volume_id` 续读？ | **FE localStorage** `useReadingProgress`；**不扩展** snapshot API（打磨期） | W8 | FE |
| Q14 | OpenAPI drift CI？ | **是**；PR 必须 `export_openapi` + `npm run gen:types` | W2 | BE+FE |
| Q15 | classics verified 与 UI 标签？ | 仅 **verified** 可显示「典籍依据」；其余「待校勘」；MVP-20 **W8** 齐 | W8 | BE+校勘+FE |
| Q16 | 合盘权威端点？ | **`POST /api/v1/relation/full`**；`/compat/full` deprecated 转发 | W1–W2 | BE |
| Q17 | 关系类型枚举？ | registry **6 类**（含 `business_partner`）；扩展只改 JSON + 测试 | W1 | BE+FE |
| Q18 | 个人 vs 合盘内容边界？ | 个人 **`GET /profile/{id}/summary`**；合盘 **不进六卷 IA** | W2–W4 | BE+FE |
| Q19 | 合盘首屏？ | **cards + 分维表**；inference 默认折叠 | W3 | FE |
| Q20 | 日支冲是否进分？ | **是**；所有双人关系 **必填维** `day_branch` | W1 | BE |

**契约追加：** [relation-compat.schema.json](../contracts/relation-compat.schema.json) · [relation-type-registry.json](../contracts/relation-type-registry.json) · [RELATION-COMPAT-MASTER-PLAN](./RELATION-COMPAT-MASTER-PLAN-2026-07-13.md)

---

## 变更记录

| 版本 | 日期 | 说明 |
|------|------|------|
| fe-be-0.1 | 2026-07-12 | 空表待填 |
| **fe-be-1.0** | **2026-07-12** | 15 题全部决议；对齐 integrated-1.0 |
| **fe-be-1.1** | **2026-07-13** | Q16–Q20 关系合盘；见 RELATION-COMPAT-MASTER-PLAN |
