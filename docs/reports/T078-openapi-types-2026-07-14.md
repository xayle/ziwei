# T078 · OpenAPI + gen:types · life 契约双端

| 字段 | 内容 |
|------|------|
| **日期** | 2026-07-14 |
| **结论** | ☑ `export_openapi` + `npm run gen:types` 已同步；BE/FE life 契约测试绿 |

## 同步内容（本轮纳入 schema）

- `GET /api/v1/life/snippets/{case_id}`（T076）
- `ArchiveBundleRequest.include_name_pointer` / `include_zeri_pointer`（T077）
- `ArchiveExtensionPointer` · `LifeSnippetsResponseModel`
- liunian-report `queue_backend` 文档字符串（T075）

## 验收

```powershell
python scripts/export_openapi.py
cd frontend; npm run gen:types
pytest -q tests/test_life_volume_schema_contract.py tests/test_life_volumes_api.py tests/test_life_snippets_api.py tests/test_openapi_sync.py
cd frontend; npm run test -- --run src/api/__tests__/openapiLifeContracts.spec.ts
```

## CI

`.github/workflows/ci.yml` 已有：

- OpenAPI export drift `git diff --exit-code docs/openapi.json`
- Frontend types drift `git diff --exit-code src/api/schema.d.ts`

→ **PR 改 schema 会红**（T078 验收「PR diff 阻断」）。
