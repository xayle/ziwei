# 关系合盘样例 PDF 评审与产品对照说明

| 字段 | 内容 |
|------|------|
| **编号** | R086 |
| **版本** | 1.0 |
| **日期** | 2026-07-13 |
| **定位** | 文墨天机样例（黄振 × 路琳清 × 华倩）合盘 PDF 的**内容说明**、**多角色评审**、**与浮生现有功能/UI 对照**、**后续产品化建议** |
| **上位** | [`plan/RELATION-COMPAT-MASTER-PLAN-2026-07-13.md`](../plan/RELATION-COMPAT-MASTER-PLAN-2026-07-13.md) · [`guides/FUSHENG-FRONTEND-DEV.md`](../guides/FUSHENG-FRONTEND-DEV.md) |
| **契约** | [`contracts/relation-compat.schema.json`](../contracts/relation-compat.schema.json) |
| **样例 PDF（仓库内权威）** | [`output/pdf/合盘分析报告-黄振-路琳清-华倩-2026-07-12.pdf`](../../output/pdf/合盘分析报告-黄振-路琳清-华倩-2026-07-12.pdf) |
| **样例 PDF（用户桌面副本）** | `Desktop/文墨天机/合盘分析报告-正式版-2026-07-12.pdf`（clone 后可能不存在） |
| **生成脚本** | `scripts/generate_wenmo_compat_pdf.py`（Agent 一次性，**非生产管线**） |

> **一句话**：样例 PDF 证明了「双人深读 + 多人矩阵 + 破局时间轴」的用户价值，但当前交付**未走** `relation-compat@1.0` 与 App 导出链路；正式产品化需补 Trust 分层、多人 FE 与 export API。

---

## 一、背景与样例来源

### 1.1 输入材料（文墨天机导出）

| 文件 | 内容 |
|------|------|
| `合盘.docx` | 黄×路主合盘叙事（八字/紫微/子女/破局） |
| `黄.docx` / `黄.xlsx` | 黄振个人盘 + 十二宫表 |
| `路.docx` / `路.xlsx` | 路琳清个人盘 + 十二宫表 |
| `华.docx` / `华.xlsx` | 华倩个人盘 + 十二宫表 |

### 1.2 三人基础信息（引擎实算用）

| 人物 | 性别 | 出生（本地） | 四柱 | 紫微命宫 |
|------|------|--------------|------|----------|
| **黄振** | 男 | 1988-06-25 06:10 · 117.183° | 戊辰 戊午 辛亥 辛卯 | 乙卯 · 武曲/七杀 |
| **路琳清** | 女 | 1993-03-06 08:35 · 117.183° | 癸酉 乙卯 丙戌 壬辰 | 癸亥 · 巨门化权 |
| **华倩** | 女 | 1993-06-29 15:15 · 122.117° | 癸酉 戊午 辛巳 丙申 | 壬戌 · 廉贞/天府 |

> **时柱说明**：文墨真太阳时黄为 **辛卯**；项目 `verify_full` 按钟表 06:10 可能排 **庚寅**。合婚总分不变（60），但妻星/时柱论述应以用户选定口径为准，正式 PDF 须标注 `day_divide` / 真太阳时开关。

### 1.3 输出物

| 路径 | 说明 |
|------|------|
| **`output/pdf/合盘分析报告-黄振-路琳清-华倩-2026-07-12.pdf`** | **仓库内权威副本**（8 页 A4；评审与复现以此为准） |
| `Desktop/文墨天机/合盘分析报告-正式版-2026-07-12.pdf` | 用户桌面副本（非 git 跟踪，clone 后或无） |
| `_tmp_wenmo/compat_results.json` | 双引擎实算 JSON |
| `_tmp_wenmo/enriched_data.json` | 十二宫 enriched 数据 |

---

## 二、样例 PDF 结构说明（8 页）

| 页 | 章节 | 主要内容 |
|----|------|----------|
| 1 | 封面 | FUSHENG 标识、三人摘要、综合分（65.5 / 59.0 / 80.0）、heuristic 免责声明 |
| 2 | 执行摘要 | 关系定性 + 3×3 缘分矩阵 |
| 3–4 | 主合盘（黄×路） | 八字 §5.1 四维、十神地支、紫微五维、合和/飞星冲克、六大宫位对照 |
| 5 | 子女·田宅·业力 | 枭神夺食/紫府子女、天机忌田宅、交叉飞星 |
| 6 | 2026–2030 | 流年对照、分角色破局清单 |
| 7 | 路×华 | 闺蜜/合伙轴、五行循环、2027 风险 |
| 8 | 三人摘要 + 结论 | 单人格局/大运/2026 一行表 + 四条最终结论 |

### 2.1 引擎得分（与 `compute_compatibility` + `calc_compatibility` 一致）

| 组合 | 八字 | 紫微 | 加权综合 |
|------|------|------|----------|
| 黄振 × 路琳清 | 60（中） | 71/100（上签） | **65.5** |
| 路琳清 × 华倩 | 52（中） | 66/100（中签） | **59.0** |
| 黄振 × 华倩 | 77（上） | 83/100（上签） | **80.0** |

### 2.2 叙事层（文墨整合，非纯引擎）

以下内容来自 `合盘.docx` / 个人 docx，**属经验推断（inference）**，不应与引擎分同层展示：

- 「业力」「灵魂剧本」「相杀相爱」等定性语
- 奇门/河洛段落（PDF 已删减，docx 原文更厚）
- 服装合伙、情感勒索等场景化建议
- 华倩对路琳清婚姻边界的影响（三角张力）

---

## 三、多角色评审摘要

### 3.1 评分总表

| 评价轴 | 分数 | 说明 |
|--------|------|------|
| 作为交付物/阅读体验 | **7.5/10** | 结构完整、有温度，纸墨色封面合格 |
| 作为浮生产品输出 | **5.5/10** | 未走 `relation-compat@1.0`，缺 Trust/分层 |
| 相对当前界面能力 | **6/10** | 比 `RelationCompatView` 更厚，但多人/导出未产品化 |
| 相对文墨原文 | **6.5/10** | 保留主合盘逻辑，删减奇门/河洛/大运深读 |

### 3.2 分角色一句话

| 角色 | 结论 |
|------|------|
| **终端用户** | 能读、有用；三角关系与破局清单是 PDF 独有价值 |
| **UX/视觉** | 色系统一，缺 MASTERPLAN 卷目/Trust 色条/宋体嵌入 |
| **后端/引擎** | 分数可信，交付路径为 Agent 脚本，非生产 API |
| **合规** | 有 disclaimer，但推断与引擎混排，未过 `content_policy` |
| **产品/GTM** | 具备单次付费或 Pro 附录潜力，缺 App 内一键导出 |

### 3.3 维度雷达（0–10）

```
内容深度 8  |  叙事温度 8  |  引擎准确 7
Trust合规 5  |  视觉品牌 7  |  产品闭环 5
界面 parity 6  |  可复现性 4  |  商业就绪 6
```

---

## 四、与浮生现有功能对照

### 4.1 功能映射

| PDF 能力 | 线上是否有 | 代码/接口 | 差距 |
|----------|------------|-----------|------|
| 双人综合分 | ✅ | `RelationCompatView` · `POST /api/v1/relation/full` | 一致 |
| 六类关系切换 | ✅ | `RELATION_TYPE_OPTIONS` | PDF 固定情侣+闺蜜混合 |
| 分维得分表 | ✅ | `dimensions[]` | PDF 拆八字/紫微两表；UI 已融合 |
| 要点卡（合和/冲克） | ✅ | `summary_cards[]` | UI 单条截断 ~120 字 |
| 宫位互涉 | ⚠️ 部分 | `palace_cross[]` | PDF 含干支+主星表；UI 为 bullet |
| 共运时间轴 | ✅ | `timeline[]` | PDF 2026–2030；API 默认 `[-1,+2]` 年 |
| 相处建议（推断） | ✅ 折叠 | `action_items[]` | **UI 更合规**（默认折叠） |
| 模块张力 | ✅ | `tensions[]` | PDF 未单独成章 |
| **三人矩阵** | ❌ | `POST /api/v1/ziwei/multi_compat`（仅 BE） | FE 未接 |
| **合盘 PDF 导出** | ❌ | `render_html_to_pdf`（报告/case 有） | 合盘页无导出按钮 |
| Trust / provenance | ❌ | `EngineTrustPanel` · `layer` 字段 | PDF 仅一句 heuristic |
| 对方经度 | ⚠️ | `RelationCompatView` | 写死 116.41，华倩类案例会偏 |

### 4.2 界面模块（`/relation/new`）

当前结果页区块顺序：

1. `VolumeHead` — 关系类型 + 标题  
2. `score-hero` — 综合分 + 等级 + summary  
3. 要点卡 — `summary_cards`（support/conflict/neutral/action 色条）  
4. 分维得分表  
5. 宫位互涉  
6. 共运时间轴  
7. **折叠**「相处建议（推断层）」  
8. 模块张力 + disclaimer  

**PDF 有而 UI 无：** 3×3 矩阵、双引擎分栏（60+71）、六宫对照表、单人盘摘要、2026–2030 宽时间轴。

**UI 有而 PDF 无：** `tensions` 专章、`layers` 折叠块、`relation_type` 切换演示。

### 4.3 与路线图任务对照

| 任务 ID | 内容 | 样例 PDF 状态 |
|---------|------|---------------|
| T106–T107 | Extension 合盘 + `/relation/full` | 引擎已用，UI 已有，PDF 未挂 Extension |
| T113 | 合盘写入 life/volumes 附录卷 | 未做 |
| T123 | PDF 六卷 + CI 快照 | 合盘 PDF 未纳入 CI |
| P3（master plan） | 分享 PNG / 合盘报告卷 GTM | 样例证明需求，链路未通 |

---

## 五、差距与优先级

### P0 — 产品化必补

1. **合盘 PDF 走正式管线**  
   - 输入：`RelationFullResponse`（`relation-compat@1.0`）  
   - 渲染：HTML 模板 + `services/pdf_exporter.render_html_to_pdf`  
   - 入口：`RelationCompatView`「导出 PDF」或 `POST /api/v1/relation/export/pdf`

2. **Trust 三层标注**  
   - 引擎分 → `layer: fact`  
   - 典籍 → `layer: cite`  
   - 破局/业力/三角 → `layer: inference`，灰底 + 默认折叠  

3. **消除双真源**  
   - 禁止仅依赖 `scripts/generate_wenmo_compat_pdf.py`  
   - PDF 必须由与 UI 相同的 API 响应生成  

### P1 — 体验增强

4. 多人合盘 FE — 接 `multi_compat`，本案 3×3 矩阵  
5. UI/PDF 双引擎分栏 — 「八字 60 + 紫微 71 = 65.5」  
6. `RelationCompatView` 补全 partner `longitude` / `tz`  
7. PDF 嵌入宋体、页码、`request_id`、生成时间  

### P2 — 内容与 IA

8. `relation_type` 模板分离 — couple 不出合伙段；`business_partner` 单模板  
9. `timeline_years` 可配置至 `[0,4]`  
10. 合盘作报告附录卷（T113），不打断六卷主 IA  

---

## 六、推荐正式架构

```
档案/对方输入
    → POST /api/v1/relation/full  (relation-compat@1.0)
    → buildRelationCompat (FE) / composer (BE)
    → RelationCompatView 展示
    → buildRelationPdfHtml (新增)
    → render_html_to_pdf
    → 正式 PDF

可选：POST /api/v1/ziwei/multi_compat (2–4 人)
    → 矩阵 HTML → 同一 PDF 管线
```

正式 PDF **必须包含**：

- `schema_version` · `request_id` · 生成时间  
- `person_a` / `person_b` 的 `pillars_primary`、命宫、`wuxing_ju_name`  
- `dimensions[]` 含 `layer` + `engine`  
- `disclaimer_block` 全文（来自 API，非手写）  
- 推断章节在附录，不占封面后前两页正文  

---

## 七、复现与调试

### 7.1 重新生成 Agent 样例 PDF（非生产）

```powershell
cd d:\Users\Administrator\Desktop\c2
python scripts/generate_wenmo_compat_pdf.py
```

依赖：Playwright Chromium、`compat_results.json` 与 `enriched_data.json` 需已存在（或由同目录分析脚本生成）。

### 7.2 调用权威合盘 API（情侣）

```http
POST /api/v1/relation/full
Content-Type: application/json

{
  "relation_type": "couple",
  "person_a": {
    "birth_datetime": "1988-06-25T06:10:00",
    "tz": "Asia/Shanghai",
    "longitude": 117.183,
    "gender": "male",
    "label": "黄振"
  },
  "person_b": {
    "birth_datetime": "1993-03-06T08:35:00",
    "tz": "Asia/Shanghai",
    "longitude": 117.183,
    "gender": "female",
    "label": "路琳清"
  },
  "options": { "include_bazi": true, "include_ziwei": true, "liunian_year": 2026 }
}
```

友人轴（路×华）：`relation_type: "friend"`，替换 person_a/b。

### 7.3 前端验证

```text
/relation/new?type=couple
/extensions → 关系合盘（统一）
```

E2E：`frontend/e2e/fusheng-relation.spec.ts`

---

## 八、已知问题（样例 PDF）

| # | 问题 | 严重度 | 处理建议 |
|---|------|--------|----------|
| 1 | 推断与引擎分同层排版 | 高 | 正式版分 `fact` / `inference` 两册页 |
| 2 | 未走 `content_policy` 禁语扫描 | 中 | 导出前 `sanitize_text` |
| 3 | 第 6 页英文 `education` | 低 | 改为「教育/成长」 |
| 4 | 无 `request_id` / 页码 | 中 | 模板补齐 |
| 5 | 黄时柱口径未声明 | 中 | Trust 脚注真太阳时 |
| 6 | 脚本与 UI 双真源 | 高 | 见 P0-3 |

---

## 九、结论

| 问题 | 答案 |
|------|------|
| 样例 PDF 能不能给用户看？ | 可作**内部样稿/需求验证**；对外需补 Trust 分层与 export 管线 |
| 引擎分是否可信？ | 黄×路 65.5 与代码实算一致 |
| 比 App 强在哪？ | 三角矩阵、六宫表、宽时间轴、叙事厚度 |
| App 比 PDF 强在哪？ | 六类关系、推断折叠、档案联动、schema 契约 |
| 下一步做什么？ | P0：export API + Trust 分层 + 消双真源；P1：多人 FE + 双引擎分栏 |

---

## 十、相关文档

| 文档 | 用途 |
|------|------|
| [`plan/RELATION-COMPAT-MASTER-PLAN-2026-07-13.md`](../plan/RELATION-COMPAT-MASTER-PLAN-2026-07-13.md) | 合盘统一开发总纲 |
| [`reports/R102-product-rebuild-plan-2026-07-13.md`](R102-product-rebuild-plan-2026-07-13.md) | 六卷主路径体验重建（**优先于**合盘 PDF P0） |
| [`contracts/relation-compat.schema.json`](../contracts/relation-compat.schema.json) | API 响应契约 |
| [`design/pdf-template-preview.html`](../design/pdf-template-preview.html) | PDF 视觉参照 |
| [`plan/FUSHENG-EXECUTION-PRIORITY-POST-W14.md`](../plan/FUSHENG-EXECUTION-PRIORITY-POST-W14.md) | T106–T115 Extension 任务 |
| `scripts/generate_wenmo_compat_pdf.py` | 样例 PDF 生成脚本（待废弃为 prod 管线） |

### 10.1 排期约定

- **R102**（六卷 UI/内容/Trust）为当前最高优先级；**不占用** R102 Week1–4 的 FE 主带宽。  
- **R086 P0**（合盘正式 export + Trust 分层 + 消双真源）在 **R102 closeout 后**启动，或并行 **≤0.2 BE** 预研（export API 草图）。  
- 合盘 PDF 的宋体/Trust/推断折叠与 R102 Week3「报告辑录化 + PDF 一致」共用模板能力，避免两套 PDF 管线。

---

*R086 · 2026-07-13 · 样例评审闭环；正式 PDF 产品化排期见 §10.1（R102 之后）。*
