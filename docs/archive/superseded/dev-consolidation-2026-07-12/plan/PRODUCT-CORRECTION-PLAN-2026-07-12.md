# 浮生 · 产品修正方案（竞品差距 × 体验诊断）

| 字段 | 内容 |
|------|------|
| **版本** | v1.0 |
| **日期** | 2026-07-12 |
| **触发** | 原产品体验反馈：**显示不全 · 内容过于 AI 化 · 看不懂 · 没有讲解** |
| **关联** | [`PRODUCT.md`](../../PRODUCT.md) · [`FUSHENG-FRONTEND-HANDBOOK.md`](../guides/FUSHENG-FRONTEND-HANDBOOK.md) · [`BACKEND-ONLY-PLAN`](./BACKEND-ONLY-PLAN-2026-07-12.md) v1.1 |

---

## 一、问题诊断（用户反馈 ↔ 代码事实）

| 用户感受 | 根因（当前实现） | 严重度 |
|----------|------------------|--------|
| **显示不全** | 关系/神煞/典籍多在 **L3 信任层**；`heuristic` 默认折叠；Report 分章导航 + 非连续阅读；大运只展示前 10 步；`relations_summary`/`shensha_summary` 后端已上浮 **前端未接** | **P0** |
| **过于 AI 化** | Report 页 **AI 解读面板**权重高；无 Key 时 LLM **Mock 模板**；`personality/career/…` 域模块长段 `interpretation_text` 像「生成腔」；`bazi_summary` 无逐句出处 | **P0** |
| **看不懂** | 界面用 **L1–L4 / engine / heuristic** 开发标签；术语无释义；`glossary` API 存在 **前端零接入** | **P0** |
| **没有讲解** | 无「怎么读这张盘」引导；无宫位/十神 **逐条讲解**；`evidence_chain`/`classic_refs` 有数据但不在主阅读路径 | **P0** |

**结论：** 后端引擎与 Trust 能力已强于多数竞品，但 **产品叙事反了**——把「可验证的结构」藏在折叠区，把「模板化长文」放在主视野，用户自然觉得像 AI 算命 App 而不是「能学会的命盘册」。

---

## 二、与同类竞品差距（按你的四个痛点重排）

> 对照：**文墨天机**（专业完整）、**测测**（AI+讲解+社区）、**灵机/天乙**（教学+术数超市）、**Baguame / 紫微派**（盘面清晰+渐进披露）

### 2.1 显示完整性

| 能力 | 文墨 / Baguame | 测测 | 浮生现状 | 差距 |
|------|----------------|------|----------|------|
| 八字六柱 + 十神全显 | ✅ 首屏 Hero | 摘要为主 | ✅ `BaziReferenceTable` | 小 |
| 合冲刑害/神煞默认可见 | ✅ 盘面旁 | 弱 | ⚠️ 多在 L3 / 需点开 | **大** |
| 紫微十二宫全星 | ✅ 方盘锚点 | 简化 | ✅ 有盘；Report 十二宫偏表格式 | 中 |
| 运限（大限/流年/流月） | ✅ 一键切换 | 日运推送 | ⚠️ Timeline 有；与 Report 未统一 | **大** |
| 双轨/iztro 可核对 | 文墨弱 | 无 | ✅ Trust 有；**非主路径** | 中（展示位） |
| 扩展术数（六爻/择日等） | 灵机「超市」 | 测试卡片 | API 有；**Extension 未主流程** | 大 |
| 家庭成员多盘 | 测测 | 文墨多盘 | API 有；UI 弱 | 大 |

### 2.2 「AI 化」与可信度（核心差异化战场）

| 维度 | 测测 | 文墨 | 浮生现状 | 应达目标 |
|------|------|------|----------|----------|
| 主内容来源 | AI 对话 + 模板 | **排盘事实 + 典籍** | 域模块长文 + AI 面板 | **事实层 > 讲解层 > AI 辅助** |
| 出处标注 | 弱 | 典籍/口诀 | `provenance.layer` 有；**用户看不到句子级引用** | 每段话标 `[典籍][引擎][推断]` |
| Mock/无 Key | 商业 AI | 无 AI | Mock 模板 **与真解读同款 UI** | Mock 必须显式「示例稿」 |
| 分享形态 | 金句卡 | 盘面截图 | API 有；UI 未闭环 | 分享 **盘面+一句引擎事实**，非 AI 小作文 |

**浮生优势（应放大，不是藏起来）：** dual_track、missing_fields、Scorecard、iztro advisory——竞品几乎没有。

### 2.3 可读性 & 讲解

| 能力 | 灵机/天乙 | Baguame | 浮生现状 | 差距 |
|------|-----------|---------|----------|------|
| 术语点击释义 | ✅ | ✅ hover | ❌ glossary 未接 | **极大** |
| 新手阅读路径 | 课程/专栏 | Basic→Pro | L1–L4 开发语言 | **极大** |
| 「为什么是这个格局」 | 断法文章 | 规则简述 | `evidence_chain` 在数据里 | **大** |
| 宫位/十神逐条讲解 | 文墨深度 | 部分 | `palace.interpretation` 有；**无引导序** | **大** |
| 连续阅读 | 长文 | 滚动区块 | Report 分章 + AI 侧栏 | 中 |

---

## 三、修正原则（产品决策）

1. **盘面与结构优先于散文** — 首屏 40%+ 给六柱/十二宫，不是给 AI 框。  
2. **讲解跟术语走，不跟 AI 走** — 讲解 =  glossary + 证据链 + 典籍句；AI 只做「追问助手」。  
3. **三层内容严格分色分栏** — 用户只见：**事实 · 讲解 · 推断（可选）**，不见 `engine/heuristic` 英文标签。  
4. **缺失必须可见** — 延续 `missing_fields`；禁止用 AI 填空。  
5. **渐进披露用用户语言** — 「摘要 / 结构 / 深读」，不用 L1–L4。

---

## 四、修正方案（分阶段）

### Phase A · 信息架构纠偏（2–3 周，P0）

| 编号 | 任务 | 做法 | 验收 |
|------|------|------|------|
| **FIX-A01** | 主路径改「结构优先」 | 八字/紫微页：**L2 结构**上移（合冲刑害、神煞、格局证据）与盘面同屏；L3 Trust 改为脚注条 | 首屏可见 relations + shensha |
| **FIX-A02** | 接后端 `relations_summary` / `shensha_summary` | `NewBaziView` / `ReportView` 消费新字段；无则 fallback `bazi_structural_summary` | 与 API 字段一致 |
| **FIX-A03** | Report 默认连续阅读 | `continuousRead` 默认 `true`；侧栏章节目录改为锚点，不隐藏未选章节 | 打印/PDF 与屏读一致 |
| **FIX-A04** | AI 面板降级 | Report AI 区默认 **折叠**；标题改为「追问助手（可选）」；Mock 显示「示例稿·非引擎结论」 | AI 不占首屏 |
| **FIX-A05** | 域模块去「生成腔」 | `buildBaziModuleCards`：优先 `rule_matches`/`classic_refs` 短句；`interpretation_text` 降为 bullet 且标 `[推断]` | 事业/财运等块 ≤3 行事实 + 1 行推断 |

### Phase B · 讲解层建设（3–4 周，P0）

| 编号 | 任务 | 做法 | 验收 |
|------|------|------|------|
| **FIX-B01** | 术语 glossary 全站接入 | 新 `TermHint` 组件 + `GET /glossary?q=`；十神/神煞/宫位名可点击 | 覆盖率：Top 30 术语 |
| **FIX-B02** | 「怎么读这张盘」引导 | 八字/紫微/Report 顶部 **ReadingGuide** 3 步：看柱 → 看格局用神 → 看运限 | 新用户 30s 能跟完 |
| **FIX-B03** | 证据链可视 | 格局/用神卡片下挂 `evidence_chain` + `classic_refs` 展开列表（典籍句 + source_page） | 每盘 ≥1 条典籍可见 |
| **FIX-B04** | 紫微宫位讲解模式 | 十二宫列表增加「一句事实 + 一句讲解」；`layer=classical` 优先 | 点击宫位见主星+讲解 |
| **FIX-B05** | 用户语言替换 | UI 文案：`classical→典籍依据` `engine→排盘推算` `heuristic→经验推断`；去掉 L1–L4 | 无开发标签外露 |

### Phase C · 显示补全（2–3 周，P1）

| 编号 | 任务 | 做法 | 验收 |
|------|------|------|------|
| **FIX-C01** | 运限统一 | `FushengZiweiTimeline` 与 Report 大运/流年/流月 **同一 target_date 链** | 切换运限三处一致 |
| **FIX-C02** | 大运全量 | 取消 `slice(0,10)` 硬截断；分页或「展开更多」 | 全大运可查 |
| **FIX-C03** | Extension 主入口 | Home / Report 增加「扩展测算」卡片（择日/合盘/相似盘） | 不再藏在深路由 |
| **FIX-C04** | 分享卡改盘面事实 | PNG 卡主文案用 **格局+命宫+一句引擎事实**，非 AI summary | 与文墨式截图对标 |

### Phase D · AI 正确定位（2 周，P1，后端已备）

| 编号 | 任务 | 做法 | 验收 |
|------|------|------|------|
| **FIX-D01** | AI 必须挂证据 | 展示 `draft.evidence_refs`；无引用句禁止整段展示为「结论」 | FE-PORT-02 + provenance |
| **FIX-D02** | 结构化导出接 UI | Report「复制给 AI」走 `/structured-text`（已实现） | 用户自选外置 AI |
| **FIX-D03** | 多轮追问（可选） | 侧栏对话；**默认不自动生成** | 测测式体验但不抢主内容 |

### Phase E · 竞品长尾（P2–P3）

| 编号 | 对标 | 说明 |
|------|------|------|
| FIX-E01 | 测测 App | 小程序/PWA 壳；后端 API-first 已备 |
| FIX-E02 | 测测日运 push | `notifications` stub → 产品化 |
| FIX-E03 | 灵机术数超市 | ExtensionHub 四模块 + 教学短文 |
| FIX-E04 | 文墨运限深度 | 童限/流时 Schema 一等字段（Phase 4） |

---

## 五、页面级改造蓝图（Before → After）

### 八字页 `NewBaziView`

| Before | After |
|--------|-------|
| L1 摘要 → L2 盘 → L3 Trust（关系折叠）→ L4 长文 | **盘 + 关系/神煞 + 格局证据** 同屏 → **讲解卡**（典籍）→ **推断**（折叠） |
| `bazi_summary` 大段 | 拆成带标签的 3–5 条 evidence |
| 无 glossary | 十神/神煞 TermHint |

### 紫微页 `FushengZiweiView`

| Before | After |
|--------|-------|
| summary 偏 heuristic 口吻 | 首行 **事实**（五行局/命宫干支）+ 格局 tier 徽章 |
| patterns 列表无讲解 | 每条 pattern + 一句「为何成立/存疑」 |

### 报告页 `ReportView`

| Before | After |
|--------|-------|
| 章节目录 + AI 面板并列 | **连续阅读** + AI **底部折叠** |
| domains 八宫格长文 | 每域：**评分事实 + 1 条典籍/引擎依据 + 推断可选** |
| Trust 章孤立 | 双轨/iztro/missing **脚注条** 嵌入对应章节 |

---

## 六、内容与文案规范（抑制 AI 感）

### 6.1 段落模板（强制）

```text
【事实】日主戊土，月令寅木，正官透干。          ← 来自 pillars/geju，不可改写
【典籍】《子平真诠》：正官格以印为用…           ← classic_refs，带书名
【推算】当前大运乙丑，流年丙午，刑冲日支。      ← engine + relations_summary
【推断】今年宜守不宜攻。（经验归纳，非古籍）   ← heuristic，必须带标签
```

### 6.2 禁止

- 无出处的大段「您性格外向…」「命中注定…」  
- Mock LLM 与真引擎结论同一视觉样式  
- 用 AI 填补 `missing_fields`  

### 6.3 AI 仅允许

- 用户主动点击「追问」  
- 引用 `structured-text` 导出后的外置对话  
- 展示 `evidence_refs` 可展开核对  

---

## 七、优先级与排期建议

```
Week 1–2   Phase A（架构纠偏 + 接 relations_summary）
Week 3–5   Phase B（glossary + ReadingGuide + 文案替换）
Week 6–7   Phase C（运限统一 + 显示补全）
Week 8     Phase D（AI 降级 + evidence_refs UI）
Week 9+    Phase E（App/推送/超市，按商业节奏）
```

**与后端关系：** Phase A/B/D 以前端为主；后端 v1.1 已提供 `structured-text`、`evidence_refs`、`relations_summary`——**修正方案主战场在 `frontend/`**。

---

## 八、验收指标（修正是否成功）

| 指标 | 目标 |
|------|------|
| 首屏可见结构字段数 | ≥8（柱、十神、格局、用神、关系、神煞、大运、流年） |
| 带标签段落占比 | 主阅读区 ≥70% 句子有 `[事实/典籍/推算/推断]` |
| glossary 点击率 | 术语点击 ≥15% 会话（上线后测） |
| AI 面板首屏占用 | 0（默认折叠） |
| 用户主观调研 | 「像教材/命盘册」>「像 AI 算命」（定性访谈） |

---

## 九、修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-07-12 | 竞品差距 + 四痛点修正方案 |
