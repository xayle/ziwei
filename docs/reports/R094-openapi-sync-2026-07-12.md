# R094 · OpenAPI + gen:types 同步 — 2026-07-12

CI drift 双端验收复跑。

## Commands

```powershell
python scripts/export_openapi.py
cd frontend && npm run gen:types
python -m pytest -q tests/test_openapi_sync.py
cd frontend && npm run type-check
```

## Results

| Check | Result |
|-------|--------|
| Export paths | **150** |
| `test_openapi_sync.py` | **27/27** |
| `gen:types` → `schema.d.ts` | ✅ |
| `vue-tsc --noEmit` | ✅ |

## Synced artifacts

- `docs/openapi.json` — includes `GET /api/v1/life/volumes/{case_id}`
- `frontend/src/api/schema.d.ts` — regenerated

## CI

`.github/workflows/ci.yml` test job:

```yaml
python scripts/export_openapi.py
git diff --exit-code docs/openapi.json
```

**Action:** commit `docs/openapi.json` + `frontend/src/api/schema.d.ts` in PR to clear drift.

---

**R094 ☑** (automation green; commit pending in working tree)
