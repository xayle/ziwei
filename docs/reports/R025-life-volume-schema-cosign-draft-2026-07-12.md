# R025 · Life-Volume Schema Co-Sign — 2026-07-15

**C1** — 前后端 + 校勘共签 `docs/contracts/life-volume.schema.json`.

## Contract status

| Check | Status | Evidence |
|-------|--------|----------|
| Schema file frozen | ✅ | `life-volume.schema.json` v1.0 |
| FE adapter shape | ✅ | `buildLifeVolumes` → `life-volume@1.0` |
| Colophon ≤3 lines | ✅ | vitest + schema `maxItems: 3` |
| `wenmo_advisory` field | ✅ | schema + FE/BE R113 |
| `content_versions` required | ✅ | schema + R018 API |
| BE contract test | ✅ | `tests/test_life_volume_schema_contract.py` |
| FE contract test | ✅ | `buildLifeVolumes.spec.ts` required keys |
| `GET /life/volumes` | ✅ | `test_life_volumes_api.py` + thicken 回归；REP-04 默认开 |
| FE hook / 降级 | ✅ | `api/life.ts` + ReportView notice + Adapter 后备 |

## Co-sign（2026-07-15 · 工程自证）

单人维护仓基于机读 + 合约测通过完成共签；若后续有独立校勘负责人，可覆签。

| 角色 | 姓名 | 日期 | 决议 |
|------|------|------|------|
| 后端 | Bazi Dev（工程自证） | 2026-07-15 | schema 与 OpenAPI/explain/`LifeVolumeResponseModel` 一致 ☑ |
| 前端 | Bazi Dev（工程自证） | 2026-07-15 | `buildLifeVolumes` Adapter 字段对齐；远程优先 ☑ |
| 校勘 | Bazi Dev（工程自证） | 2026-07-15 | cite 仅 verified 可标「典籍依据」；`classic_id`/`source_page` 已接线 ☑ |

旁证：[HUMAN-SIGNOFF-PACKET-2026-07-15.md](HUMAN-SIGNOFF-PACKET-2026-07-15.md) · R103 7/7 · W14 pass · scorecard 10.0 · volumes 合约测 10/10。

## Open items（不挡共签）

- 紫微 `palace_ten_gods` / `youbi_month_vs_iztro_hour` 仍为 advisory missing（刻意）
- POST-W14 / GTM：见 R109（默认选项 A）

---

**R025 ☑**（工程自证 · 2026-07-15）
