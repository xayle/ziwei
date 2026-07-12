# 浮生 UI 线框模板（Draw.io）

与 [**设计定案**](../FUSHENG-DESIGN-MASTERPLAN.md) 及 [**顺序执行清单**](../../plan/FUSHENG-EXECUTION-PRIORITY.md) 配套的低保真线框。

## 文件清单

| 文件 | 对应页面 | 用途 |
|------|----------|------|
| `01-profile-tabs.drawio` | `/profile` | 档案 Tab、双栏 KPI（F5-2） |
| `02-bazi-trust.drawio` | `/new/bazi` | 六柱 Hero + 卷二块 + 校勘脚注 |
| `03-report-cross.drawio` | `/report` | 六卷卷目 + 跋 advisory |
| `04-ziwei-timeline.drawio` | `/new/ziwei/timeline` | 卷三运限叙事（F5-4） |
| `05-ziwei-plate.drawio` | `/new/ziwei` | 方盘 Hero、纯色底（F5-3） |
| [`05-home-song-target.html`](05-home-song-target.html) | `/` | **首页 · 简约国风**（[`FUSHENG-MINIMAL-GUOFENG-DESIGN`](../FUSHENG-MINIMAL-GUOFENG-DESIGN.md)） |
| [`fusheng-home-song-aesthetic-mockup.png`](fusheng-home-song-aesthetic-mockup.png) | `/` | AI 概念稿（已废弃路线，仅作反例对照） |

## 如何打开

1. 安装 **Draw.io Integration**（`.vscode/extensions.json`）
2. 双击 `.drawio` 或右键 → **Open With… → Draw.io**
3. 可导出 PNG 放入 PR / 设计评审

## 配色对照（与 `variables.css` / MASTERPLAN §二 一致）

| 用途 | Token | 色值 |
|------|-------|------|
| 纸张底 | `--brand-paper` | `#f5f0e6` |
| 内容白 | `--surface` | `#fffaf5` |
| 铜金强调 | `--brand-gold` | `#b8894d` |
| 深墨文字 | `--brand-ink` | `#1a1410` |
| 缺失/双轨 | `--brand-cinnabar` | `#8b3a2a` |

**禁止**：语义绿黄 alert 铺底、铜金 gradient 按钮（见 RISK-ALERT R-02）。

## 协作约定

- 线框只描述 **信息层级与区块顺序**，不写最终文案
- 改线框后同步更新 `skin-preview.html` 对应节或 `targets/handbook-*.md`
- 高保真视觉以 [`skin-preview.html`](../skin-preview.html) + [`targets/`](targets/) 截图门禁为准
