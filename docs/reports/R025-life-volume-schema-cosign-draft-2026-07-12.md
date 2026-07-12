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

## Human co-sign (required for R025 ☑)

| 角色 | 姓名 | 日期 | 决议 |
|------|------|------|------|
| 后端 | | | schema 与 OpenAPI/explain 一致 ☐ |
| 前端 | | | buildLifeVolumes 为 Adapter，字段对齐 ☐ |
| 校勘 | | | cite 层 classic_id 策略认可 ☐ |

## Open items (W16+)

- `GET /life/volumes` 权威 API（R096/R116）— Adapter 仍可用至 W16。

---

**Automation:** contract tests green. **R025 ☐** until three signatures above.
