# 八字页布局目标说明（handbook A5 · 母版 A）

| 字段 | 内容 |
|------|------|
| **版本** | target-bazi-1.2 |
| **状态** | S2 母版 A 已落地 · **布局 v1.2 见 [`FUSHENG-BAZI-PAGE-DESIGN.md`](../FUSHENG-BAZI-PAGE-DESIGN.md)** |
| **日期** | 2026-07-12 |
| **页面** | `/new/bazi` · `NewBaziView.vue` |
| **母版** | Chart-Centric（§2.6） |
| **对照样页** | [`../skin-preview.html`](../skin-preview.html) §11 `#layout-bazi` |
| **竞品参考** | Baguame 盘面优先 · ziwei.pub 信息密度 |

---

## 1. 设计目标（美术 + 规划）

| 目标 | 验收 |
|------|------|
| 首屏看见「盘」 | 六柱表顶部 1/3 视口内完整可见（1920×1080） |
| 不像后台 | 全页 flat 卡 ≤4 块；无彩色分区大框 |
| 可信但不吓人 | Trust 为白底脚注，非粉红 section |
| 专业深度可选 | 速览 / 结构 / 深读 三档，默认速览 |
| 宽屏能聚焦 | 内容区 `max-width: 1120px` 居中 |

---

## 2. 桌面布局（≥960px · 1120px 内容区）

```text
视口 1920px
├── Shell 全宽（纸底 + 微纹理）
│   └── Main max-width 1120px, margin auto, padding-x 28px
│       ├── [可选] PageHead — 建议弱化或移除（顶栏已有页名）
│       ├── 口径条 caliber-banner          h≈36px  单行
│       ├── SummaryStrip                     h≈56px  全宽
│       ├── Grid 主区                          gap 14px
│       │   ├── 左列 58%  六柱表 Hero        min-h 280px
│       │   └── 右列 42%  辅助栈              sticky top 88px
│       │       ├── 流日卡 LiuriTodayCard    flat
│       │       └── 关系卡 BaziStructural    flat
│       ├── 深度切换 depth-toggle            右对齐或贴主区顶
│       ├── Trust 脚注 EngineTrustPanel      compact, 白底
│       └── 解读 AnalysisPanel               手风琴 ×3
```

### 2.1 尺寸与间距

| 元素 | 数值 |
|------|------|
| 区块纵向间距 | `24px`（`--sp-6`） |
| 口径条 | `padding 8px 12px`；`font-size 12px`；可点击展开 |
| SummaryStrip | `padding 14px 18px`；KPI 间距 `24px` |
| 主 Grid | `grid-template-columns: 1.45fr 0.75fr`；`gap 14px` |
| 六柱表 | 最小宽 `640px`；列宽均分；**日柱列** `background: rgba(240,224,199,.35)` |
| 天干字号 | `28–32px` 衬线粗体；藏干 `≤40%` 主字号 |
| Trust 脚注 | `padding 12px 14px`；`font-size 12px`；`background #fff` |
| 解读手风琴 | 章间距 `16px`；典籍层左框 `3px --layer-classical-border` |

### 2.2 视线流（F 型）

1. 口径条（扫一眼）  
2. SummaryStrip KPI 数字（铜金）  
3. 六柱表天干地支（停留最久）  
4. 右侧流日 / 关系（补充）  
5. Trust 脚注（核对，可跳过）  
6. 解读（按需展开）

---

## 3. 平板（640–960px）

| 变更 | 说明 |
|------|------|
| Grid 改单列 | 六柱表全宽置顶 |
| 辅助卡 | 流日 + 关系 **横排两列** 或上下叠放 |
| SummaryStrip | 保持横排 wrap |
| sticky 取消 | 右列 `position: static` |

---

## 4. 移动（<640px · 375px 基准）

```text
├── 口径条（可折叠为一行 + chevron）
├── SummaryStrip  2×2 网格 + 第5项独占一行
├── 六柱表 Hero   100% 宽，允许横向滚动
├── 流日卡        全宽 flat
├── 关系卡        全宽 flat，默认可折叠
├── depth-toggle  全宽 segmented
├── Trust 脚注    全宽，表格改堆叠行
└── 解读          手风琴全宽
```

| 项 | 规则 |
|----|------|
| 页面 | **禁止** 整体横向滚动 |
| 六柱表 | **允许** `.pillar-grid { overflow-x: auto }` |
| 底栏导航 | 56px；主内容 `padding-bottom: 72px` |
| 触控 | 按钮/切换最小高 `44px` |

---

## 5. 深度切换与模块映射

| 用户档位 | 可见模块 | 隐藏/折叠 |
|----------|----------|-----------|
| **速览**（默认） | 口径条、SummaryStrip、六柱表主表、流日卡摘要、Trust 摘要行 | 藏干贡献、关系详情、解读全文 |
| **结构** | + 藏干行、关系卡、柱间细目 | 解读区仍折叠 |
| **深读** | + AnalysisPanel 三层手风琴 | — |

**禁止出现在 UI 的文案**：`L1` `L2` `L3` `L4`、`四层语法`、`引擎未覆盖字段（必明示）` 作大标题。

Trust 区标题改为：**引擎校验** 或 **核对脚注**（11px 全大写追踪字距）。

---

## 6. 组件皮肤对照（实现时 @ skin-preview）

| 组件 | 样页锚点 | 实现文件 |
|------|----------|----------|
| SummaryStrip | `#summary` | `SummaryStrip.vue` — value 改铜金 |
| 六柱表 | `#pillars` | `BaziReferenceTable.vue` — 日柱列底、去冷灰 |
| Trust 脚注 | `#trust` | `EngineTrustPanel.vue` — compact 白底 |
| 深度切换 | `#depth` | 新建或 `fusheng-page.css` `.fs-depth-toggle` |
| 解读三层 | `#depth` explain-block | `AnalysisPanel` 左边框样式 |

---

## 7. 与当前实机的差异清单（改版必改）

| # | 现状 | 目标 |
|---|------|------|
| 1 | `fs-layer--trust` 粉红底大框 | 白底脚注 `.trust-footnote` |
| 2 | `fs-layer__label` 显示 L1/L2 | 移除或 `aria-hidden` 仅开发 |
| 3 | PageHead + Shell 双层标题 | 二选一，建议留 Shell 页名 |
| 4 | 六柱表嵌在 structure 色块内 | 盘面 Hero 独立 `surface-2` 垫底 |
| 5 | SummaryStrip value 墨色 | value 用 `--brand-gold-dark` |
| 6 | 解读与结构同权重并列 | 解读下沉，默认折叠启发式 |

---

## 8. 验收截图清单

改版完成后在 `docs/design/audit-screenshots/` 存：

| 文件名 | 视口 |
|--------|------|
| `target-bazi-1920.png` | 1920×1080 全页 |
| `target-bazi-1920-hero.png` | 首屏裁切（含六柱表） |
| `target-bazi-375.png` | iPhone 375 全页 |
| `target-bazi-depth-structure.png` | 结构档展开态 |
| `target-bazi-trust.png` | Trust 脚注特写 |

对照 [`skin-preview.html`](../skin-preview.html) §05–§09 逐项目视比对。

---

## 9. 后续页面（规划预留）

| 页面 | 母版 | 备注 |
|------|------|------|
| 紫微 | A（方盘 ≥60%） | toolbar 落底部非右侧 |
| 合婚 | D 双 Chart | 参考 Baguame 并排 |
| 报告 | C | 另文 `handbook-report-layout.md` |
