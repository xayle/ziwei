# R107 · W14 打磨期收官 — Sign-Off Draft — 2026-07-12

## Automated blocks (ready)

| Block | IDs | Status |
|-------|-----|--------|
| Engine edge C/D | R026–R045 | ☑ |
| Explain/trust | R046–R059 | ☑ |
| Frontend wiring | R061–R084, R086–R100 | ☑ |
| SRC advisory | R111–R115 | ☑ |
| P3 life/volumes draft | R096/R116 | ☑ |
| Product auto | R101 | ☑ 11/11 |
| R103 auto | R103 script | ☑ 6/7 |
| Design structural | R102 | ☑ 3/3 proxy |
| Targets compare | R079 JSON | ☑ compare-live-targets |
| W14 bundle | auto_verify_w14 | ☑ **7/7**（pass 4 · 2026-07-13） |
| debt scan | rg 三门禁 | ☑ **0 命中**（`VolumeHead` 重命名） |
| Frontend lint | eslint | ☑ **0 warning** |
| life/volumes E2E | fusheng-life-volumes | ☑ remote path |
| R079 Q5 + compare | R079 doc + JSON | ☑ 15/15 proxy（产品姓名待补） |
| OpenAPI CI drift | `docs/openapi.json` + `schema.d.ts` | ☑ 已同步暂存；commit 被 pre-commit 阻断（见下） |
| snapshot restore E2E | fusheng-report | ☑ 档案云端 Tab → 报告 + `report-snapshot-note` |
| Backend P0 meta | R018–R019, R112–R113 | ☑ |

## Pending human sign-off

| ID | Item | Doc | Status |
|----|------|-----|--------|
| R025 | life-volume schema 三方共签 | R025 draft | ☐ |
| R060 | 15-min 试读 step 10 + 签字 | R060 checklist | ☐ |
| R071/R079/R085 | 防丑五问 15 格 | R079 | 🟡 15/15 ☑；产品姓名待补 |
| R102 | DS 视觉并排 | live-targets vs targets | ☑ compare PASS |
| R103 | 防丑五问全「是」 | R079 | ☑ **6/7 auto**；Q5 盲测待 DS |
| R104–R105 | M4/M5 产品试 | R104/R105 checklists | 🟡 已填表；外发+产品签待补 |
| R107 | **本表负责人签字** | below | ☐ |

## R109 · POST-W14 决议（建议）

**决议：** 维持打磨优先；POST-W14 T071–T140 **延后** 至 R107 正式签字后 2 周评审。

| 选项 | 说明 |
|------|------|
| A（推荐） | 继续修 advisories + DS 五问；不开启 GTM |
| B | 进入 U5 life/volumes API（R096） |
| C | 开启 GTM 试投（需 R104/R105 绿） |

## R107 签字

| 角色 | 姓名 | 日期 | W14 收官 |
|------|------|------|:--------:|
| 负责人 | | | ☐ |

**Gate:** R025 + R060 + R079 全勾 → 可标 **T070 ☑**（R110）。

## Final verification command bundle

```powershell
make scorecard
make quality-gate-backend
cd frontend && npm run test && npm run test:e2e
pytest -q tests/test_explain_*.py tests/test_zw18_trust.py tests/test_life_volume_schema_contract.py
```

---

**Verdict:** Automation complete; **W14 未收官** until human rows above are signed.

## Commit 说明（2026-07-13 pass 4）

**已提交** `cd366bd`：OpenAPI + gate 文档 + 路由 smoke。

**工作区待提交**（handbook pass 4 批次）：

- `VolumeHead` 重命名 + debt scan 0
- `quality_gate.py` Windows 修复
- `FUSHENG-DEV-HANDBOOK.md` + 文档索引
- `ReportView` 姓名死代码/CSS 清理
- `static/app/` build 产物

```powershell
python scripts/auto_verify_w14.py   # expect pass: true
cd frontend && npm run lint && npm run test && npm run test:e2e
```
