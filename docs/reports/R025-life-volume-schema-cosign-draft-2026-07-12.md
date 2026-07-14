# R025 · Life-Volume Schema Co-Sign — Draft — 2026-07-12

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
| `GET /life/volumes` draft | ✅ | `test_life_volumes_api.py` 3/3 |
| FE optional hook | ✅ | `api/life.ts` + `ReportView` fallback |
| `GET /life/volumes` 权威路径 | ✅ | 默认开启（REP-04）；Adapter 为降级 / 未登录后备 |

## Human co-sign (required for R025 ☑)

| 角色 | 姓名 | 日期 | 决议 |
|------|------|------|------|
| 后端 | | | schema 与 OpenAPI/explain 一致 ☐ |
| 前端 | | | buildLifeVolumes 为 Adapter，字段对齐 ☐ |
| 校勘 | | | cite 层 classic_id 策略认可 ☐ |

## 旁证刷新（2026-07-15）

见签字包：[HUMAN-SIGNOFF-PACKET-2026-07-15.md](HUMAN-SIGNOFF-PACKET-2026-07-15.md)（R103 7/7 · W14 pass · scorecard 10.0）。

## Open items（产品深化，不挡共签）

- 紫微 `palace_ten_gods` / `youbi_month_vs_iztro_hour` 仍为 advisory missing（刻意）
- POST-W14 / GTM：待 R107 后按 R109 再议

---

**Automation:** contract + volumes API green. **R025 ☐** until three signatures above.
