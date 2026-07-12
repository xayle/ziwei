# 共享契约索引

前后端 API 与 JSON 形状的**唯一真源**（代码生成与测试应对齐此处）。

| 文件 | 用途 | 权威阶段 |
|------|------|----------|
| [life-volume.schema.json](./life-volume.schema.json) | 六卷 + 卷首 + 跋响应形状 | FE Adapter W3+；BE GET /life/volumes W16+ |
| [explain-section-map.json](./explain-section-map.json) | explain sections ↔ 卷目映射 + 报告加载策略 | P1 explain |
| [relation-compat.schema.json](./relation-compat.schema.json) | 双人关系合盘 `POST /relation/full` 响应 | P0 relation_engine |
| [relation-type-registry.json](./relation-type-registry.json) | 6 类关系 → 八字维/紫微宫位对/文案禁令 | P0 relation_engine |

**引用文档：** [FUSHENG-INTEGRATED-DEV-PLAN](../plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md) · [RELATION-COMPAT-MASTER-PLAN](../plan/RELATION-COMPAT-MASTER-PLAN-2026-07-13.md) · [FE-BE-DECISIONS](../plan/FE-BE-DECISIONS.md)

**前端类型：** `frontend/src/types/life-volume.ts` — 与 schema 字段对齐  
**前端契约常量：** `frontend/src/constants/feBeContract.ts` · `frontend/src/utils/feBeAdapter.ts`  
**前端开发文档：** [`docs/guides/FUSHENG-FRONTEND-DEV.md`](../guides/FUSHENG-FRONTEND-DEV.md)

**校验（待建）：** `tests/test_life_volume_schema.py` — jsonschema 验证 fixture
