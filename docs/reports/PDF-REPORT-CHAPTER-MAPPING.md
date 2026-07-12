# PDF 报告章节对应版

本文档用于说明当前档案型命理产品的 PDF 报告结构，以及每一章对应的数据来源、展示目标和核心字段。  
目标是让 PDF 报告保持“正式交付件”风格，而不是调试输出或纯数据堆叠。

## 1. 报告目标

- 将用户输入的基础信息转换为统一档案
- 将八字、紫微、姓名三条主线整合为一份可讲解的报告
- 将时间轴、预警、附录整理成可复盘、可人工批注的交付件
- 保留原始数据索引，但不让原始数据破坏正文体验

## 2. 报告结构总览

| 章节 | 章节名称 | 主要用途 | 主要数据来源 |
|---|---|---|---|
| 封面 | 封面 | 建立档案感、交付感、版本感 | `case`、`snapshot`、`bazi`、`ziwei`、`name`、`zeri`、`fengshui` |
| 目录 | 目录 | 展示整份报告结构 | 固定章节结构 + 置信度标签 |
| 1 | 个人基础档案 | 记录用户基础输入与时间基准 | `Case` / `CaseOut` |
| 2 | 八字总览 | 给出八字核心结论 | `BaziFullResponse` |
| 3 | 八字深度分析 | 展示五行、刑冲合害、流年摘要 | `BaziFullResponse` 的深层字段 |
| 4 | 运势时间轴 | 展示起运、大运、流年、预警 | `dayun`、`liunian`、`liunian_detail`、`current_fortune_summary` |
| 5 | 紫微总览 | 展示紫微核心格局和摘要 | `ZiweiResponse` |
| 6 | 紫微宫位分析 | 展示十二宫和格局分析 | `ZiweiResponse.palaces`、`patterns`、`analysis`、`forecast` |
| 7 | 姓名分析 | 展示五格、三才、总分 | `NameAnalysisResponse` |
| 8 | 应用建议与参考 | 展示择日、风水、延伸建议 | `zeri`、`fengshui` |
| 9 | 附录与人工批注 | 留给人工讲解、版本和原始索引 | `export_format_version`、`exported_at`、`snapshot`、`errors` |

## 3. 章节说明

### 3.1 封面

**目标**

- 让 PDF 第一眼更像正式档案，而不是接口输出。

**展示内容**

- 用户姓名
- 性别
- 出生时间
- 出生地
- 当前分析模块状态
- 快照版本信息

**核心字段**

- `case.name`
- `case.gender`
- `case.birth_dt_local`
- `case.city`
- `case.tz`
- `case.lon`
- `snapshot.kind`
- `snapshot.api_version`
- `snapshot.rule_version`

---

### 3.2 目录

**目标**

- 让报告结构一眼可读
- 让用户知道每一章讲什么

**展示内容**

- 章节编号
- 章节标题
- 置信度标签

**说明**

- 目录页不展示复杂结论，只展示结构

---

### 3.3 个人基础档案

**目标**

- 明确“这是谁、什么时间、什么基准”

**展示内容**

- 姓名、性别
- 出生地、经度、时区
- 现居地、现居时区、现居经度
- 公历/农历
- 闰月标记
- 时间精度
- 未知时辰兜底方式
- 真太阳时开关
- 备注、标签
- 快照信息

**核心字段**

- `Case.id`
- `Case.name`
- `Case.gender`
- `Case.birth_dt_local`
- `Case.tz`
- `Case.city`
- `Case.lon`
- `Case.current_city`
- `Case.current_province`
- `Case.current_lon`
- `Case.current_tz`
- `Case.calendar_mode`
- `Case.is_leap_month`
- `Case.birth_time_precision`
- `Case.unknown_time_fallback`
- `Case.solar_time_enabled`
- `Case.notes`
- `Case.tags`
- `Snapshot.id`
- `Snapshot.kind`
- `Snapshot.api_version`
- `Snapshot.rule_version`
- `Snapshot.schema_version`
- `Snapshot.created_at`

**展示原则**

- 只展示硬信息
- 不在本章展开解释

---

### 3.4 八字总览

**目标**

- 先给八字结构性结论，再进入细节

**展示内容**

- 四柱
- 日主强弱
- 格局
- 用神、忌神
- 命局摘要

**核心字段**

- `pillars_primary.year`
- `pillars_primary.month`
- `pillars_primary.day`
- `pillars_primary.hour`
- `ten_gods.year`
- `ten_gods.month`
- `ten_gods.day`
- `ten_gods.hour`
- `day_master_strength.score`
- `day_master_strength.tier`
- `day_master_strength.factors`
- `geju.geju_name`
- `geju.geju_level`
- `geju.interpretation_text`
- `yongshen.favor`
- `yongshen.avoid`
- `bazi_summary`

**展示原则**

- 先结论，后依据
- 先整体，后局部

---

### 3.5 八字深度分析

**目标**

- 把八字判断依据拆开，让分析可解释、可讲解

**展示内容**

- 五行分布
- 偏缺、偏旺
- 平衡建议
- 刑冲合害总览
- 天干相克
- 流年重点

**核心字段**

- `wuxing_score.wood`
- `wuxing_score.fire`
- `wuxing_score.earth`
- `wuxing_score.metal`
- `wuxing_score.water`
- `wuxing_weak`
- `wuxing_strong`
- `balance_advice`
- `dizhi_relations`
- `tiangan_clashes`
- `liunian_detail`

**展示原则**

- 数值采用条形或卡片化表达
- 关系类信息单独成块，不混进总览

---

### 3.6 运势时间轴

**目标**

- 把起运、大运、流年、预警放在同一时间线里

**展示内容**

- 起运年龄
- 当前大运
- 当前流年
- 下一换运
- 大运条目
- 流年条目
- 主动预警
- 流月提示

**核心字段**

- `dayun.start_age`
- `dayun.start_age_text`
- `dayun.items[]`
- `liunian.items[]`
- `current_fortune_summary.current_dayun`
- `current_fortune_summary.current_liunian`
- `current_fortune_summary.dayun_years_remaining`
- `current_fortune_summary.top3_actions`
- `monthly_fortune`
- `liunian_detail`

**展示原则**

- 时间轴优先讲阶段变化
- 预警优先提示本命年、换运、冲克

---

### 3.7 紫微总览

**目标**

- 先给紫微的核心身份信息和结构摘要

**展示内容**

- 命主星
- 身主星
- 五行局
- 命宫干支
- 身宫干支
- 总览摘要
- 结构摘要

**核心字段**

- `life_ruler_star`
- `body_ruler_star`
- `wuxing_ju_name`
- `life_palace_gz`
- `body_palace_gz`
- `summary`
- `true_solar_time`
- `patterns[]`

**展示原则**

- 总览页不要把多个宫位分析压成一段长文
- 结构摘要只保留关键格局和一句解释

---

### 3.8 紫微宫位分析

**目标**

- 按宫位展开十二宫和格局判断

**展示内容**

- 十二宫总览
- 每宫主星、辅星
- 每宫结论、建议、提示
- 格局与分析
- 时间轴与流月提示

**核心字段**

- `palaces[]`
- `palace.name`
- `palace.branch`
- `palace.stem`
- `palace.main_stars`
- `palace.aux_stars`
- `palace.analysis`
- `palace.analysis_tags`
- `palace.conclusion`
- `palace.explanation`
- `palace.suggestion`
- `palace.tooltip`
- `patterns[]`
- `analysis`
- `forecast`
- `liuyue[]`

**展示原则**

- 每个宫位保持短块展示
- 长文本必须摘要化
- 不将宫位说明写成连续大段正文

---

### 3.9 姓名分析

**目标**

- 给名字一个结构化、可讲解的结论

**展示内容**

- 五格
- 三才
- 总分
- 一句话摘要

**核心字段**

- `surname`
- `given_name`
- `tianke.number`
- `tianke.element`
- `tianke.lucky`
- `tianke.score`
- `tianke.desc`
- `renke.number`
- `renke.element`
- `renke.lucky`
- `renke.score`
- `renke.desc`
- `dike.number`
- `dike.element`
- `dike.lucky`
- `dike.score`
- `dike.desc`
- `waike.number`
- `waike.element`
- `waike.lucky`
- `waike.score`
- `waike.desc`
- `zonge.number`
- `zonge.element`
- `zonge.lucky`
- `zonge.score`
- `zonge.desc`
- `sancai.pattern`
- `sancai.lucky`
- `sancai.score`
- `sancai.desc`
- `overall_score`
- `summary`

---

### 3.10 应用建议与参考

**目标**

- 把建议从主结论中拆出来，避免正文太重

**展示内容**

- 择日推荐
- 风水建议
- 幸运方向、颜色、植物、装饰等

**核心字段**

- `zeri.year`
- `zeri.month`
- `zeri.month_gz`
- `zeri.purpose_label`
- `zeri_days[]`
- `fengshui.auspicious_directions`
- `fengshui.decor`
- `fengshui.plants`
- `fengshui.lucky_colors`
- `fengshui.taboo`
- `fengshui.interpretation_text`

---

### 3.11 附录与人工批注

**目标**

- 给人工讲解、校对、签批预留空间

**展示内容**

- 导出版本
- 导出时间
- 格式说明
- 原始数据索引
- 人工批注区
- 免责声明

**核心字段**

- `export_format_version`
- `exported_at`
- `case`
- `snapshot`
- `errors`

**展示原则**

- 原始数据只做索引，不做大段直出
- 人工批注区保留空白线

## 4. 章节设计原则

1. 先结论，后细节
2. 先结构，后解释
3. 先卡片，后列表
4. 先摘要，后索引
5. 原始数据不进入正文主视觉
6. 章与章之间要有明确节奏差异

## 5. 推荐的正文视觉节奏

- 封面：强识别
- 目录：轻信息
- 基础档案：稳重、清晰
- 八字总览：结论优先
- 八字深度分析：图表优先
- 运势时间轴：阶段优先
- 紫微总览：核心信息优先
- 紫微宫位：卡片优先
- 姓名分析：表格式对照
- 应用建议：补充型内容
- 附录：索引和批注

## 6. 可直接复用的总结句

本 PDF 报告采用“封面 - 目录 - 个人基础档案 - 八字总览 - 八字深度分析 - 运势时间轴 - 紫微命盘总览 - 紫微宫位分析 - 姓名分析 - 应用建议与参考 - 附录与人工批注”的结构，所有章节都从统一档案数据和计算快照中生成，保证交付内容、解释逻辑和人工批注空间一致。
