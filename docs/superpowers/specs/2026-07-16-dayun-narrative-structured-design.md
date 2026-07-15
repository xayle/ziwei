# 大运叙事结构化呈现（方案 B）

| 字段 | 值 |
|------|-----|
| 状态 | 已并入多轨规划 · P0 实施规格 |
| 日期 | 2026-07-16 |
| 决策 | 方案 B；完整路线见 [多轨规划（含河洛/奇门）](./2026-07-16-dayun-multi-track-roadmap.md) |
| 范围 | 八字深读大运块；报告卷三同源；P0 预留互证折叠壳 |

---

## 1. 问题

当前 `generate_dayun_narrative()` 已按「总起 / 事业 / 财运 / 情感 / 健康 / 古籍 / 声明」写模板，但 **拼成单一 `narrative` 字符串**；前端 `AnalysisPanel` 把整段塞进 `body`，形成墙文。用户诉求：

1. 有内容规划，不是长篇大论；
2. **数据是数据，讲解是讲解**，不要拼在同一读面。

---

## 2. 目标与非目标

### 目标

- API 返回可渲染的结构化域字段；保留 `narrative` 作兼容拼装（导出/PDF/旧客户端）。
- UI 分两层：**数据条**（可扫读事实）与 **讲解网格**（四域短文 + 古籍脚注）。
- 显式标注本段为「八字大运 · 启发式讲解」，避免被读成典籍铁口或其它术数。

### 非目标（本文件 / P0）

- **不实现**河洛/奇门算法（P2/P3，见多轨规划）；P0 仅允许互证区占位（`not_implemented`），禁止假数。
- 不改写十神模板策略本身（结构拆出后总量可不变）。
- 自动 LLM 大运（仍保持按需加载）。

---

## 3. 信息架构

每个大运步（如「丙子」）一卡，内部分区：

```
┌─────────────────────────────────────────┐
│ 数据条（引擎事实）                         │
│ 丙子 · 0–9岁 · 十神 · 顺/逆用神 · 格局提示   │
├─────────────────────────────────────────┤
│ 总起（core）一行意象 + 顺逆短注             │
├────────────┬────────────┐
│ 事业       │ 财运       │
├────────────┼────────────┤
│ 情感       │ 健康       │
└────────────┴────────────┘
│ 脚注：古籍佐证（可折叠）+ 免声明           │
│ 徽章：启发式                               │
└─────────────────────────────────────────┘
```

- **数据条**：来自既有引擎字段（干支、起止岁、十神、用神顺逆、geju/yongshen 提示等），**不**混入事业/财运长文。
- **讲解区**：仅启发式文本域；四格等宽，桌面 2×2，窄屏单列。
- **古籍**：脚注列表（来源 + 摘句），默认折叠或次级样式，不与四域并排抢视线。

---

## 4. 数据契约

### 4.1 新增模型（概念）

```ts
type DayunNarrativeSection = {
  core: string
  career: string
  wealth: string
  love: string
  health: string
  trend_note?: string
  classics: Array<{ source: string; text: string }>
  disclaimer: string
}

// Dayun step / dayun-report item
{
  // …现有引擎字段…
  narrative?: string | null           // 兼容：由 sections 拼装的完整原文
  narrative_sections?: DayunNarrativeSection | null
}
```

Python：`app/schemas/bazi.py`（及 dayun-report 响应体）增加与上表同形的 Pydantic 模型；`narrative_sections` optional。

### 4.2 生成器

`generate_dayun_narrative` 拆为：

1. `build_dayun_narrative_sections(...) -> DayunNarrativeSection`（真源）；
2. `format_dayun_narrative(sections) -> str`（拼回现有带【】长文，赋值 `narrative`）；
3. 调用方同时挂 `narrative` + `narrative_sections`。

财富估算句留在 `wealth` 字段内（或 `wealth` + 可选 `wealth_estimate`）；本期可不拆第三字段。

### 4.3 兼容

| 消费者 | 行为 |
|--------|------|
| 旧前端 / 仅读 `narrative` | 仍可读长文 |
| 新前端 | 有 `narrative_sections` 则走分块 UI；否则临时 FE 解析【】降级（过渡一个版本后可删） |
| PDF / 导出 | 可继续用 `narrative`，或后续另开「结构化排版」票 |

OpenAPI / `make sync-frontend-types` 随 schema 变更。

---

## 5. 前端改动

| 位置 | 改动 |
|------|------|
| 新小组件（建议）`DayunNarrativeCard.vue` 或扩 `AnalysisPanel` 变体 | 渲染数据条 + 四域 + 脚注 |
| `NewBaziView.vue` | `dayunAnalysisBlocks` 不再把整段塞 `body`；改接 sections |
| `ReportView.vue`（若同数据） | 同期改 `dayun-detail__narrative`，避免报告仍墙文 |
| 单测 | 解析/挂载 sections；缺字段降级 |

样式：复用 `variables.css` / 既有 fusheng 卡片间距；**不用**仪表盘式多卡堆叠整页；单大运一组合即可。

---

## 6. 文案与 Trust

- 区块标题人读：事业 / 财运 / 情感 / 健康 / 古籍佐证。
- 层徽章保持「启发式」（与现 `PatternTierBadge` / layer 一致）。
- 不在 UI 暴露机读字段名或模板密钥。

---

## 7. 测试与验收

- 后端：sections 四域非空；`format` 后中文字数仍落在既有验收带（若有单测断言则更新为「sections 齐全 + narrative 可由 format 复现」）。
- 前端：有 sections 时 DOM 出现四域标题且无整段墙文主容器；无 sections 时降级不炸。
- 手工：深读 → 加载大运叙事 → 丙子等步可见数据条与四格，古籍在脚注。

---

## 8. 实施顺序

1. Schema + `dayun_narrative.py` 拆 sections / format  
2. dayun-report 装配路径填 `narrative_sections`  
3. FE 组件 + `NewBaziView`（必要则 `ReportView`）  
4. 类型同步、单测、静态构建（若发版走 Docker SPA）

---

## 9. 开放项（本规格已决议）

| 项 | 决议 |
|----|------|
| 主轴 | 人生域分块；河洛/奇门为互证参考轨（多轨规划） |
| 数据 vs 讲解 | 上下分流，禁止拼成单一散文块主读 |
| `narrative` | 保留兼容拼装 |

---

## 10. 审阅清单

请确认：

- [ ] 四域（事业/财运/情感/健康）+ 古籍脚注是否足够  
- [ ] 报告页是否必须同一迭代改（默认：**是**，若共用 narrative）  
- [ ] 可开始写实现计划并改代码  
