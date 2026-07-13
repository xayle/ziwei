# 浮生 · 八字页改版设计（先设计、后实装）

| 字段 | 内容 |
|------|------|
| **版本** | bazi-page-design-1.2 |
| **日期** | 2026-07-13 |
| **状态** | **P1–P4 已实装 · v1.2 完成** |
| **页面** | `/new/bazi` · `NewBaziView.vue` |
| **上位** | [`FUSHENG-MINIMAL-GUOFENG-DESIGN.md`](./FUSHENG-MINIMAL-GUOFENG-DESIGN.md) · [`FUSHENG-ART-FOUNDATION.md`](./FUSHENG-ART-FOUNDATION.md) |
| **布局手册** | [`targets/handbook-bazi-layout.md`](./targets/handbook-bazi-layout.md) |
| **样张** | [`mockups/06-bazi-self-check-target.html`](./mockups/06-bazi-self-check-target.html) · [`mockups/07-bazi-page-layout-target.html`](./mockups/07-bazi-page-layout-target.html) · [`mockups/08-bazi-cover-spread-target.html`](./mockups/08-bazi-cover-spread-target.html) |
| **线框** | [`mockups/02-bazi-trust.drawio`](./mockups/02-bazi-trust.drawio) |

---

## 〇、原则

> **先定章法与区块顺序，再动 Vue/CSS。**  
> 八字页主角永远是 **六柱界画**；校勘是 **格物层脚注**，不是第二块 Dashboard。

| 约束 | 说明 |
|------|------|
| 纸墨两境 | 纸 `#f5f0e6` 外缘 → 白 `#fffaf5` 单块内容区 |
| 读法三层 | 格物（盘+校勘）→ 引经（卷二/深读典籍）→ 余论（推断，默认折叠） |
| 数据边界 | Trust 仅 `useEngineTrustDisplay` + `EngineTrustPanel` |
| 分阶段 | P1→P4 独立验收，禁止一次改完全页 |

---

## 一、已决事项（v1.1）

| # | 问题 | **决议** |
|---|------|----------|
| D1 | KPI 五格（SummaryStrip） | **速览隐藏**；卷封一行 meta 已含日主·格局·用神；**结构档**起显示五格，数字 `--brand-gold-dark` |
| D2 | 卷二 vs 校勘重复 | **卷二固定两行摘要**（干支关系 + 神煞）；刑冲细目、四柱细目 **只在校勘折叠区** |
| D3 | 速览校勘 | **保留一行** `<details>`「校勘提示（N 项）」；摘要 ≤2 条 + 尾注「切至结构查看全部」；**不展示** provenance 表 |
| D4 | 登记行文案 | **主句人话 + 技术备注折叠**（见 §2.5） |
| D5 | 右侧关系卡 | **速览**仅流日卡；**结构/深读**显示 `BaziStructuralRelations` **摘要 ≤4 条**；完整表只在校勘 |

---

## 二、整页布局规划

### 2.1 区块 ID 与纵向顺序（冻结）

```text
[B0] Shell 顶栏          — 篇题「八字 · 春 · 一命之枢」（已有）
[B1] 卷封带              — VolumeHead 瘦身版（P2）
[B2] 口径条              — 单行 caliber-banner，可折叠（P2）
[B3] 提示条              — 缓存/时辰 advisory，单行（已有）
[B4] 深度切换            — 速览 | 结构 | 深读（P3 改 underline）
[B5] 主 Grid             — 六柱 Hero + 右栏（P2 去嵌套卡）
[B6] 格物 · 校勘脚注     — EngineTrustPanel register（P1）
[B7] 卷二 · 业之象       — 两行登记（P1 文案收敛）
[B8] 格局双轨对照        — 有数据才显示（结构档）
[B9] 卷一 · 命之根       — AnalysisPanel（深读档）
[B10] 大运叙事           — 按需加载（深读档）
```

**间距：** 区块间 `--sp-6`（24px）；Grid 内 `--sp-4`（16px）。

### 2.2 三档布局对照（桌面 1120px）

#### 速览（默认 · 认盘）

```text
┌──────────────────────────────────────────────────────────────┐
│ [B1] 程安东 · 1990/06/17  癸丑·偏财格·用神木土  [档案][报告] │
│ [B2] 真太阳时未启用 · 子时日界寿星…                    [▼]  │
│ [B4]   速览  │  结构  │  深读          ← underline 界画     │
├────────────────────────────┬─────────────────────────────────┤
│ [B5] 六柱表（主表行）     │ 流日卡（摘要）                   │
│      无藏干贡献行         │                                 │
├────────────────────────────┴─────────────────────────────────┤
│ [B6] ▸ 校勘提示（3 项）  ← 折叠；展开 ≤2 条 + 「结构档全部」 │
└──────────────────────────────────────────────────────────────┘
  ✗ 无 KPI 五格 · ✗ 无卷二 · ✗ 无校勘全表 · ✗ 无深读
```

#### 结构（核对引擎）

```text
┌──────────────────────────────────────────────────────────────┐
│ [B1][B2][B4] 同上                                            │
│ [B5′] KPI 五格（铜色数字）← 结构档新增                       │
├────────────────────────────┬─────────────────────────────────┤
│ 六柱表 + 藏干/细目行      │ 流日卡 + 关系摘要（≤4 条）       │
├────────────────────────────┴─────────────────────────────────┤
│ [B6] 格物 · 校勘脚注（完整 register · provenance 默认展开）  │
├──────────────────────────────────────────────────────────────┤
│ [B7] 卷二 · 业之象 — 干支关系 · 神煞（各一行，无重复表）     │
│ [B8] 格局双轨对照（可选）                                    │
└──────────────────────────────────────────────────────────────┘
  ✗ 无深读手风琴
```

#### 深读（读辞）

```text
  结构档全部内容
       +
┌──────────────────────────────────────────────────────────────┐
│ [B9] 卷一 · 命之根 — AnalysisPanel（典籍/引擎/推断）         │
│      推断层默认折叠                                          │
│ [B10] 大运叙事 — 按钮触发加载                                │
└──────────────────────────────────────────────────────────────┘
```

### 2.3 首屏预算（1920×1080）

| 档位 | 首屏 1/3 必须可见 | 允许滚出 |
|------|-------------------|----------|
| 速览 | 六柱主表、深度切换、卷封一行 | 校勘折叠、全部脚注 |
| 结构 | + KPI 五格顶缘、校勘眉题 | provenance 表下半、卷二 |
| 深读 | 同结构 | 手风琴全文 |

**首屏禁止（全档）：** 粉红 Trust 块、三层 CodexPanel 嵌套、速览下 KPI 五格。

### 2.4 主 Grid 规格

| 项 | 桌面 ≥960px | 平板 / 移动 |
|----|-------------|-------------|
| 列比 | `1.45fr / 0.75fr` | 单列，六柱置顶 |
| 左列 min | 640px（表可横滚） | 100% 宽，`overflow-x: auto` |
| 右栏 sticky | `top: 88px`（结构档） | 取消 sticky |
| 日柱列 | `rgba(240,224,199,.35)` 淡铜底 | 同 |

### 2.5 移动布局（≤640px）

```text
卷封 → 口径（折叠）→ 深度切换（全宽三钮 44px 高）
→ 六柱表（可横滚）→ 流日卡
→ [结构] KPI 2×2+1
→ 校勘脚注（provenance 改堆叠行，非宽表）
→ 卷二两行 → 深读手风琴
```

| 规则 | 说明 |
|------|------|
| 页级 | 禁止整体横向滚动 |
| 表 | 仅六柱表容器可横滚 |
| 校勘表 | `<640px` 时 provenance 四列改 **标签:值** 堆叠行 |

---

## 三、内容归属矩阵（防重复 · 冻结）

| 数据 | 主展示位 | 次展示 | 禁止 |
|------|----------|--------|------|
| 四柱干支 | 六柱表 | — | 校勘重复表 |
| 藏干/贡献 | 六柱细目行（结构+） | — | 右侧再开全表 |
| 刑冲合害 **摘要** | 卷二 一行 | 右侧关系卡 ≤4 条 | 三处全文 |
| 刑冲合害 **细目** | 校勘折叠 | — | 卷二、右侧 |
| 神煞 **摘要** | 卷二 一行 | — | 校勘摘要行重复 |
| 神煞/空亡/藏干 **细目** | 校勘「四柱细目」 | — | 右侧 BaziStructuralRelations 全表 |
| missing / provenance | 校勘 | 速览 ≤2 条摘要 | alert 色块 |
| 格局/用神 KPI | 卷封 meta（速览） | KPI 五格（结构） | 速览五格横条 |
| 典籍解读 | 深读 AnalysisPanel | — | 结构档首屏 |

---

## 四、格物 · 校勘脚注（P1 详规）

### 4.1 定位

| 项 | 值 |
|----|-----|
| 区眉题 | **格物 · 校勘脚注** |
| 区内眉题 | **引擎校验 · 跋前脚注** |
| 读法层 | L1 格物 |
| 位置 | [B6] 紧贴 [B5] 下、[B7] 上 |

### 4.2 视觉语法

```text
┌─ trust-footnote（白底 · 1px --border-md · 无阴影）─────────────┐
│ 引擎校验 · 跋前脚注                                            │
├────────────────────────────────────────────────────────────────┤
│ ! 缺失  刑冲摘要                                               │
│ △ 校勘  出生时刻接近时辰交界（±15 分）                         │
│         └─ 备注  near_shichen_boundary  （11px 雾色，可折叠）   │
│ ✓ 核对  整体置信度：中等                                       │
├─ details[open] 可信度分层 ─────────────────────────────────────┤
├─ details 双轨 / 四柱细目 / 旺衰 / 刑冲细目 / … ────────────────┤
└────────────────────────────────────────────────────────────────┘
```

### 4.3 登记行类型

| 类型 | 图标 | 徽章 | 左线 | 主句示例 |
|------|------|------|------|----------|
| 核对 | ✓ | 核对 | `--border-md` | 整体置信度：中等 |
| 校勘 | △ | 校勘 | `--brand-gold` | 出生时刻接近时辰交界（±15 分） |
| 缺失 | ! | 缺失 | `--brand-cinnabar` | 刑冲摘要（引擎未返回） |

### 4.4 文案规则（人话 + 备注）

| 引擎信号 | 主句（用户可见） | 备注（折叠/secondary） |
|----------|------------------|------------------------|
| `near_shichen_boundary` | 出生时刻接近时辰交界（±15 分） | 原因码 + 原始 warning |
| `missing clash_summary` | 刑冲摘要（引擎未返回） | 字段名 |
| `confidence medium` | 整体置信度：中等 | L0 / dual 等技术码 |
| provenance note | 不直接作主句 | 缩略显示于表「备注」列 |

实现：`buildEngineTrustDisplay` 增 `formatTrustLineHuman()`（P1 可先做 missing/validation 映射，provenance 备注仍 raw）。

### 4.5 折叠分组（结构档 / 深读档）

| 分组 | 默认 | 速览 |
|------|------|------|
| 摘要登记行 | 展开 | 折叠入口内 ≤2 条 |
| 可信度分层 | 展开 | **隐藏** |
| 双轨口径 | 折叠 | 隐藏 |
| 四柱细目 | 折叠 | 隐藏 |
| 旺衰因子 | 折叠 | 隐藏 |
| 刑冲合害细目 | 折叠 | 隐藏 |
| 结构摘要 / 流日 / iztro | 折叠 | 隐藏 |

### 4.6 速览交互（D3）

```text
▸ 校勘提示（3 项）
    展开后：
    ! 缺失  刑冲摘要
    △ 校勘  出生时刻接近时辰交界（±15 分）
    ─────────────────────────────
    切至「结构」查看全部校勘与可信度分层
```

不自动切换档位；尾注可点击切换 `depth = 'structure'`（P1 可选增强）。

---

## 五、卷封与 KPI（P2 预览 · 与 P1 衔接）

### 5.1 卷封带 [B1]

| 元素 | 速览 | 结构 |
|------|------|------|
| 姓名 · 日期 | ✓ | ✓ |
| 一行 meta | 日主·格局·用神·强弱（truncate） | 同左或略长 |
| CTA | 查看档案（ghost）· 进入报告（primary 唯一铜钮） | 同 |
| VolumeHead 双层标题 | **移除** shell 外重复（P2） | |

### 5.2 KPI 五格 [B5′]

| 档位 | 行为 |
|------|------|
| 速览 | **不渲染** SummaryStrip |
| 结构 / 深读 | 渲染；`value` 用 `--brand-gold-dark`；位于 Grid **上方** 单行 |

---

## 六、分阶段实装路线图

```text
P1 校勘脚注 ──→ P2 卷封+盘面 ──→ P3 深度切换 ──→ P4 深读收敛
  1–2d           1–2d              0.5d            1d
```

| 阶段 | 范围 | 文件 | 验收 |
|------|------|------|------|
| **P1** | [B6][B7] 校勘 register、卷二两行、区块顺序、内容矩阵、速览折叠 | `EngineTrustPanel` `NewBaziView` `fusheng-page.css` `buildEngineTrustDisplay` | §8.1 + 样张 06 |
| **P2** | [B1][B2][B5] 卷封瘦身、去 CodexPanel 嵌套、KPI 档位化 | `VolumeHead` `NewBaziView` `BaziReferenceTable` | 样张 07 + 首屏截图 |
| **P3** | [B4] depth underline；SummaryStrip 铜色 | `fusheng-page.css` `ProfileTabNav` 同款 tab 语法 | 375/1920 切换截图 |
| **P4** | [B9][B10] 深读下沉、推断默认折叠、大运按需 | `AnalysisPanel` `NewBaziView` | E2E 深读路径 |

**报告 / 紫微：** 维持 `layout="default"` 至 P1–P2 稳定后再评估统一 register。

---

## 七、组件映射

| 区块 | 组件 | Props / 样式 |
|------|------|----------------|
| [B1] | `VolumeHead` | P2 瘦身 |
| [B5] | `BaziReferenceTable` + 右栏卡片 | P2 单块白面 |
| [B5′] | `SummaryStrip` | `v-if="depth !== 'overview'"` |
| [B6] | `EngineTrustPanel` | `layout="register"` |
| [B7] | `CodexPanel` 或行登记 | 两行 `fs-codex-line` |
| [B9] | `AnalysisPanel` | 深读档 |

---

## 八、验收标准

### 8.1 P1（校勘）

- [x] 无 alert 铺底；登记行三色左线正确
- [x] 结构档：校勘在盘面下、卷二上
- [x] 速览：仅折叠提示；≤2 摘要 + 结构档引导
- [x] 卷二仅两行；刑冲/四柱细目不出现在卷二
- [x] 对照 [`06-bazi-self-check-target.html`](./mockups/06-bazi-self-check-target.html)
- [x] E2E `bazi-trust-overview` / `bazi-layer-trust` 仍绿

### 8.2 整页（P1–P4 完成后）

- [x] 对照 [`07-bazi-page-layout-target.html`](./mockups/07-bazi-page-layout-target.html) 三档
- [ ] `docs/design/audit-screenshots/target-bazi-*.png`（需本地截图）
- [x] `npm run test` + E2E 八字相关（城市 mock 已修复）

---

## 九、评审记录

| 日期 | 版本 | 结论 |
|------|------|------|
| 2026-07-13 | 1.0 | 初稿 + 样张 06 |
| 2026-07-13 | **1.1** | 并入评估意见；D1–D5 已决；内容矩阵；三档布局；分阶段路线图 |
| 2026-07-13 | **1.2** | 补全 P2–P4 详规、区块规格表、状态机、文案映射、E2E 影响、现机迁移 |
| 2026-07-13 | **1.2 实装** | P1–P4 全部落地：`NewBaziView` · `EngineTrustPanel` · `fusheng-page.css` |

**实装完成。** 验收对照样张 06/07/08 与 `npm run test` / `npm run test:e2e`。

---

## 十一、区块规格表（逐块冻结）

### 11.1 总览

| ID | 名称 | 组件 | 档位可见 | CSS 类（目标） |
|----|------|------|----------|----------------|
| B0 | Shell 顶栏 | `NewAppShell` | 全档 | 已有 |
| B1 | 卷封带 | `VolumeHead` → `bazi-cover` | 全档 | P2 新增 |
| B2 | 口径条 | `caliber` details | 全档 | `fs-caliber-banner` |
| B3 | 提示条 | advisory `<p>` | 条件 | `fs-advisory` / `fs-hint` |
| B4 | 深度切换 | 三钮 | 全档 | `archive-tabs` 同款 |
| B5 | 主 Grid | table + aside | 全档 | `bazi-hero` |
| B5′ | KPI 五格 | `SummaryStrip` | 结构+深读 | `fs-kpi-strip` |
| B6 | 校勘脚注 | `EngineTrustPanel` | 速览折叠+结构+深读 | `bazi-self-check` |
| B7 | 卷二 | 两行登记 | 结构+深读 | `bazi-vol2` |
| B8 | 双轨对照 | `DualTrackTable` | 结构+（有数据） | `bazi-dual-track-block` |
| B9 | 深读解读 | `AnalysisPanel` | 仅深读 | `bazi-layer-explain` |
| B10 | 大运叙事 | 按需按钮 | 仅深读 | `bazi-load-dayun` |

### 11.2 [B1] 卷封带（P2）

对齐档案页 `archive-cover` 语法，但 **不 sticky**（八字页整页滚动）。

```text
┌─ bazi-cover（白底单块 · 底部分界 1px）────────────────────────────┐
│ 春 · 一命之枢          ← 11px 铜左线眉题（volumeId=vol1）        │
│ 程安东 · 1990/06/17    ← display 22–28px                         │
│ 癸丑 · 偏财格 · 用神木土 · 中和  ← 12px 雾色 meta（topSummary）   │
│                              [查看紫微 ghost] [进入报告 primary] │
└──────────────────────────────────────────────────────────────────┘
```

| 项 | 规格 |
|----|------|
| padding | `clamp(20px, 3vw, 32px) clamp(20px, 3vw, 40px) 16px` |
| 与 B2 间距 | `--sp-4` |
| 标题 | 档案 label 去日期重复（同 Profile 卷封规则） |
| CTA | 全页唯一铜色实心钮 =「进入报告」；「查看紫微」改 ghost 文字链亦可 |
| 移除 | `fs-page-head` 大卡片阴影；与 Shell 篇题不重复 h1 |

### 11.3 [B2] 口径条（P2）

| 项 | 规格 |
|----|------|
| 默认 | 单行 truncate，`fs-caliber-banner` |
| 展开 | `<details>` 显示完整 caliberBanner + timeWarnings 列表 |
| 字号 | 12px · `--brand-mist` |
| testid | 保留 `bazi-caliber-banner` |

### 11.4 [B3] 提示条

| 类型 | 样式 | 条件 |
|------|------|------|
| 缓存复用 | `fs-hint fs-hint--cache` | `isCacheValid` |
| 时辰/历史时区 | `fs-advisory fs-advisory--cinnabar` 左线 | `timeWarnings.length` |
| 加载失败 | `ResultStateCard` 替代整页 B5–B10 | `error` |

### 11.5 [B4] 深度切换（P3）

**语法：** 与档案 `ProfileTabNav` / `archive-tabs` 一致，**禁止** pill 圆角容器。

| 项 | 值 |
|----|-----|
| 容器 | `border-bottom: 1px solid var(--border-md)` |
| 按钮 | `min-height 40px`；active = 铜 underline 2px |
| 位置 | Grid **上方**（B5′ 与 B5 之间：B4 → B5′? → B5） |

**顺序冻结：** B1 → B2 → B3 → **B4** → B5′（结构+）→ B5 Grid → B6…

| 档位 | 切换时行为 |
|------|------------|
| → 结构 | 无额外请求；展示 B5′ B7 B8 B6 全文 |
| → 深读 | 触发 `loadPageExplain`（已有 watch）；滚动 optional 至 B9 |
| → 速览 | 隐藏 B5′ B7 B8 B9 B10；B6 变折叠 |

持久化：`depth` 存 `sessionStorage` key `fusheng.bazi.depth`（P3 可选）。

### 11.6 [B5] 主 Grid · 六柱 Hero（P2）

**目标：** 单块 `bazi-spread` 白面，内部分两列，**去掉 CodexPanel 套 CodexPanel**。

```text
┌─ bazi-spread（--surface · 1px border-md）─────────────────────────┐
│ ┌─ bazi-hero__chart ─────────┐ ┌─ bazi-hero__aside ────────────┐ │
│ │ BaziReferenceTable         │ │ BaziLiuriTodayCard            │ │
│ │ · 日柱列淡铜底             │ │ [结构+] BaziStructuralRelations│ │
│ │ · 结构档 +藏干行           │ │   mode="summary" maxItems=4   │ │
│ └────────────────────────────┘ └───────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

| 子区 | 速览 | 结构 |
|------|------|------|
| 表 · 主行 | ✓ | ✓ |
| 表 · 藏干/细目行 | ✗ | ✓ |
| 流日卡 | ✓ 摘要 | ✓ |
| 关系卡 | ✗ | ✓ ≤4 条 |

**testid：** 保留 `bazi-layer-structure` 在外层 spread。

### 11.7 [B7] 卷二 · 业之象（P1）

| 行 | 数据源 | 格式 |
|----|--------|------|
| 干支关系 | `formatRelationsSummaryText(result)` | `**干支关系** — {text}` |
| 神煞摘要 | `formatShenshaSummaryText(result)` | `**神煞摘要** — {text}` |

- 不用 `CodexPanel` 大标题区；用 `bazi-vol2` + 左线 section 眉题
- 无数据时显示「暂无关系摘要」单行雾色，不隐藏区块
- testid：保留 `bazi-vol2-block`

### 11.8 [B8] 格局双轨对照

- 条件：`depth !== 'overview' && dualTrackReference.length`
- 组件：`DualTrackTable variant="reference"`
- 位置：B7 之下；与校勘内「双轨口径」不重复——**B8 给用户读，校勘给引擎字段**

### 11.9 [B9][B10] 深读（P4）

**B9 AnalysisPanel**

| layer | 左线 | 默认 |
|-------|------|------|
| classical 典籍 | `--brand-gold` 3px | 首块展开 |
| engine 引擎 | `--brand-mist` | 折叠 |
| heuristic 推断 | `--text-3` + badge | **全部折叠** |

区块眉题：**引经 · 卷一命之根**（与格物/卷二层级区分）

**B10 大运叙事**

- 仅 `depth === 'deep'`
- 默认按钮；不自动 `loadDayunNarratives`
- 加载态/错误：`fs-hint`；成功则追加 `AnalysisPanel` blocks

---

## 十二、页面状态机

```text
                    ┌─────────────┐
                    │  loading    │
                    │ ResultState │
                    └──────┬──────┘
                           │ success
              ┌────────────┴────────────┐
              ▼                         ▼
       ┌─────────────┐           ┌─────────────┐
       │  ready      │           │  error      │
       │  depth 三档 │           │ 重试按钮    │
       └─────────────┘           └─────────────┘
```

| 状态 | 可见区块 | 说明 |
|------|----------|------|
| `loadingBazi` | B1 可选 + ResultState compact | 不渲染空表 |
| `error` | B1 + ResultState 全幅 | action 重算 |
| `!result` | 同 error 或引导补档案 | 链 `/profile?reason=archive` |
| `ready` | 按档位表 | 正常 |

**空档案 / 无 birthDt：** 卷封仍显示；B5 区 ResultState「请先补全档案」。

---

## 十三、文案与人话映射（P1 工程清单）

### 13.1 缺失字段 → 主句

| 字段 key | 主句 |
|----------|------|
| `clash_summary` | 刑冲摘要（引擎未返回） |
| `combine_summary` | 合化摘要（引擎未返回） |
| `harm_summary` | 害破摘要（引擎未返回） |
| `hour_pillar` | 时柱（引擎未返回） |
| `geju_detail` | 格局细目（引擎未返回） |
| `flow_score` | 流日联动分（引擎未返回） |
| *其他* | `{中文或 key 空格化}` |

函数：`formatMissingFieldLabel`（已有）+ `formatTrustValidationLine`（新增）

### 13.2 校验行 → 主句 + 备注

| 模式 | 主句 | 备注 |
|------|------|------|
| `/置信度.*medium/i` | 整体置信度：中等 | 原串 |
| `/near_shichen/i` | 出生时刻接近时辰交界（±15 分） | 原因码 |
| `/双轨/` | 存在双轨口径差异 | 双轨 id |
| `/L0/` | — | 仅备注，不进主句 |
| 默认 | 原串去技术前缀 | — |

### 13.3 卷二摘要截断

| 字段 | max 长度 | 超出 |
|------|----------|------|
| relations summary | 120 字 | `…` |
| shensha summary | 120 字 | `…` |

使用现有 `truncateText` / `formatVol2Summary` 输出。

---

## 十四、现机 → 目标迁移对照

| 现机 `NewBaziView` | v1.2 目标 | 阶段 |
|--------------------|-----------|------|
| `VolumeHead` + `fs-page-head` 卡片 | `bazi-cover` 界画卷封 | P2 |
| `SummaryStrip` 速览常显 | `v-if="depth !== 'overview'"` | P1/P2 |
| `SummaryStrip` 在 B4 之前 | 移至 B4 之后、B5 之前 | P2 |
| `CodexPanel` 包表/流日/关系 | `bazi-spread` 单块 | P2 |
| `fs-depth-toggle` pill | `archive-tabs` | P3 |
| 校勘在 vol2 之后 | 校勘在 B5 下、B7 上 | P1 |
| 速览 trust 含 provenance | 速览仅 ≤2 行 + 引导 | P1 |
| `BaziStructuralRelations` 结构档全表 | `summary` 模式 ≤4 条 | P1 |
| vol2 CodexPanel 多行 | 两行登记 | P1 |

---

## 十五、样式 Token 与类名（新增 · P1–P3）

| 类名 | 用途 | 文件 |
|------|------|------|
| `.bazi-page` | 页根 grid gap | 已有 |
| `.bazi-cover` | B1 卷封 | `fusheng-page.css` P2 |
| `.bazi-spread` | B5 单块白面 | P2 |
| `.bazi-vol2` | B7 两行 | P1 |
| `.bazi-self-check` | B6 区眉题 | P1 已有 |
| `.bazi-depth-tabs` | B4（或复用 `.archive-tabs`） | P3 |
| `.trust-*` | 校勘登记 | P1 已有 |
| `.fs-kpi-strip__value` | 铜色数字 | P2/P3 |

**shell：** 八字页 **不** 使用 `shell--archive` 式内部滚动；保持 **document 滚动**。

---

## 十六、E2E / testid 影响（实装时需同步）

| testid | 现期望 | v1.2 变更 |
|--------|--------|-----------|
| `bazi-layer-summary` | 速览可见 | **结构档才可见** → 用例改断言或改点 B1 meta |
| `bazi-trust-overview` | 展开有 `provenance-section` | **移除** provenance；仅 missing/validation 行 |
| `bazi-vol2-block` | 结构档可见 | 不变 |
| `bazi-layer-trust` | 结构档 | 不变；位置变早 |
| `bazi-depth-toggle` | pill 按钮 | 选择器仍可用，类名变 |
| `bazi-layer-explain` | 深读 | 不变 |

**受影响文件：** `fusheng-bazi-ziwei.spec.ts`（trust overview）、`fusheng-anti-slop.spec.ts`、`fusheng-trial-read.spec.ts`

---

## 十七、分阶段验收清单（扩展）

### P2 卷封 + 盘面

- [ ] 速览首屏无 KPI 五格
- [ ] 单块 `bazi-spread`，无嵌套 CodexPanel
- [ ] 卷封 meta 一行可读；CTA 仅一铜钮
- [ ] 日柱列淡铜底
- [ ] 截图 `target-bazi-1920-hero.png`

### P3 深度切换

- [ ] underline tab 与档案页一致
- [ ] KPI 数字 `--brand-gold-dark`
- [ ] 375px segmented 全宽 44px

### P4 深读

- [ ] 推断层默认折叠
- [ ] 大运按需加载
- [ ] `fusheng-bazi-explain.spec.ts` 仍绿

---

## 十八、与紫微 / 报告对齐（后续）

| 页 | 校勘 layout | 卷封 | 深度切换 |
|----|-------------|------|----------|
| 八字 | register（P1） | bazi-cover（P2） | 三档 |
| 紫微 | register（P5 计划） | ziwei-cover | 三档 |
| 报告 | default + 跋 | report toc | 卷目 |

八字 P1–P2 稳定后再写 `FUSHENG-ZIWEI-PAGE-DESIGN.md` 引用本文件 §十一。

---

## 十九、样张与线框同步任务

| 资产 | 状态 | 动作 |
|------|------|------|
| `06-bazi-self-check-target.html` | v1.1 | ✅ |
| `07-bazi-page-layout-target.html` | v1.1 | ✅ |
| `08-bazi-cover-spread-target.html` | v1.2 | ✅ P2 卷封+spread |
| `02-bazi-trust.drawio` | 旧 | P1 后更新校勘位置 |

---

## 二十、相关链接

- [`handbook-bazi-layout.md`](./targets/handbook-bazi-layout.md)
- [`skin-preview.html`](./skin-preview.html) §06 · §11
- [`FUSHENG-ART-EXECUTION-PLAN-2026-07-13.md`](../plan/FUSHENG-ART-EXECUTION-PLAN-2026-07-13.md)
