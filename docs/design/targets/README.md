# 浮生 · 设计截图门禁（F1-7 / T014）

| 字段 | 内容 |
|------|------|
| **版本** | targets-1.0 |
| **日期** | 2026-07-12 |
| **任务** | F1-7 · T014 |
| **样张来源** | [`../skin-preview.html`](../skin-preview.html) §11 八字 · §12 紫微 · §09 卷目 |

> **说明**：打磨期 W2–W3 门禁截图。实机页面达标后（T015–T023）可用 Playwright 对 `/new/bazi`、`/new/ziwei`、`/report` 重拍替换。

---

## 冻结文件

| 文件 | 来源节 | 用途 |
|------|--------|------|
| `bazi.png` | skin-preview `#layout-bazi` | 八字母版 A 布局门禁 |
| `ziwei.png` | skin-preview `#layout-ziwei` | 紫微方盘纯色 Hero 门禁 |
| `report-toc.png` | skin-preview `#volumes` | 六卷+跋 卷目 IA 门禁 |

**重生成命令**（仓库根目录）：

```powershell
# 推荐（Python playwright，已验证）
python scripts/capture_design_targets.py

# 或 Node（需 frontend npm run install:e2e）
node scripts/capture-design-targets.mjs
```

---

## 防丑五问（负责人签字）

| # | 问题 | bazi | ziwei | report-toc |
|---|------|:----:|:-----:|:----------:|
| 1 | 首屏是否只有一个视觉主角？ | ☐ | ☐ | ☐ |
| 2 | 是否只有纸 + 内容白两级底？ | ☐ | ☐ | ☐ |
| 3 | 铜色是否只在 1 CTA + KPI + active 导航？ | ☐ | ☐ | ☐ |
| 4 | 首屏是否是数字/盘面而非大段叙述？ | ☐ | ☐ | ☐ |
| 5 | 遮住中文标题后截图是否仍能认出浮生？ | ☐ | ☐ | ☐ |

**签字**

| 角色 | 姓名 | 日期 | 备注 |
|------|------|------|------|
| 设计 | （待签） | 2026-07-12 | skin F1-6/T009 后初冻 · PNG 已生成 |
| 产品 | | | |
| 前端 | | | |

---

## 相关文档

- [`handbook-bazi-layout.md`](handbook-bazi-layout.md) — 八字像素细则
- [`FUSHENG-DESIGN-MASTERPLAN.md`](../FUSHENG-DESIGN-MASTERPLAN.md) — 色板/字体定案
- [`FUSHENG-EXECUTION-PRIORITY.md`](../../plan/FUSHENG-EXECUTION-PRIORITY.md) — T014 任务
