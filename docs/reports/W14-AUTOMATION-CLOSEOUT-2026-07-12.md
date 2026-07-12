# W14 自动化轨收官 — 2026-07-12

`docs/plan/FUSHENG-EXECUTION-REMAINING.md` 中 **可机读验收** 已闭合；以下为终态摘要。

## 一键复验

```powershell
python scripts/auto_verify_w14.py      # 7/7：scorecard · gate · R007/R103/R060 · pytest core
python scripts/auto_verify_env.py
node scripts/compare-live-targets.mjs    # 需先 E2E targets 导出 live PNG
make generate-r108
```

## 自动化矩阵

| 域 | ID | 状态 | 证据 |
|----|-----|------|------|
| 引擎 | scorecard | 24/24 | `scorecard-latest.json` |
| 契约 | R094/R025 tests | 绿 | openapi 27/27 · life-volume contract |
| 产品 | R101 | 11/11 | R101 report |
| 预警 | R103 | 6/7 | R103-auto-verify-latest.json |
| 试读 | R060 | 步骤 1–9 · `auto_verify_r060` **7/7 子项** | `fusheng-trial-read.spec.ts` · Windows GBK 打印已修 |
| 风险 | R080 | 3/3 | `fusheng-risk-alert.spec.ts` |
| 防丑 | R071/R079 | 结构+compare | anti-slop + compare JSON |
| 终验 | R106 | 绿 | R106-final-verify |
| 环境 | R002/R004 | 机读 | env-auto-verify-latest.json |
| 发布 | R108 | 可生成 | `make generate-r108` |
| POST-W14 | R109 | 建议 A | R109-post-w14-decision |

## 人工 Gate（未闭合）

| ID | 阻塞 |
|----|------|
| R025 | 三方 schema 签字 |
| R060 | 步骤 10 主观 + 签字 |
| R079 Q5 | 防丑五问 15 格 |
| R085 | 三页自检块签字 |
| R104–R105 | M4/M5 产品试 |
| R107 | 负责人 W14 签字 |
| R110 | R107 后更新 EXECUTION-PRIORITY |

## PR 提交提醒

工作区待提交（清 CI drift）：

- `docs/openapi.json`
- `frontend/src/api/schema.d.ts`

```powershell
python scripts/export_openapi.py
cd frontend && npm run gen:types
```

---

**Verdict:** 自动化轨 **CLOSED**；W14 产品收官待 **R107 人工签字**。
