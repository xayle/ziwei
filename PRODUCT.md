# Product

## Register

浮生（Fú Shēng）

## Brand Slogan

浮生若寄，知命知心

## Users

主要使用者是需要查看八字、紫微斗数排盘结果的普通用户，以及继续维护命理功能的开发者。
他们的使用场景是已经进入命盘分析页面，希望快速得到一张可读、可验证、可继续扩展的盘面。

## Product Purpose

这是一个命理分析应用，核心任务是完成八字、紫微斗数、合盘与相关分析能力的排盘和结果展示。
成功标准不是“页面花哨”，而是盘面稳定可用、数据与知识可复用、接口和前端表现一致。

## Brand Personality

克制、可信、带一点神秘感。
整体语气偏安静，不做廉价玄学装饰，也不做过度科技风包装。

## Anti-references

- 过度紫色渐变和金红堆砌的玄学风页面
- 花哨但信息层级混乱的命盘界面
- 为了视觉效果而隐藏缺失数据
- 不可解释的自定义交互和不熟悉的按钮形态

## Design Principles

- 先保证盘面骨架清晰，再补充解释和延伸信息
- 缺失字段必须显式呈现，不能静默隐藏
- 八字和紫微分模块展示，避免信息混在一起
- 结果展示优先服务于读取和验证，再考虑视觉修饰
- 新页面与旧页面解耦，避免回退影响现有工作流

## Accessibility & Inclusion

- 目标至少满足 WCAG AA 的可读性要求
- 保持键盘可达和清晰焦点态
- 动效必须提供 reduced motion 降级
- 颜色不能作为唯一信息承载方式

## 执业声明与口径说明

本产品面向命理学习与结构验证，**不构成**医疗、法律、投资或就业决策建议。用户应自行判断输出内容的适用性。

### 双轨标注（recorded / engine）

部分命例同时保留：

- `recorded_geju`：古籍或历史 golden 标签
- `engine_geju`：当前引擎 live 计算基线

当二者不一致时，Regression 以 `engine_geju` 为准；产品层应显式展示双口径，避免静默覆盖。

### 已知漂移清单

| ID | 古籍/历史标签 | 引擎基线 | 说明 |
|----|---------------|----------|------|
| ZIP09 | 从官杀格 | 七杀格 | 时干乙木比肩助身，阻断从杀；Report 须双轨说明 |
| ZIP21 | 食神制杀格 | 七杀格 | 衍生格；`derived_geju` 对照 |
| ZIP22 | 伤官佩印格 | 伤官格 | 衍生格；`derived_geju` 对照 |
| GT03/05/07/08 | 正/偏财混用 | 引擎统一口径 | 已对齐 `engine_geju` 并保留 `recorded_geju_classical_note` |

### 紫微 × iztro 交叉核验

- 命令：`make verify-iztro`（CI advisory，不阻断合并）；`make verify-iztro-hour`（右弼 hour 口径辅煞对照）
- 详情：`docs/reports/ZIWEI-IZTRO-DRIFT-NOTES.md`
- **主星已对齐 iztro**：ZW01–02、04–08（2026-07-11 修复 `_place_ziwei` 后）
- **边界用例**：ZW03（立春前 + 晚子时）— **双轨**见 [`docs/reports/ZW03-DUAL-TRACK.md`](docs/reports/ZW03-DUAL-TRACK.md)
  - 引擎 canonical：`year_divide=lichun` + `day_divide=solar_next` → 乙丑
  - iztro 对照：`year_divide=normal` + `day_divide=forward` + ti=12 → 癸丑
- **文墨天机（wenmo）**：`make verify-wenmo-horoscope` / `python scripts/wenmo_engine_diff.py --bazi --write` — **advisory only**；差异写入报告与 colophon，**不覆盖主盘**（与 iztro 同轨）
- API：`iztro_crosscheck.advisory` 字段供 Report 展示
- 请求参数：`year_divide=lichun|normal`；`day_divide=solar_next|forward|current`（默认公历换日）
- Demo：`GET /api/v1/ziwei/demo?crosscheck=true` 可选启用交叉核验

### 右弼安星口径（产品决策）

- **默认维持流派差**：引擎 `youbi_method=month`（戌起正月逆数月），与 iztro 生时安右弼可能差一宫。
- **不改为 iztro 默认**：主星验盘已 14/14 对齐；右弼差异在 `engine_warnings` 与 Report 可信度区显式标注。
- **可选切换**：请求 `youbi_method=hour` 可切至时辰口径（legacy）；不作为产品默认。

### 免责声明

- 真太阳时、子时换日、四化表等流派参数可在档案中配置；不同设置可能导致盘面差异。
- 紫微借星、格局判定、典籍断语分层标注（heuristic / classical）请在 Report 中查看出处与置信度。
- 开发者维护引擎与语料，不保证与任一单一古籍版本完全一致。
