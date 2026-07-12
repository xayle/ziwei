# R106 · INTEGRATED §十 终验复跑 — 2026-07-12

Block H 终验命令复跑（pass 3 — 快照 E2E 去 skip）。

## 后端

| 命令 | 结果 |
|------|------|
| `python scripts/auto_verify_w14.py` | **7/7** pass（含 R060 trial E2E） |
| `python scripts/auto_verify_r103.py` | **6/7** pass（Q5 人工） |
| `pytest` core explain/schema/life/import | **22/22** |

## 前端

| 命令 | 结果 |
|------|------|
| `npm run test` | **87/87** |
| `npm run type-check` | pass |
| E2E 全量 | **47/47**（含快照恢复；无 skip） |
| E2E life/volumes remote | **1/1**（snapshots mock 防 401 清 token） |

## CI 接线（本轮）

- `test` job: `auto_verify_w14` + `verify-volume-names`
- `frontend` job: E2E 后 `compare-live-targets.mjs`

## Advisory

- `docs/openapi.json` 本地大 diff — 需单独 `make export-openapi && make sync-frontend-types` 提交
- R107/R110 仍待人工签字后更新

---

**R106 ☑**（自动化复验绿）
