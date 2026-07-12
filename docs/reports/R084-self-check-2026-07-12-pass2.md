# R084 Self-Check Pass 2 — 2026-07-12

第二轮 §三 / W14 自动化验收（10 步批次）。

## 10 步自动化清单

| # | 步骤 | 结果 |
|---|------|------|
| 1 | `scripts/compare-live-targets.mjs` | ✅ 新增（尺寸/体积比） |
| 2 | `scripts/auto_verify_r007.py` | ✅ Q1–Q15 决议可机读 |
| 3 | `scripts/auto_verify_w14.py` | ✅ 后端 bundle 绿 |
| 4 | `make` targets：`compare-live-targets` · `auto-verify-w14` · `auto-verify-r007` | ✅ |
| 5 | E2E `fusheng-targets-screenshot` 导出 live PNG | **4/4** |
| 6 | `compare-live-targets` 三页对比 | ✅ pass（height advisory） |
| 7 | `auto_verify_w14` scorecard+gate+pytest | **5/5** |
| 8 | Vitest + type-check | **77/77** + pass |
| 9 | E2E responsive+flow+bazi-ziwei | **19/19** |
| 10 | 债务 `rg` 扫描 | **0 命中** |

## 命令摘要

```text
python scripts/auto_verify_w14.py          → pass
node scripts/compare-live-targets.mjs    → pass (height advisory ×3)
npm run test                               → 77/77
npm run test:e2e -- fusheng-targets-screenshot → 4/4
npm run test:e2e -- fusheng-responsive fusheng-flow fusheng-bazi-ziwei → 19/19
rg "linear-gradient|PageHead|#334155|-ok-bg|trust-drift-bg|四维分析|ChapterStub" frontend/src → 0
```

## Advisory

| 项 | 说明 |
|----|------|
| targets 高度 | 冻结 PNG 来自 skin-preview 裁剪；实机 1120×800 为 advisory，待 DS 并排目检 |
| OpenAPI | `export_openapi.py` 本地有较大 diff，交 CI/R094 处理 |
| R079 Q5 / R103 #3 | 防丑五问 blind test 仍须人工 |

## 产物

- `docs/reports/live-targets-latest/live-*.png`
- `docs/reports/R079-targets-compare-latest.json`
- `docs/reports/w14-auto-verify-latest.json`

---

**R084 pass2:** 可自动化块全绿。R060/R079 DS 签字仍待人工。
