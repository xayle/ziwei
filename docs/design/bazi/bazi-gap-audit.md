# 八字引擎 Gap Audit

版本：v1.0  
日期：2026-07-11  
关联：[ENGINE-CORE-FIX-PLAN](../../plan/ENGINE-CORE-FIX-PLAN-2026-07-11.md) · [方法注册表](ENGINE-METHOD-REGISTRY.md)

---

## 1. 执行摘要

| 阶段 | 状态 | 说明 |
|------|------|------|
| Phase 0 口径 | ✅ | B-01 ~ B-04 已确认 |
| Phase 1 P0 | ✅ | liuri 修复、双轨统一、gender 透传 |
| Phase 2 P1 | ✅ | self_seat、estimate_wealth、city_tier/industry |
| Phase 3 P2 | ✅ | 流日/流时最小实现、换运提示、测试矩阵 |
| Phase 4 文档 | ✅ | 本文档 + [进度报告](../reports/ENGINE-CORE-PROGRESS-2026-07-11.md) |

**结论**：八字引擎核心路径已从「双轨 + 硬编码缺失」收敛为「单轨新引擎 + 显式字段」。CLS01–CLS12 格局/用神已与古籍对齐；剩余缺口见 §4 与进度报告 §5。

---

## 2. 已具备（✅）

| 模块 | 权威路径 | API 暴露 |
|------|----------|----------|
| 四柱 | `app/core/verify.py`（sxtwl/cnlunar） | `pillars_primary` |
| 五行分 | `services/bazi_engine/wuxing.py` | `wuxing_score`（0–100%） |
| 日主强弱 | `services/bazi_engine/strength.py` | `day_master_strength` |
| 用神 | `services/bazi_engine/yongshen.py` | `yongshen` |
| 自坐 | 十二长生（B-02） | `pillar_details.*.self_seat` |
| 空亡 | `tables.get_kongwang` | `kongwang` / `kongwang_hit` |
| 地支关系 | `relations.get_branch_relations` | `dizhi_relations` |
| 天干相克 | `relations.get_stem_clashes` | `tiangan_clashes` |
| 调候摘要 | `MONTH_CLIMATE_RULES` + 用神 | `bazi_structural_summary.adjustment_summary` |
| 大运 | `dayun.py` + `build_dayun` | `dayun`（含 `transition_hint`） |
| 流年 | `liunian.py` | `liunian` |
| 财富估算 | `analysis/wealth_estimate.py` | 大运 `wealth_range` |
| 流日/流时 | `liuri.py` | `liuri_liushi`（需 `target_date`） |

---

## 3. Phase 修复对照

| 编号 | 任务 | 状态 | 备注 |
|------|------|------|------|
| B-P0-01 | liuri 语法修复 | ✅ | 玄空迁至 `fengshui_engine/xuankong.py` |
| B-P0-02 | wuxing/strength/yongshen 单轨 | ✅ | `compute_core_metrics()` |
| B-P0-03 | gender 透传 | ✅ | 大运顺逆 |
| B-P1-01 | 全柱 self_seat | ✅ | 禁止 unexplained `"缺失"` |
| B-P1-02 | estimate_wealth | ✅ | 替换内联系数 |
| B-P1-03 | city_tier / industry | ✅ | `BaziFullRequest` |
| B-P2-01 | 流日/流时 | ✅ P2 | 干支+十神 + `flow_score` / 大运流年联动 |
| B-P2-02 | 刑冲合害/空亡/调候 | ✅ | 经 `_enrich_v2_analysis` 输出 |
| B-P2-03 | 换运提示 | ✅ P2 | `start_age_days` + `days_to_next_transition` + `next_transition_hint` |
| B-P3-01 | verify 单轨 + `missing_fields` | ✅ P4 | 统一 `calculate()` |
| B-P3-02 | M2 enrich 可观测 | ✅ P5 | enrich 失败写入 `missing_fields` / warnings |
| B-P3-03 | CLS pre_1900 回归 | ✅ P6 | `engine_geju` 基线；CLS 古籍 drift 24/24 PASS |
| B-P3-04 | 十神/格局子平口径 | ✅ | `tables.get_ten_god` 阴阳异正同偏；`geju.py` 建禄/羊刃/化气 skip |
| B-P3-05 | 子平透干取格链 | ✅ | `_resolve_ref_stem`：月干藏透/同气/司令定正偏/比劫不夺格 |
| B-P3-06 | 八正格配用神 | ✅ | `_get_zhengge_yongshen`：官印/制杀/化杀/佩印/生财等 |
| B-P3-07 | 化气/外格/从格专用用神 | ✅ | `_get_extended_geju_yongshen`：曲直/化土/从财/从势等 |

---

## 4. 仍存在的 Gap

### 4.1 功能层（低优先级 / 已最小实现）

| Gap | 严重度 | 说明 |
|-----|--------|------|
| 流日/流时深度联动 | 低 | 最小实现已有；三层 flow 评分可继续加强 |
| 外格/化气/从格专用用神 | — | ✅ B-P3-07：曲直/化土/从财/从势等专用分支 |
| GT02 recorded 用神 | — | ✅ 已对齐：正印格官印用水+木 |

### 4.2 数据/结构层

| Gap | 说明 |
|-----|------|
| CLS 文献页码 | `source_page` 待人工核对原书（算法已对齐） |
| 十神口径下游 | LLM/报告若硬编码旧十神需排查 |

### 4.3 测试层

| 套件 | 状态 |
|------|------|
| `test_golden_regression.py` | ✅ GT01–GT08 + CLS；96 passed；古籍 drift 全 PASS |
| `test_geju_extended.py` | ✅ 含 CLS 取格 + 八正格/外格/化气/从格用神 |
| `test_engine_p4/p5/p6` | ✅ verify / enrich / pre1900 |
| `test_leap_month.py` | ✅ shim 导出 `_KNOWN_LEAP_MONTH_WINDOWS` |

---

## 5. 废弃与禁止引用

| 项 | 状态 |
|----|------|
| `app/core/solar_time.py` | 废弃，用 `solar_time_v2.py` |
| `bazi_full_service.compute_wuxing/strength` | ✅ 已删除 | 统一使用 `compute_core_metrics()` |
| `_calculate_v1` 内联财富系数 | 已删除，用 `estimate_wealth` |

---

## 6. 变更记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-07-11 | v1.0 | Phase 4 初始 gap audit（Phases 0–3 完成后） |
| 2026-07-11 | v1.1 | P3：liuri API、verify 对齐、legacy 清理、前端 types + schema.d.ts |
| 2026-07-11 | v1.2 | P4–P6：verify 单轨、enrich missing、CLS 回归；十神/格局子平口径对齐 |
| 2026-07-11 | v1.4 | B-P3-07 化气/外格/从格用神链；`TestExtendedGejuYongshen` |
| 2026-07-11 | v1.3 | 子平透干取格 + 八正格配用神；CLS01–CLS12 格局/用神古籍全对齐 |
