# R096 · GET /life/volumes Draft — 2026-07-12

W16 authority path **development starter** (U5 / P3-01).

## FE optional hook (2026-07-12)

| Item | Detail |
|------|--------|
| API client | `frontend/src/api/life.ts` → `GET /api/v1/life/volumes/{case_id}` |
| ReportView | Tries remote when logged in + `remoteCaseId`, or `VITE_USE_LIFE_VOLUMES_API=true` |
| Fallback | `buildLifeVolumes` Adapter remains default (Q1 W16) |
| Debug attr | `data-life-volume-source="local|remote"` on report root |
| E2E | `fusheng-life-volumes.spec.ts` — remote 路径 1/1（snapshots mock 防 401） |

## Deliverables

| Item | Path |
|------|------|
| Schema | `app/schemas/life_volume.py` |
| Builder | `services/life_volume_service.py` |
| Router | `GET /api/v1/life/volumes/{case_id}` · `routers/life.py` |
| Tests | `tests/test_life_volumes_api.py` (3/3) |

## Behaviour

- Loads owned `Case` from DB
- Aggregates `bazi/full` snapshot + `ziwei/full` + explain batch (`geju/relations/domains` + `palaces/fortune`)
- Returns `life-volume@1.0` with **8 volumes + colophon**
- Vol5 sections default `collapsed_default: true`
- Colophon includes `wenmo_advisory` when present

## FE transition note

打磨期 FE **continues** `buildLifeVolumes` Adapter (Q1 W16). This endpoint is for contract联调 and POST-W14 U5.

## Bugfix bundled

`explain_ziwei.py` fortune section: `DayunItem` uses `ganzhi` (not `palace_name`); `LiunianInfo` single-year (not `.items`).

## Verification

```powershell
pytest -q tests/test_life_volumes_api.py tests/test_life_volume_schema_contract.py
```

---

**R096 ☑** (draft) · **R116** schema field ☑ · W16 full authority (cache, snippets) deferred.
