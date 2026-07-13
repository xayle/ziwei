# 浮生 · 美术落地执行规划

| 字段 | 内容 |
|------|------|
| **版本** | art-exec-1.0 |
| **日期** | 2026-07-13 |
| **状态** | **P1+P2 实装 · P4 待 E2E signoff** |
| **美术真源** | [`../design/FUSHENG-ART-FOUNDATION.md`](../design/FUSHENG-ART-FOUNDATION.md) |
| **工程** | [`../guides/FUSHENG-FRONTEND-DEV.md`](../guides/FUSHENG-FRONTEND-DEV.md) |

---

## 〇、目标

把「简约国风 + 宋式章法」从文档/mockup **落到 Vue 实装**，且每阶段可验收、可回滚。

**不做：** 一次性大改全站皮肤；不加新装饰纹样。

---

## 一、阶段总览

```text
P0 冻结 ──→ P1 品牌壳 ──→ P2 首页 ──→ P3 卷页章法 ──→ P4 门禁
  (本文)      shell/logo    NewHome     bazi/report    signoff
```

| 阶段 | 产出 | 预估 | 依赖 |
|------|------|------|------|
| **P0** | 美术真源 + 样张 + LOGO v2 | ✅ 已完成 | — |
| **P1** | Shell / favicon / 报告封面统一新标识 | ✅ 2026-07-13 | P0 |
| **P2** | `NewHomeView` = 品牌首页（非档案） | ✅ gate + 卷目登记 | P1 |
| **P3** | 命盘/报告页应用行界与两级纸面 | 2–3d | ✅ 首版实装 |
| **P4** | 截图门禁 + anti-slop 回归 | 0.5d | P3 |

---

## 二、P0 · 冻结（已完成）

- [x] [`FUSHENG-ART-FOUNDATION.md`](../design/FUSHENG-ART-FOUNDATION.md) — 色彩/间距/版心/章法
- [x] [`FUSHENG-MINIMAL-GUOFENG-DESIGN.md`](../design/FUSHENG-MINIMAL-GUOFENG-DESIGN.md) — 产品定案
- [x] [`FUSHENG-BRAND-LOGO-v2.md`](../design/FUSHENG-BRAND-LOGO-v2.md) + SVG/PNG
- [x] [`mockups/05-home-song-target.html`](../design/mockups/05-home-song-target.html) — 首页样张
- [x] 外部参考归纳（识典古籍 / Plaud / 刻本 / 反参考）

---

## 三、P1 · 品牌壳统一

**范围：** 导航、favicon、报告封面、E2E 选择器 — **不改页面结构**。

| 任务 | 文件 | 验收 |
|------|------|------|
| Shell 已用 `fusheng-mark.svg` | `NewAppShell.vue` | 44px 无圆裁 |
| 报告封面 | `ReportView.vue` | 88px mark |
| favicon | `frontend/public/fusheng-logo.png` | 纸底清晰 |
| 首页 shell 文案 | `NewAppShell` subtitle | 不重复 LOGO 内文案 |
| E2E | `fusheng-anti-slop.spec.ts` | logo visible |

**禁止：** 此阶段不改 `NewHomeView` 布局。

---

## 四、P2 · 品牌首页

**目标：** `/` 首屏 = LOGO + 系列名 + 进入；档案下沉。

| 任务 | 说明 |
|------|------|
- [x] 拆分视图 | `NewHomeView` 品牌首页 |
- [x] 首屏 | mark + 人生六卷辑录 + 进入辑录 |
- [x] 滚动 | `BrandVolumeRegister` 六卷登记表 |
- [x] 案头 | 滚动后 desk 块 — 有档案时显示 |
| 数据 | 首屏 **无** profile 姓名/四柱（`useProfile` 延迟加载） |

**对照样张：** `docs/design/mockups/05-home-song-target.html`

**验收：**

- [x] 首屏留白 ≥65%（gate 居中 · min-height 视口）
- [x] 仅纸→白一级内容块（gate 纯纸面 · codex 单 panel）
- [x] 六卷为行界表，非卡片
- [x] `npm run test`（BrandVolumeRegister.spec）

---

## 五、P3 · 卷页章法

**原则：** 只应用 **章法**（间距、行界、两级纸面），不加国风装饰。

| 页面 | 主角 | 改动要点 |
|------|------|----------|
| `/profile` | 档案封面 | 卷封 Hero；KPI 条保留但降视觉权重 |
| `/new/bazi` | 六柱界画 | 去嵌套卡；Trust 左线 |
| `/new/ziwei` | 方盘 | 纯色底；宫格线 |
| `/report` | 卷目 | 与 MASTERPLAN 卷结构对齐 |

**共享组件提取（按需）：**

- `VolumeRegister.vue` — 六卷三列表
- `CodexPanel.vue` — 纸→白单块容器
- `SectionRule.vue` — 铜左线 section

**Token：** 禁止新增 chroma；只用 `variables.css` 现有项。

---

## 六、P4 · 门禁与回归

| 检查 | 命令 / 资产 |
|------|-------------|
| 单元测试 | `cd frontend && npm run test` |
| E2E | `npm run test:e2e` |
| 截图对照 | `docs/design/targets/` 更新首页截图 |
| Anti-slop | R079 五问自检 |
| mockup 同步 | 结构变更加 `05-home-song-target.html` |

**Signoff 条件：**

1. 美术三问（Foundation §七）全页通过  
2. 首页与 mockup 结构一致  
3. CI 绿  

---

## 七、风险与回滚

| 风险 | 缓解 |
|------|------|
| 首页改版影响老用户路径 | 案头续读保留；`/profile` 仍直达档案 |
| SVG 字体在 PDF/导出不一致 | 报告导出继续用 PNG fallback |
| 过度简化丢功能 | P3 才动卷页；P2 只动首页 |

**回滚：** P2 可 feature flag `VITE_BRAND_HOME=0` 切回旧首页（若实现时加开关）。

---

## 八、下一步（建议立即做）

1. **你确认** [`FUSHENG-ART-FOUNDATION.md`](../design/FUSHENG-ART-FOUNDATION.md) 数据与章法  
2. **执行 P2**：按 mockup 改 `NewHomeView.vue`  
3. P3 按 [`FUSHENG-EXECUTION-PRIORITY.md`](./FUSHENG-EXECUTION-PRIORITY.md) 卷顺序排期  

---

## 九、相关链接

- [识典古籍](https://www.shidianguji.com) — 文献 UI 样本  
- [Plaud 留白设计](https://www.digitaling.com/articles/1418437.html) — 留白率参考  
- [宋代美学 · 百科](https://baike.baidu.com/item/%E5%AE%8B%E4%BB%A3%E7%BE%8E%E5%AD%A6/67390408) — 雅淡简韵  
