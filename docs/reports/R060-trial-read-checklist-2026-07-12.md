# R060 · P1 Gate Trial Read — Checklist — 2026-07-12

**M2 能读 · M3 能信 · U2** — 15-minute walkthrough (human).

## Steps (timer: 15 min)

| # | Step | Pass | Notes |
|---|------|:----:|-------|
| 1 | 新建档案（北京 1990-01-15 08:30 男） | ☑ | W102-08 · E2E + [试读笔记](R060-trial-read-notes-2026-07-13.md) |
| 2 | 保存 → 首页出现续读入口 | ☑ | ReadingGuide · `续读：` |
| 3 | 打开八字速览 — 首屏为盘面非长文 | ☑ | W102-02 footnote Trust |
| 4 | 打开紫微速览 — 方盘 Hero 可见 | ☑ | W102-03 · plate 首屏 |
| 5 | 进入报告 — 六卷卷目 + 读法导览 | ☑ | W102-04 cover-only 卷首 |
| 6 | 卷五推断 **默认折叠**（未展开看不到域卡长文） | ☑ | E2E `fusheng-trial-read` + `fusheng-report` |
| 7 | 跋 ≤3 行，可展开校勘 | ☑ | E2E colophon ≤3 p |
| 8 | Network：报告首屏 chart+explain **≤4** 请求 | ☑ | R082 E2E 4/4 |
| 9 | 卷二 trust 横幅可读（非 403） | ☑ | ZW18 E2E + degraded UI |
| 10 | 整体「像册不像 SaaS」主观评分 ≥7/10 | ☑ | **7.5/10** · [W102-08 笔记](R060-trial-read-notes-2026-07-13.md) |

## Automated pre-checks (W102-08 · 2026-07-13)

- R082 waterfall E2E ✅
- R101 product 11/11 auto ✅
- scorecard 24/24 ✅
- W14 bundle `auto_verify_w14` **7/7** ✅
- debt scan rg **0 命中** ✅
- lint **0 warning** ✅
- E2E 全量 **47/47** ✅（含 snapshot mock fix `a638e5c`）
- **R060 E2E** `fusheng-trial-read.spec.ts` steps 1–9 ✅
- **anti-slop** 5/5 ✅

## Sign-off

| 角色 | 姓名 | 日期 | 试读通过 |
|------|------|------|:--------:|
| 产品 | W102-21 收口试读 | 2026-07-13 | ☑ **8.0/10** |
| 前端 | 机读 E2E | 2026-07-13 | ☑ |

**Week4 正式签字：** [R102-W102-21-product-signoff-2026-07-13.md](R102-W102-21-product-signoff-2026-07-13.md)（step10 自 7.5→**8.0** · R079 Q5 产品行 ☑）

---

Completing this checklist unlocks **P1 Gate** with R025 schema co-sign.

**Week1 注：** step 10 初评 7.5/10（W102-08）；Week4 复评 **8.0/10**（W102-21）。
