# 八字 × 紫微 全项 9.5 达标整改总纲

版本：v1.0  
日期：2026-07-11  
基线评审：命理师严厉评分（八字 7.2 / 紫微 6.4 / 语料 7.0 / 产品 5.8）  
目标：**24 个评分项全部 ≥ 9.5 / 10**

---

## 0. 9.5 分的统一验收标准

每一项达标须同时满足：

| 维度 | 要求 |
|------|------|
| **典籍对齐** | 与《子平真诠》《滴天髓》《千里命稿》或《紫微斗数全书》指定口径一致； intentional drift 须 `recorded_*` + `engine_*` 双字段 + 用户可见说明 |
| **黄金回归** | ≥3 条独立 `pillar_direct` 或 `datetime` 用例；CI 100% PASS |
| **边界覆盖** | 该分项涉及的子时/闰月/真太阳时/流派参数至少有 1 条边界用例 |
| **可信度标注** | API 返回 `confidence` + `method_registry_id`；启发式层必须 `layer: heuristic` |
| **产品可见** | Fusheng 主路径或 Report 必须展示该分项核心输出（非仅后端字段） |

**评分复检**：每项整改完成后由 `scripts/audit_scorecard.py`（待建）输出 0–10 分 + 未达标缺口列表。

---

## 1. 八字分项达标清单

### 1.1 四柱排盘与历法边界（8.0 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| 子时换日不可配 | `pillars.py` 增加 `zi_day_rule: sxtwl \| early_zi_prev_day \| early_zi_same_day`；默认 sxtwl | GT05/GT06 + 新用例 ZI01–ZI04 四套规则各 PASS |
| 真太阳时+子时复合边界 | `tests/test_solar_zi_boundary.py`：经度 75°–135°，23:00–01:00 每 5min 采样 | 0 未解释翻柱 |
| 固定 120°E | `solar_time_v2` 支持 `standard_meridian` + 历史地方时表（省会经度 JSON） | 乌鲁木齐 vs 北京同钟点差异用例 PASS |
| 产品未展示边界 flag | API `validation.warnings` + 前端 Profile 展示 `day_boundary_crossed` | 手动 QA 1 条 |

**工时**：5d · **负责模块**：`pillars.py`, `solar_time_v2.py`, `boundary.py`, Fusheng Profile

---

### 1.2 五行旺衰 / 日主强弱（7.5 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| 无人元司令 | `strength.py` 新增 `_month_commander(day, month_branch, solar_term_day)` 分初/中/末司令 | 12 月支 × 3 段单元测试 |
| 藏干权重缺典籍锚 | `wuxing.py` 权重写入 `ENGINE-METHOD-REGISTRY` B-05；提供 `weight_profile: ziping \| modern` | 切换 profile 不破坏 ZIP/CLS 基线 |
| 旺衰与从格阈值耦合 | 从格阈值改为基于 `strength_score` + `wuxing_ratio` 双条件 | ZIP07–10 仍 PASS |

**工时**：6d

---

### 1.3 格局判定（7.8 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| 炎上/润下/稼穑/从革仅占比 | `geju.py` 新增 `_check_yanshang/runxia/jiaxu/congge_structural()` 对标曲直 | 各 2 条滴天髓/千里 pillar_direct 用例 |
| 缺复合格局名 | 增加 `伤官佩印格` `杀印相生格` `食神制杀格` `财滋弱杀格`（命名层，不替代八正格） | 子平语料各 1 例对齐 |
| 破格无救应 | `check_po_geju()` 扩展：合能解冲、印能化杀、食神制杀救应 | `test_geju_extended` +8 cases |
| ZIP09 漂移 | 保留引擎逻辑；`recorded_geju` 保留；Report 展示双口径 | 用户可见「古籍从杀 / 引擎七杀」 |

**工时**：10d

---

### 1.4 用神喜忌（7.6 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| 真假从未分 | `yongshen.py` `_cong_yongshen()` 分真从/假从（比劫印透程度） | ZIP07/09/10 三分支 |
| GT 正偏财漂移 | 统一 `recorded_geju` 为引擎口径 **或** 引擎支持 `legacy_ref_stem` 模式 | 36/36 recorded==engine 或文档化双轨 |
| 调候 vs 格局优先级 | `yongshen` 返回 `primary` + `secondary` + `priority_reason` | API schema + 前端展示 |

**工时**：5d

---

### 1.5 大运流年（6.5 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| 流年深度不足 | `liunian.py` 增加 `yongshen_shift` `geju_po_jiu` `tai_sui_relation` | 12 流年矩阵测试 |
| 大运格局联动 | `dayun.py` 每步大运附 `geju_impact` `yongshen_shift` | GT03 逆排 + ZIP07 从财大运 |
| 流日流时浅 | `liuri.py` 三层 `flow_score` 与大运/流年/用神联动 | P2 计划项闭环 |

**工时**：8d

---

### 1.6 合冲刑害 / 神煞（7.0 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| 天干合化浅 | `relations.py` `get_stem_combinations()` 合化成功/失败判定 | 甲己合土 + 破格例 |
| 神煞未入格局 | `shensha.py` → `geju` 天乙/魁罡/禄神与破格联动 | 3 神煞 × 2 格局 |
| 三会方局未命名 | `relations.py` 检测三会；`geju` confidence 调整 | 寅卯辰木会例 |

**工时**：6d

---

### 1.7 古籍语料（7.8 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| 语料未接规则 | `classic_refs.py` 格局名 → `geju_candidates` 软提示（非硬覆盖） | ZIP07 语料检索命中 |
| 子平无 ctext | `.env` + `make verify-ctext` CI optional job | ≥80 精确章节 |
| ZIP autogen 质量 | 剔除注文未断言从格；人工再审 ZIP11–16 | autogen score≥12 才入库 |

**工时**：4d + 人工 2d

---

### 1.8 黄金用例（8.2 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| 86% 古籍标签对齐 | 解决 GT03/05/07/08 + ZIP09 或双轨文档化 | recorded==engine ≥ 95% |
| 外格缺 pillar 用例 | 新增 ZIP17–ZIP22：炎上/润下/稼穑/从革/食神制杀/伤官佩印 | 6 例 engine 对齐 |

**工时**：4d

---

### 1.9 分析断语层（5.5 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| 模板化 | 新建 `services/bazi_engine/classical_narrative.py`：格局→滴天髓/子平句式 | 每格局 ≥1 典籍句 |
| 现代六维分误导 | `scoring.py` 输出 `layer: modern_convention`；前端默认折叠 | 不进入 Report 主文案 |
| 顺逆气机 | `structural_summary` 增 `shun_ni` 字段（旺衰+格局+大运） | CLS01–03 人工 spot check |

**工时**：8d

---

### 1.10 八字产品呈现（6.8 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| 典籍闭环 | Report 格局块：引擎格 + 古籍注 + 语料引用链接 | ZIP07–10 截图 QA |
| 用神双层 | 展示 primary/secondary + 调候 | Fusheng Bazi tab |
| 边界警示 | 子时/真太阳时 warning 条 | Profile + Result |

**工时**：5d

---

## 2. 紫微分项达标清单

### 2.1 安星诀（8.3 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| 仅 1 盘黄金 | `data/ziwei_ground_truth.json` 新增 ZW01–ZW08（男女/闰月/晚子/不同年干） | 8 盘 × 14 主星 + 6 辅煞坐标 |
| debug print | 删除 `stars_aux.py` debug | lint clean |

**工时**：6d + 人工排盘验证 3d

---

### 2.2 宫位 / 命宫身宫 / 五行局（8.5 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| 身宫 UI 不可见 | `FushengZiweiPlate` 身宫徽标 + 说明 | ZW01 截图 |
| 空宫借星 |  plate 展示借星虚线 | 空宫用例 ZW03 |

**工时**：3d

---

### 2.3 四化体系（8.0 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| UI 不展示 | Plate 四化色 + 图例；hover 显示宫干四化 | 8 盘回归 |
| 庚干多方案不可选 | Fusheng 高级设置 `sihua_stem_indices` | API 透传 E2E |

**工时**：4d

---

### 2.4 大限流年流月流日（7.5 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| 起运非精确 | `dayun.py` `start_age_exact` 精确到月日（可选） | 与文墨/iztro 对照 2 例 |
| 无叠宫 | `liunian.py` `overlay_palace_map`：大限/流年/流月入宫 | 设计文档 01-大限流年 3 例 |
| 流年 UI | Fusheng 时间轴 tab（从 NewZiweiView 移植精简版） | 可选流年 |

**工时**：8d

---

### 2.5 格局判定（5.8 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| 条件过松 | `patterns.py` top-20 格局重写：庙旺阈值 + 煞星计数 + 宫位约束 | 对照 `01-经典格局.md` 20/20 |
| 缺火贪/铃贪/杀破狼 | 新增 ZRULE_043–050 | 各 1 黄金盘触发 |
| 紫府限寅申 | ZRULE 条件收紧 | 误报率 <5% on ZW01–08 |

**工时**：12d

---

### 2.6 飞星 / 叠宫（6.0 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| forecast 非叠宫 | `forecast.py` 改为 `overlay_palace_map` 驱动 | 废弃 keyword-only 路径 |
| flying UI | Report/Fusheng 飞星简图 | 自化 ↑↓ 可见 |

**工时**：7d

---

### 2.7 断语与分析层（4.8 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| 静态模板 | `analysis.py` 改为 宫位+主星+四化+亮度 组合表（全书句式） | 12 宫 × 14 主星抽样 |
| 合盘误导 | `compatibility.py` 标注 `layer: heuristic`；文案改为「参考」 | API schema |
| forecast 分数 | 改为 `tier: favorable/neutral/caution` 非 0–100 | 前端不显示百分 |

**工时**：10d

---

### 2.8 黄金用例（4.5 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| ground_truth 零紫微 | 合并 ZW01–ZW08 入 `ground_truth_cases.json` 或并行 JSON | `test_ziwei_golden_regression.py` |
| 跨工具校验 | 可选：iztro 快照 diff（允许亮度差异注明） | CI optional |

**工时**：5d

---

### 2.9 流派参数 / 真太阳时（7.2 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| 前端全默认 | `ZiweiAlgoSettings` 接入 Profile 高级面板 | 8 参数 E2E |
| 八字紫微太阳时未统一 | `buildChartRequests.ts` solarTime → `longitude` 联动 | 同一 profile 双盘一致 |

**工时**：3d

---

### 2.10 紫微产品呈现（5.0 → 9.5）

| 缺口 | 交付物 | 验收 |
|------|--------|------|
| 85% 字段丢弃 | 恢复 `NewZiweiView` 时间轴 tab 到 `/new/ziwei` 子路由 | 大限/流年/流月可交互 |
| Report 过薄 | `ReportZiweiChart` 增亮度+四化+身宫 | 打印 PDF QA |

**工时**：8d

---

## 3. 交叉分项

| 项目 | 当前 | 交付物 | 工时 |
|------|------|--------|------|
| 体系统合 6.5 | ZW+ZIP 双验 3 人档案 | `dual_verify_cases.json` | 4d |
| 可信度标注 5.0 | 全 API `confidence` + `layer` | schema 统一 | 3d |
| 执业就绪度 6.8 | `PRODUCT.md` 执业声明 + 漂移清单 | 法务级免责声明 | 1d |
| 学术严谨度 7.5 | `scripts/audit_scorecard.py` 自动复检 | CI nightly | 3d |

---

## 4. 执行阶段（建议 18–20 周）

```
Phase A  地基（周 1–3）   ZW01–08 黄金盘 + 可信度 schema + 审计脚本
Phase B  八字引擎（周 4–8）  1.1–1.6 + ZIP17–22
Phase C  紫微引擎（周 9–13） 2.1–2.6 + patterns 重写
Phase D  断语+语料（周 14–16） 1.7–1.9 + 2.7
Phase E  产品闭环（周 17–19） 1.10 + 2.3–2.4–2.9–2.10
Phase F  总验收（周 20）     24 项复检 ≥9.5 + 文档 + 截图 QA
```

**总工时估算**：~145 人日（约 1 人 7 个月 / 2 人 3.5 个月 / 3 人 2.5 个月）

---

## 5. 不可一次到位的诚实边界

以下即使用尽工时，**9.5 分仍可能需要「口径选择」而非「绝对真理」**：

1. **ZIP09**：古籍从杀 vs 引擎七杀——可双轨文档化至 9.5，但无法「单一正确答案」
2. **庚辛壬癸四化多派**：可达 9.5 需 **用户选派**，非默认一统
3. **早子时换日**：三派各有传承，9.5 = 三派可切换 + 用例覆盖，非消灭分歧
4. **紫微格局**：全书派 vs 中州派细节差异——top-20 收紧后可 9.5，余格 8.5 标注待补

---

## 6. 立即开工的 Sprint A（本周可执行）

- [ ] A1 创建 `data/ziwei_ground_truth.json` 骨架 + ZW01 第二盘（1990 男命示例）
- [ ] A2 API 全响应加 `confidence` / `layer` 字段（八字+紫微）
- [ ] A3 删除 `stars_aux.py` debug print
- [ ] A4 ZIP autogen 门槛：`comment` 须含从/化关键词才入库
- [ ] A5 `scripts/audit_scorecard.py` 读取本计划输出 24 项分数

---

## 7. 相关文档

- [八字 Gap Audit](../design/bazi/bazi-gap-audit.md)
- [紫微 Gap Audit](../design/ziwei/ziwei-gap-audit.md)
- [ENGINE-CORE-FIX-PLAN](./ENGINE-CORE-FIX-PLAN-2026-07-11.md)
