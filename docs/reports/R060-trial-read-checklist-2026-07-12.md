# R060 · P1 Gate Trial Read — Checklist — 2026-07-12

**M2 能读 · M3 能信 · U2** — 15-minute walkthrough (human).

## Steps (timer: 15 min)

| # | Step | Pass | Notes |
|---|------|:----:|-------|
| 1 | 新建档案（北京 1990-01-15 08:30 男） | ☐ | |
| 2 | 保存 → 首页出现续读入口 | ☐ | ReadingGuide |
| 3 | 打开八字速览 — 首屏为盘面非长文 | ☐ | |
| 4 | 打开紫微速览 — 方盘 Hero 可见 | ☐ | |
| 5 | 进入报告 — 六卷卷目 + 读法导览 | ☐ | |
| 6 | 卷五推断 **默认折叠**（未展开看不到域卡长文） | ☑ | E2E `fusheng-trial-read` + `fusheng-report` |
| 7 | 跋 ≤3 行，可展开校勘 | ☐ | 人工目视 |
| 8 | Network：报告首屏 chart+explain **≤4** 请求 | ☑ | R082 E2E 4/4 |
| 9 | 卷二 trust 横幅可读（非 403） | ☑ | ZW18 E2E + degraded UI |
| 10 | 整体「像册不像 SaaS」主观评分 ≥7/10 | ☐ | |

## Automated pre-checks (pass 4 · 2026-07-13)

- R082 waterfall E2E ✅
- R101 product 11/11 auto ✅
- scorecard 24/24 ✅
- W14 bundle `auto_verify_w14` **7/7** ✅
- debt scan rg **0 命中** ✅
- lint **0 warning** ✅
- E2E 全量 **47/47** ✅
- **R060 E2E** `fusheng-trial-read.spec.ts` steps 1–9 ✅

## Sign-off

| 角色 | 姓名 | 日期 | 试读通过 |
|------|------|------|:--------:|
| 产品 | | | ☐ |
| 前端 | | | ☐ |

---

Completing this checklist unlocks **P1 Gate** with R025 schema co-sign.
