# 浮生全书 · 抖音增长 · 细致开发方案

| 字段 | 内容 |
|------|------|
| **版本** | **v2.1（与 BACKEND-MASTER v2.2 对齐）** |
| **日期** | 2026-07-12 |
| **产品定位** | **宋式美学 · 人生之书** — 像翻阅一册命盘辑录，讲尽一生结构，而非 AI 算命 App |
| **增长模式** | **抖音内容引流 → 档案建档 → 数据洞察 → 付费深度阅读/报告** |
| **合并来源** | [BACKEND-ONLY v1.1](./BACKEND-ONLY-PLAN-2026-07-12.md) · [PRODUCT-CORRECTION](./PRODUCT-CORRECTION-PLAN-2026-07-12.md) · [UNIFIED-DEV](./FUSHENG-UNIFIED-DEV-PLAN-2026-07-12.md) · [FUSHENG-ART-STYLE](../design/FUSHENG-ART-STYLE.md) |
| **状态** | 🟡 **W15+ 后置**（打磨期禁止提前做；合并来源已归档，仅留历史索引） |

---

## 〇、产品一句话（抖音也能讲清楚）

> **浮生是一本可核对的「人生命盘辑录」：**  
> 用八字+紫微把一生的结构写清楚（经），用典籍与校勘脚注讲明白（注），用运限时间轴续写每一章（卷）。  
> AI 只当卷末「问书助手」，不当全书作者。

**对外话术（合规）：** 传统文化与自我认知工具 · 非医疗/投资/就业建议 · 仅供参考。

---

## 一、2026 市场与 AI 调研摘要

### 1.1 市场规模与人群

| 指标 | 来源趋势（2025–2026） | 对浮生的含义 |
|------|------------------------|--------------|
| 中国玄学/星座 App 市场 | 数百亿级人民币体量；18–35 岁占 **~68%** | 年轻人要「懂自己」，不是要晦涩术语 |
| AI 玄学搜索热度 | 抖音/小红书「AI 八字」「DeepSeek 算命」播放量 **百万级** | 流量在，但用户开始质疑 **AI 排盘准不准** |
| 行业 ARPU 参考 | 头部 App ARPU **~90 元/年** 量级 | Freemium + 深度报告有空间 |
| 抖音政策 | 严禁封建迷信直播；塔罗/占卜需规避话术 | 定位 **自我认知/传统文化/人生结构**，禁「改命」「必中」 |

### 1.2 2026 AI 命理三条铁律（行业共识）

| 铁律 | 说明 | 浮生策略 |
|------|------|----------|
| **排盘确定性，解读才用 AI** | LLM 直接「从生日算命」幻觉率高；紫微安星几乎必错 | ✅ 已有 Scorecard 引擎；AI **禁止**替代排盘 |
| **RAG + 结构化输入** | 把命盘 JSON/Markdown 喂给模型，比裸聊准 | ✅ `structured-text` + `evidence_refs` |
| **护城河在数据资产** | 古籍语料、黄金盘、verified 典籍，非 Prompt | ✅ classics 20%、GT/ZW 黄金盘；继续扩 |

**我们的差异化一句话（对 AI 竞品）：**  
「别人用 AI 写命运；浮生用算法写命盘，用典籍写讲解，AI 只帮你问书。」

### 1.3 抖音/短视频用户关注点（按热度排序）

| 排名 | 用户真正关心的 | 内容钩子示例 | 产品承接 |
|------|----------------|--------------|----------|
| 1 | **感情/正缘/合盘** | 「你的正缘什么时候来」 | 夫妻宫+合盘 Extension；分享卡 |
| 2 | **事业/财运/要不要跳槽** | 「今年适不适合动」 | 流年+大运卷；流月 Timeline |
| 3 | **自我认知/MBTI 式标签** | 「你是什么类型的人」 | 格局+十神+性格域（去 AI 腔） |
| 4 | **今年/本月运势** | 「这个月财运怎么样」 | 流年流月；日运（后期通知 stub） |
| 5 | **原生家庭/性格成因** | 「为什么你总是…」 | 四柱+用神+讲解层 |
| 6 | **可信度/准不准** | 「AI 算命靠谱吗」 | **双轨+iztro+校勘脚注**（差异化素材） |
| 7 | **便宜/免费先试试** | 首张牌免费、一键测试 | Freemium 配额 + 免费摘要卷 |
| 8 | **可分享的身份卡** | 金句卡、命盘截图 | 竖版分享 PNG + 引擎事实句 |

> 你的抖音视频应优先打 **1–3 + 6**：情感与自我认知是流量；**可核对**是信任与转化。

---

## 二、竞品亮点对照（每家 2 个特点 + 浮生应对）

| 竞品 | 类型 | **亮点 ①** | **亮点 ②** | 浮生现状 | 本方案 |
|------|------|------------|------------|----------|--------|
| **测测** | 泛心理+社区 | **小测试引流**（MBTI/塔罗/趣味测试） | **达人连麦按分钟计费**（核心变现） | 无测试壳；无达人 | GTM：免费「结构摘要」替代测试；**不做达人市集**（质量难控） |
| **文墨天机** | 专业紫微工具 | **排盘精度+大时间跨度** | **运限一键切换**（大限/流年/流月/流日） | 引擎可比；运限 UI 分裂 | FIX-C01；童限 Phase 4 |
| **灵机/天乙/高人汇** | 术数超市+撮合 | **多术数入口**（八字/六爻/风水） | **真人大师订单分成** | API 有；无订单 | Extension 超市；**不做大师撮合** |
| **同道大叔/陶白白** | 星座 IP | **爆款内容矩阵**（周运/情感） | **私域微信转化** | 无 IP 运营后端 | **创作者数据面板** + 归因 API |
| **星座女神** | 抖音 KOC 驱动 | **抖音小红书 KOC 铺量** | 月活高但付费转化偏低 | 无投放追踪 | `utm` 归因 + 落地页 |
| **Baguame** | 八字 Web 工具 | **Basic/Pro 渐进披露** | 合盘/移动端清晰 | 有分层雏形 | 宋式「卷目详略」 |
| **紫微派/iztro** | 开源排盘 | **十二宫方盘极简** | 三方四正/运限 overlay | iztro 已交叉核验 | 方盘 Hero + 脚注 |
| **DeepSeek/ChatGPT** | 通用 LLM | **对话便利、零门槛** | 多轮追问 | 有 LLM API | **追问助手** + structured 导出 |
| **DeepOracle 等垂直 AI** | AI+多流派 | **多流派八字对照** | 商业透明度不一 | dual_track 已有 | 双轨脚注当信任素材 |
| **YiSphere 等聊天壳** | AI+工具调用 | **聊天式一站式** | 多角色大师人设 | 无聊天壳 | 可选 H5 轻量对话（P2） |

### 2.1 浮生应坚持的「不做清单」（避坑）

| 不做 | 原因（竞品教训） |
|------|------------------|
| 达人连麦市集 | 测测 700+ 投诉；AI 教课出题考试化 |
| 纯 AI 从生日全自动 | 行业公认排盘幻觉 |
| 金句玄学卡当主产品 | 像 AI 算命 App；与「之书」定位冲突 |
| 直播占卜话术 | 抖音封禁风险 |
| 改命/化解法事导流 | 合规与品牌损伤 |

### 2.2 浮生应放大的「独有两点」（抖音素材库）

1. **校勘式信任**：双轨格局、missing_fields、iztro 对照 —— 拍「AI 算命靠谱吗」反转片。  
2. **人生之书结构**：卷目清晰、经注分离 —— 拍系列「读你的人生第一卷」。

---

## 三、产品信息架构：人生之书（宋式册页）

### 3.1 全书结构（替代 L1–L4 开发语言）

| 册页 | 用户语言 | 内容来源 | 默认状态 |
|------|----------|----------|----------|
| **封面** | 档案名、生辰一行、一句「卷首语」 | 引擎事实 | 展开 |
| **卷首** | 怎么读这本书（ReadingGuide） | 产品文案 | 展开 |
| **卷一·命之根** | 四柱、十神、格局、用神 | engine + classical | 展开 |
| **卷二·业之象** | 合冲刑害、神煞、双轨 | relations_summary | 展开 |
| **卷三·运之波** | 大运、流年、流月 | engine timeline | 展开 |
| **卷四·宫之图** | 紫微十二宫、格局 tier | ziwei engine | 展开 |
| **卷五·事之理** | 事业/财/婚/健康（事实+典籍+推断） | enrich 域 | 推断折叠 |
| **卷六·问书** | AI 追问助手（可选） | LLM + evidence_refs | **默认折叠** |
| **跋·校勘** | missing、iztro、典籍 spotcheck | Trust | 脚注条嵌入各卷 |

### 3.2 宋式美学落地规则（摘自 ART-STYLE）

- 载体 = **册页/辑录**；线条 = **界画直线**；色 = 纸墨铜朱。  
- 神秘感应来自 **校勘与双轨**，不来自云雾金箔。  
- 抖音竖版素材：纸纹底 + 细线框 + 一句「卷 x」标题，禁紫雾霓虹。

### 3.3 抖音内容 ↔ 产品页映射

| 视频系列 | 钩子 | 落地页 | 转化目标 |
|----------|------|--------|----------|
| 「读懂你的格局」 | 格局名+一句典籍 | `/bazi` 卷一 | 注册建档 |
| 「今年运之波」 | 流年干支+刑冲 | Report 卷三 | 免费摘要 → 付费全卷 |
| 「夫妻宫真相」 | 紫微夫妻宫主星 | `/ziwei` 卷四 | 合盘 Extension |
| 「AI 算命靠谱吗」 | iztro 双轨对比 | Report 跋 | 信任 → 分享 |
| 「你的人生目录」 | 六卷目录动效 | `/report` 连续阅读 | PDF/深度报告购买 |

---

## 四、增长与商业化架构（抖音 → 卖用户）

### 4.1 漏斗

```mermaid
flowchart LR
  A[抖音短视频] --> B[H5/落地页 卷首摘要]
  B --> C[免费建档 1 盘]
  C --> D[卷一~二 免费读]
  D --> E[卷三~五 付费解锁]
  E --> F[PDF全书 / 年度运卷 订阅]
  F --> G[私域复购 明年卷]
```

### 4.2 定价建议（可调）

| 档位 | 内容 | 参考价 | 后端依赖 |
|------|------|--------|----------|
| **免费** | 卷一~二摘要、分享卡 1 次/日 | ¥0 | quota |
| **读卷 Pass** | 卷三~五全量 + Timeline | ¥29–49/月 | entitlement |
| **全书 PDF** | 印装风 PDF + 校勘附录 | ¥68–128/次 | fusheng_report |
| **年度运卷** | 流年报告异步 + 12 月流月 | ¥98–198/年 | liunian DB 队列 |

### 4.3 你需要的数据分析（创作者视角）

| 指标 | 用途 | 后端需求 |
|------|------|----------|
| 视频 topic → 点击 → 注册 | 哪类内容带货 | **归因 API** |
| 卷目停留时长 | 哪一卷促付费 | **analytics events** |
| 分享卡导出次数 | 裂变 | export 日志 |
| 付费转化 cohort | 抖音粉 vs 自然流 | user.source |
| 术语点击热词 | 下期视频选题 | glossary 点击埋点 |
| 流失点（卷二未读卷三） | 优化讲解 | funnel 事件 |

---

## 五、后端功能规划（在 v1.1 之上 · 为抖音与卖书新增）

> v1.1 已完成：引擎、quota、structured-text、evidence_refs、archive-bundle、liunian 队列等。  
> **精确执行** → [BACKEND-MASTER-PLAN v2.2](./BACKEND-MASTER-PLAN-2026-07-12.md)（§十五 用户里程碑与改期）。  
> **GTM 后端项（BE-GTM-01~12）整体顺延至 Master P3（约 W16）之后**；W8 前仅做试读卷，不做六卷全量付费 campaign。

### 5.1 后端任务全表

| ID | 功能 | 优先级 | 说明 | 主要路径 |
|----|------|--------|------|----------|
| **BE-GTM-01** | 事件分析 API | **P0** | `POST /api/v1/analytics/events` 批量埋点；卷目阅读/术语点击 | 新 `routers/analytics_events.py` |
| **BE-GTM-02** | 渠道归因 | **P0** | 用户/案例 `utm_source/campaign/content_id`（抖音视频 ID） | `Case`/`User` 字段 + 注册接口 |
| **BE-GTM-03** | 抖音钩子句 API | **P3** | `GET /life-snippets`（P3-02；W16 前用 explain batch 手工抽句） | P3 Read Model |
| **BE-GTM-04** | 人生卷目 API | **P3** | `GET /life-volumes/{case_id}`（P3-01；**W16 上线**） | 读模型 |
| **BE-GTM-05** | 卷目解锁权益 | **P0** | `entitlement`: free/volume_pass/full_book；中间件校验 | 扩展 `quota_service` |
| **BE-GTM-06** | 支付回调实装 | **P1** | 微信/Stripe webhook → 写 entitlement | `routers/payment.py` 深化 |
| **BE-GTM-07** | H5/小程序 JWT | **P1** | 短 token 落地页免登录读卷一摘要 | `auth` 扩展 |
| **BE-GTM-08** | 创作者统计面板 API | **P1** | 你的后台：topic 转化、cohort | `routers/creator_stats.py` |
| **BE-GTM-09** | 合规免责声明块 | **P0**（Master P0-08） | 所有 report/explain API 带 `disclaimer_block` | schemas |
| **BE-GTM-10** | 私域留资 stub | **P2** | 手机号/微信 optional；导出 CSV | `routers/leads.py` |
| **BE-GTM-11** | 竖版分享卡模板 | **P1** | `export/card?layout=douyin` 9:16 | `pdf_exporter` |
| **BE-GTM-12** | OpenAPI 全量同步 | **P0** | 新端点进 CI | `make sync-frontend-types` |
| **BE-R01** | ZW18 iztro | **P0**（Master P0-01） | 数据校准或 trust degraded | 已有计划 |
| **BE-R02** | 典籍页码 spotcheck | P2 | 人工队列 | 已有计划 |
| **BE-P4-02** | 童限/流日 Schema | P2 | 对标文墨 | Phase 4 |

### 5.2 后端不必再做（已定案）

| 项 | 原因 |
|----|------|
| 引擎核心重写 | Scorecard 24/24 |
| 达人撮合/连麦 | 竞品投诉+品控 |
| 从紫薇回迁 router | c2 为超集 |
| LLM 替代排盘 | 行业反模式 |

### 5.3 `life-snippets` 响应示例（抖音文案用）

```json
{
  "case_id": "...",
  "hooks": [
    {"tag": "事实", "text": "日主戊土，正官格透干。", "layer": "engine"},
    {"tag": "典籍", "text": "《子平真诠》：官格贵印…", "layer": "classical"},
    {"tag": "推算", "text": "2026 丙午，流年冲日支。", "layer": "engine"}
  ],
  "vertical_title": "卷三·运之波",
  "disclaimer": "传统文化与自我认知参考，非命运断言。"
}
```

---

## 六、前端开发规划（宋式之书 + 抖音承接）

### 6.1 与 PRODUCT-CORRECTION 的合并任务

| 原 ID | 之书化改名 | 周次 |
|-------|------------|------|
| FIX-A01 | **卷一·卷二同屏**（命之根+业之象） | W1 |
| FIX-A02 | 接 `relations_summary` | W1 |
| FIX-B01/B02 | 卷首 ReadingGuide + TermHint | W3 |
| FIX-B03 | 典籍证据链嵌入各卷 | W4 |
| FIX-A04/D01 | 卷六·问书 默认折叠 | W2/W8 |
| FIX-C04 | 抖音竖版分享卡 UI | W7 |

### 6.2 前端新增（GTM 专属）

| ID | 任务 | 周次 | 文件 |
|----|------|------|------|
| **FE-GTM-01** | 抖音落地页 `LandingVolume.vue`（卷首摘要） | W5 | `views/landing/` |
| **FE-GTM-02** | 卷目导航 `BookToc.vue` 替代章节目录 | W2 | `components/fusheng/` |
| **FE-GTM-03** | 卷锁定态 + 付费墙 UI | W6 | 接 entitlement API |
| **FE-GTM-04** | 钩子句复制按钮（拍视频用） | W5 | 接 life-snippets |
| **FE-GTM-05** | 创作者 Dashboard（仅你） | W8 | `views/creator/` |
| **FE-GTM-06** | 埋点 SDK 封装 | W5 | `utils/analytics.ts` |
| **FE-GTM-07** | 竖版 9:16 分享预览 | W7 | export card |

### 6.3 页面母版（宋式）

| 母版 | 用于 | 参考 |
|------|------|------|
| **A 盘面卷** | 八字/紫微 | handbook-bazi-layout |
| **B 档案卷** | Profile/Home | 侧栏 KPI |
| **C 全书卷** | Report 连续阅读 | report-print.css |
| **D 落地卷** | 抖音 H5 | 单卷摘要+CTA |

---

## 七、内容规范（之书版 · 抗 AI 化）

### 7.1 四层标签（强制）

【事实】【典籍】【推算】【推断】— 同 PRODUCT-CORRECTION §六。

### 7.2 抖音脚本模板（你自己拍）

```text
钩子（3s）：「你的命盘第一卷写的是什么？」
事实（10s）：展示卷一格局+十神（屏幕录屏浮生）
信任（5s）：「这是引擎算的，不是 ChatGPT 编的」+ iztro/双轨一闪
CTA（5s）：「链接里免费读你的卷一卷二」
```

### 7.3 合规话术

- ✅ 自我认知、传统文化、人生结构、参考  
- ❌ 改命、化解、必中、算命、迷信  

---

## 八、16 周细致排期（与 BACKEND-MASTER v2.2 对齐 · 2026-07-12 修订）

> **重要：** 原 W5 落地页/六卷/付费 campaign **已改期**。抖音全量带货不得早于 **U2（W8）**；六卷+付费不得早于 **U5（W16）**。

| 周 | 后端（Master） | 前端/设计 | 抖音运营 |
|----|----------------|-----------|----------|
| **W1–3** | P0：ZW18·Snapshot·disclaimer·OpenAPI | trust UI；types 同步 | 只拍「引擎可核对」系列；**不挂付费** |
| **W4–8** | P1：explain/batch·MVP-20·quota Redis | 八字页 2 往返；TermHint；卷一二同屏 | **U2 试投**：卷首+卷一二；钩子句从 fact_lines |
| **W9–13** | P2：校勘 35%·PDF·童限 REGISTRY | Report 接 explain；付费墙 UI 预备 | 小规模测 PDF 内测（U4） |
| **W14–16** | P3：life-volumes·snippets·worker | BookToc；LandingVolume；六卷阅读 | **U5 正式上线** 卷三~五付费 |
| **W17+** | BE-GTM-01~08 增长后端 | 埋点 SDK；Creator Dashboard | 全量 campaign + 年度运卷 |

### 8.1 对外话术时间线

| 阶段 | 话术 |
|------|------|
| W8 前 | 「命盘结构册 · 试读卷（卷一~二）」 |
| W8–15 | 「人生之书 · 内测卷（含 PDF 样章）」 |
| W16 后 | 「人生六卷 · 完整版」 |

---

## 八（原）· 16 周排期存档

<details>
<summary>v2.0 原排期（已废止，仅备查）</summary>

| 周 | 后端 | 前端/设计 | 你的抖音运营 |
|----|------|-----------|--------------|
| **W0** | OpenAPI 同步；BE-GTM-09 disclaimer | Token/卷目线框 Draw.io | 定 3 个系列选题 |
| **W1–2** | BE-GTM-02 归因；BE-GTM-04 life-volumes v0 | 卷一~二同屏；BookToc | 拍 1 条「格局」测点击 |
| … | （余周略，见 git 历史） | | |

</details>

---

## 九、插件与工具链（22 个全用 · 按角色）

> 详见 [FUSHENG-UNIFIED-DEV-PLAN §四](./FUSHENG-UNIFIED-DEV-PLAN-2026-07-12.md)；本书方案增量：

| 场景 | 插件/命令 |
|------|-----------|
| 卷目线框 | **Draw.io** `handbook-book-toc.drawio` |
| 抖音落地页静态稿 | **Live Server** + `skin-preview.html` |
| 竖版分享卡视觉 | **colorize** 朱批色 |
| 卷目文案 | **Markdown All in One** + markdownlint |
| 钩子句 API 联调 | `backend:dev` + **Error Lens** |
| 埋点/漏斗 | **Vitest** `analytics.spec.ts` |
| 落地页 E2E | **Playwright** `e2e/douyin-landing.spec.ts` |
| 每周 Gate | `make scorecard` · `make quality-gate` |

### Cursor Agent 模板（之书 + GTM）

```
@docs/plan/FUSHENG-BOOK-GTM-DEV-PLAN-2026-07-12.md
@docs/design/FUSHENG-ART-STYLE.md
@frontend/src/views/ReportView.vue

按「人生之书」六卷重构 Report：BookToc、卷六问书默认折叠。
新增 life-volumes 消费占位；宋式界画线框。
禁止 L1-L4、金箔、AI 主文案。
```

---

## 十、验收标准（产品+商业+技术）

### 10.1 产品体验

| 指标 | 目标 |
|------|------|
| 首屏结构字段 | ≥8 |
| 六卷 IA 上线 | 卷一~四默认展开 |
| 带标签句子占比 | ≥70% |
| 卷六 AI 首屏占用 | 0 |

### 10.2 抖音增长（你运营侧）

| 指标 | 目标（冷启动 8 周） |
|------|---------------------|
| 落地页点击率 | 监测 baseline |
| 注册转化率 | ≥5% 点击用户 |
| 付费转化率 | ≥3% 注册用户（可调） |
| 分享卡导出 | 每付费用户 ≥1 |

### 10.3 技术 Gate

```bash
make sync-frontend-types
make scorecard                    # 24/24
make test-fast
cd frontend && npm run test && npm run test:e2e
python scripts/verify_classics_ctext.py
```

---

## 十一、文档关系（哪份是「最终」）

| 文档 | 角色 |
|------|------|
| **本文 v2.0** | **产品+增长+后端+前端 总蓝图**（抖音+之书） |
| [FUSHENG-UNIFIED-DEV-PLAN](./FUSHENG-UNIFIED-DEV-PLAN-2026-07-12.md) | 10 周工程+插件细则 |
| [BACKEND-ONLY v1.1](./BACKEND-ONLY-PLAN-2026-07-12.md) | 后端已结项清单 |
| [PRODUCT-CORRECTION](./PRODUCT-CORRECTION-PLAN-2026-07-12.md) | 四痛点诊断原文 |
| [FUSHENG-ART-STYLE](../design/FUSHENG-ART-STYLE.md) | 宋式美术宪法 |
| [FUSHENG-SONG-DEVELOPMENT](../guides/FUSHENG-SONG-DEVELOPMENT.md) | 三角色实施手册 |

**建议：** 前端设计定稿前，以 **本文 §三 卷目 IA + §六 前端表** 为交互准绳；定稿后回写 `skin-preview.html` 与 `handbook-report-layout.md`。

---

## 十二、修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v2.0 | 2026-07-12 | 宋式人生之书 + 2026 市场/AI 调研 + 竞品双亮点 + 抖音 GTM + 后端 GTM 12 项 + 16 周排期 |
| v2.1 | 2026-07-12 | 与 BACKEND-MASTER v2.1 对齐；GTM 后端延后 P3 |
| **v2.1-align** | **2026-07-12** | **与 BACKEND-MASTER v2.2 改期：W8 试读卷、W16 六卷付费、BE-GTM 顺延 W17+** |
