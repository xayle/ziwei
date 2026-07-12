# 紫微页布局目标说明（handbook A5 · 母版 A）

| 字段 | 内容 |
|------|------|
| **版本** | target-ziwei-1.0 |
| **日期** | 2026-07-12 |
| **任务** | F1-3 · T012 |
| **页面** | `/new/ziwei` · `FushengZiweiView.vue` |
| **母版** | Plate-Centric（方盘 Hero） |
| **对照样页** | [`../skin-preview.html`](../skin-preview.html) §12 `#layout-ziwei` |
| **截图门禁** | [`ziwei.png`](ziwei.png) |

---

## 1. 设计目标

| 目标 | 验收 |
|------|------|
| 方盘即首屏主角 | 方盘区 ≥60% 宽、≥50% 首屏高（桌面） |
| 纯色底 | `--surface` 无 gradient |
| 无双标题 | 无 `PageHead`；壳篇题「紫微 · 卷四」 |
| 深度三档 | 速览 / 结构 / 深读，默认速览 |
| degraded 必显 | `trust_level=degraded` 横幅或朱批行 |

---

## 2. 桌面布局（≥960px · 1120px 内容区）

```text
Main max-width 1120px
├── [无 PageHead]
├── SummaryStrip（可选 KPI：命宫主星、格局 tier）
├── Grid
│   ├── 左/主 方盘 Hero FushengZiweiPlate   min-h 360px  宽 ≥60%
│   └── 右栏 宫位解释 / 飞星摘要             sticky optional
├── EngineTrustPanel compact
└── 深度切换 + PalaceAnalysisGrid（深读）
```

### 2.1 方盘区

| 元素 | 数值 |
|------|------|
| 背景 | `var(--surface)` 纯色 |
| 宫格线 | `1px var(--border-md)` |
| 宫名 | `--font-ui` 11px 雾棕 |
| 主星 | `--font-display` 14–16px |
| 网格 | 4×4 标准方盘（中宫 2×2） |

### 2.2 禁止

- `linear-gradient` 铺底
- 青绿/紫粉 section 底
- 顶栏 + PageHead + 色块标题三层叠

---

## 3. 平板 / 移动

| 断点 | 变更 |
|------|------|
| &lt;960px | 方盘全宽置顶；右栏下移 |
| 375px | 方盘区块内横滚可接受；**页级**无横滚 |

---

## 4. 运限页（卷三）

`/new/ziwei/timeline` 另见 F5-4；本 handbook 仅本命方盘工作台。

---

## 5. 关联

- 执行：EXECUTION-PRIORITY T051 · INTEGRATED F5-3
- 引擎：`docs/design/ziwei/`
