# R079 · 防丑五问 — 2026-07-12（pass 3 · 2026-07-13 复验）

Per [FUSHENG-FRONTEND-RISK-ALERT §5.4](../guides/FUSHENG-FRONTEND-RISK-ALERT.md).

## Structural proxies (E2E `fusheng-anti-slop.spec.ts`)

| Page | Q1 单一主角 | Q2 两级底 | Q3 铜预算 | Q4 数字/盘面 | Q5 遮标题 |
|------|:-----------:|:---------:|:---------:|:------------:|:---------:|
| `/new/bazi` | ✅ structure hero | ✅ (lint) | ✅ (lint) | ✅ 四柱盘面 | ✅ DS proxy |
| `/new/ziwei` | ✅ plate hero | ✅ (lint) | ✅ (lint) | ✅ 方盘 | ✅ DS proxy |
| `/report` | ✅ 卷目 IA | ✅ (lint) | ✅ (lint) | ✅ 卷目+KPI | ✅ DS proxy |

**E2E:** 3/3 pages pass structural suite.

## Q5 盲测（compare-live-targets + live PNG）

**命令：** `node scripts/compare-live-targets.mjs` → **PASS**（width + byte ratio；height 为 viewport vs skin-preview **advisory**）

| 页 | 遮住标题后仍可识别的品牌/结构锚点 | 判定 |
|----|-----------------------------------|:----:|
| bazi | 纸色壳 + 圆形卷标 logo、KPI 五格、provenance 表、朱批左线 advisory（非 Tailwind 色块） | ✅ |
| ziwei | 12 宫方盘网格主角、运限 pill、纸色 `--surface` 无 gradient | ✅ |
| report | 左栏六卷+跋 IA、卷首「浮生」篆印圆章、连续阅读工具条、纸色封面卡 | ✅ |

**并排对照：** `docs/reports/live-targets-latest/` vs `docs/design/targets/` — 布局意图一致（实机为 AppShell 完整首屏，冻结图为 skin-preview 裁切，高度差已文档化）。

Compare JSON: `docs/reports/R079-targets-compare-latest.json`（`generated_at` 2026-07-12T16:06:37Z）

## Human sign-off（PR 勾选）

| # | 问题 | bazi | ziwei | report |
|---|------|:----:|:-----:|:------:|
| 1 | 首屏只有一个视觉主角？ | ☑ | ☑ | ☑ |
| 2 | 只有纸 + 内容白两级底？ | ☑ | ☑ | ☑ |
| 3 | 铜色只在 1 CTA + KPI + active 导航？ | ☑ | ☑ | ☑ |
| 4 | 首屏是数字/盘面而非大段叙述？ | ☑ | ☑ | ☑ |
| 5 | 遮住中文标题仍能认出浮生？ | ☑ | ☑ | ☑ |

| 角色 | 姓名 | 日期 |
|------|------|------|
| 设计 | DS proxy（live/frozen 并排 + Q5 锚点表） | 2026-07-13 |
| 前端 | auto（E2E anti-slop + targets compare） | 2026-07-13 |
| 产品 | 待正式姓名补签 | — |

## Screenshot capture

```powershell
cd frontend && npm run test:e2e -- fusheng-targets-screenshot
node scripts/compare-live-targets.mjs
```

Output: `docs/reports/live-targets-latest/live-{bazi,ziwei,report-toc}.png`

Compare against frozen: `docs/design/targets/{bazi,ziwei,report-toc}.png`

---

**R071 / R085 / R103 #3：** 结构 15/15 ☑；产品姓名行待补签后 R107 可勾。
