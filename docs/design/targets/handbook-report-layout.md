# 报告页布局目标说明（handbook C · 母版 C）

| 字段 | 内容 |
|------|------|
| **版本** | target-report-1.0 |
| **日期** | 2026-07-12 |
| **任务** | F1-2 · T011 |
| **页面** | `/report` · `ReportView.vue`（F4 重构） |
| **母版** | Volume-Centric（连续阅读） |
| **对照样页** | [`../skin-preview.html`](../skin-preview.html) §09 `#volumes` |
| **截图门禁** | [`report-toc.png`](report-toc.png) |

---

## 1. 设计目标

| 目标 | 验收 |
|------|------|
| 像翻私人辑录，不像 SaaS 章节列表 | 卷目用语文卷名，无「四维分析」旧章 |
| 一屏一锚 | 首屏见卷目或当前卷封，非五层标题叠 |
| 连续阅读 | 单 scroll 六卷+跋；卷间 `32px` 间距 |
| 推断收束 | 卷五域卡默认折叠；badge「推断」 |
| 校勘最小 | 跋 ≤3 行；iztro/wenmo 在 expandable 脚注 |

---

## 2. 卷目 IA（冻结）

| id | 标签 | 首屏角色 |
|----|------|----------|
| preface | 卷首 | ReadingGuide + disclaimer |
| vol1 | 卷一·命之根 | 八字 pillars/geju |
| vol2 | 卷二·业之象 | relations + shensha |
| vol3 | 卷三·运之波 | dayun/liunian 分节 |
| vol4 | 卷四·宫之图 | ziwei 方盘摘要 |
| vol5 | 卷五·事之理 | domains fact+inference |
| vol6 | 卷六·问书 | 手动 LLM，默认折叠 |
| colophon | 跋·校勘 | ColophonFootnote |

---

## 3. 桌面布局（≥960px · max-width 1280px）

```text
Shell 篇题：报告 · 六卷辑录
├── ReportChapterNav（左 sticky 或顶卷目条）  宽 240px 可选
└── ReportBody max-width 1280px
    ├── 卷首 preface
    ├── vol1 … vol6（VolumeSection ×6）
    └── colophon（跋 expandable）
```

### 3.1 尺寸

| 元素 | 数值 |
|------|------|
| 卷名 | `--font-display` · `18–20px` |
| 节标题 | `--font-ui` · `14px` 雾棕 |
| 正文 | `--font-ui` · `14px` 墨 |
| 卷间距 | `32px`（`--sp-8`） |
| 节间距 | `24px`（`--sp-6`） |
| 典籍左线 | `3px --brand-gold` |
| 朱批缺失 | `3px --brand-cinnabar` 单行 |

---

## 4. 移动（375px）

| 变更 | 说明 |
|------|------|
| 卷目 | 顶 horizontal scroll 或折叠抽屉 |
| 无页级横滚 | 正文折行；表格可区块内横滚 |
| 卷名 | 保持 display 栈，不缩小至 &lt;16px |

---

## 5. 请求预算

报告页 ≤4 HTTP：`archive-bundle` + `bazi explain/batch` + `ziwei explain/batch`（或并入 bundle）。

---

## 6. 关联

- 数据层：`frontend/src/types/life-volume.ts` · `buildLifeVolumes.ts`（T025）
- 执行：INTEGRATED §5.7 F4 · EXECUTION-PRIORITY T036–T048
