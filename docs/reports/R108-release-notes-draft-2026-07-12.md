# 浮生 · W14 打磨期发布说明（草案）— R108

**日期：** 2026-07-12 · **范围：** R001–R110 自动化轨

## Summary

- **六卷报告 + 跋** 主路径；explain/batch 接入；`GET /life/volumes` 可选权威路径（登录+remoteCaseId）
- **引擎** scorecard 24/24；iztro/wenmo horoscope 对照轨 CI advisory
- **质量门** `auto_verify_w14` 6/6 · vitest **87/87** · E2E **47/47** 全绿（无 skip）
- **设计** live PNG + `compare-live-targets` PASS（height advisory）

## R101 产品 11 项

[R101-auto-verify-2026-07-12.md](./R101-auto-verify-2026-07-12.md) — **auto 11/11 ✅**

## R103 预警 7 项

[R103-auto-verify-latest.json](./R103-auto-verify-latest.json) — **auto 6/7 ✅**（防丑五问 Q5 待 DS）

| # | 项 | Auto |
|---|-----|:----:|
| 1–2 | R-01~R-05 / 三门禁 | ✅ risk-alert E2E + debt 0 |
| 3 | 防丑五问全「是」 | ⏸ DS |
| 4 | targets 截图 | ✅ compare JSON pass |
| 5–7 | 叙述预算 / 卷五 / 卷六 | ✅ |

## Scorecard

```
Overall: 10.0/10  Passed: 24/24
```

`docs/reports/scorecard-latest.json`

## New automation (pass 3)

| Script / Spec | Purpose |
|---------------|---------|
| `auto_verify_w14.py` | 后端 bundle |
| `auto_verify_r103.py` | 预警 6/7 |
| `compare-live-targets.mjs` | R079 截图对比 |
| `fusheng-life-volumes.spec.ts` | remote 数据源 E2E |
| `fusheng-report.spec.ts` | 快照恢复 E2E（cities/cases pathname mock + `data-snapshots-ready`） |

## Known advisories

- **OpenAPI/types** — `docs/openapi.json` + `schema.d.ts` 已重导（R094）；**待 PR 提交** 清 CI drift
- POST-W14 GTM: **deferred** (R109 选项 A)
- W14 收官: R025/R060/R079 Q5/R107 人工

## Reports index

R100 · R101 · R102 · R079 · R080 · R084 pass2 · R096 · R106 · R060 · R025 · R107

---

Attach PR screenshots per R079 when merging W14.
