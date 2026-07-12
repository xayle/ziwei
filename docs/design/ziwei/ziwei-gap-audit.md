# 紫微引擎 Gap Audit

版本：v2.0  
日期：2026-07-11  
关联：[ENGINE-CORE-FIX-PLAN](../../plan/ENGINE-CORE-FIX-PLAN-2026-07-11.md) · [方法注册表](ENGINE-METHOD-REGISTRY.md)

---

## 1. 执行摘要

| 阶段 | 状态 |
|------|------|
| Phase 0 口径（Z-01 ~ Z-05） | ✅ |
| Phase 1 P0 安星/运限 | ✅ |
| Phase 2 P1 结构补齐 | ✅ |
| Phase 3 P2 流日/流时 + 测试矩阵 | ✅ |
| Phase 4 文档 | ✅ | 含 [进度报告](../../reports/ENGINE-CORE-PROGRESS-2026-07-11.md) |

**结论**：紫微底层从「字典列表 + silent 缺失」升级为「dataclass 模型 + `missing_fields`」。P0 已对齐 **流年四化默认** 与 **全路由算法参数透传**（`/full`、`/demo`、`/batch`、`/flying`、合盘）。

---

## 2. 已具备（✅）

| 能力 | 模块 | 模型化 |
|------|------|--------|
| 命宫/身宫/五行局 | `palaces.py` | ✅ |
| 14 主星 + 亮度流派 | `stars_main.py` | ✅ |
| 辅煞杂曜（含天德/月德） | `stars_aux.py` | ✅ |
| 本命/宫干四化 | `transforms.py` | ✅ |
| 大限 + 四化 + 博士 | `dayun.py` | ✅ `DayunItem` |
| 流年 | `liunian.py` | ✅ `LiunianInfo` |
| 流月（斗君） | `liunian.py` | ✅ `LiuyueInfo` |
| 流日/流时 | `liuri.py` | ✅ `LiuriLiushiBundle`（引擎可选） |
| 飞星盘 | `flying.py` | ✅ |
| 格局检测 | `patterns.py` | ✅ 含庙旺/煞星/大限化忌冲本命 |
| 小限 | `__init__.py` | ✅ standard 默认 |
| 缺失追踪 | `ZiweiChart` | ✅ `missing_fields` / `engine_warnings` |
| 身宫标记 | `PalaceInfo` | ✅ `is_body_palace`（白虎守身等） |

---

## 3. Phase 修复对照

| 编号 | 任务 | 状态 |
|------|------|------|
| Z-P0-01 ~ Z-P0-05 | 日支/安星/流年/斗君/router | ✅ |
| Z-P1-01 | `LiuyueInfo` | ✅ |
| Z-P1-02 | `missing_fields` | ✅ |
| Z-P1-03 | `is_body_palace` | ✅ |
| Z-P1-04 | 小限 standard | ✅ |
| Z-P1-05 | 真太阳时异常 | ✅ warning + missing |
| Z-P1-06 | 月德星 | ✅ 全书口径「子宫起子顺数至年太岁」；同期补 **天德**（酉宫起子） |
| Z-P2-01 | 流日/流时 | ✅ 引擎参数 `flow_*` |
| Z-P2-02 | 格局增强 | ✅ |
| Z-P2-03 | 大限化忌冲本命 | ✅ |
| Z-P2-04 | 择日天德地支型 | ✅ `zeri_engine` |

---

## 4. 仍存在的 Gap

### 4.1 API 与引擎不一致

| 项 | 状态 | 说明 |
|----|------|------|
| `*_method` / `flow_*` 透传 | ✅ P0 | `/full`、`/demo`、`/batch`、`/flying`、合盘均经 `_ziwei_full_args` |
| `liunian_sihua_method` 默认 | ✅ P0 | 统一为 `year_stem`（引擎 ↔ schema ↔ 文档） |

### 4.2 功能层

| Gap | 严重度 | 说明 |
|-----|--------|------|
| 流日/流时默认关闭 | ✅ P3 | `include_flow_liuri` standard/pro 默认 True |
| 流日/流时 API 响应 | ✅ P3 | 默认可选；独立八字 endpoint 已增 |
| 大限化忌冲本命 | ✅ P1 | 仅检测 `resolve_current_dayun_item` 当前大运 |
| `patterns` 来源追溯 | ✅ P2 | `rule_id` + `evidence_chain` 对齐八字侧 |

### 4.3 结构/展示层

| Gap | 说明 |
|-----|------|
| `analysis` 文本化 | ✅ P3 | 新增 `analysis_structured` 逐宫结构化字段 |
| `structural_summary` | ✅ P4 | `ZiweiChartStructuralSummary` + `PalaceRef` / `SanfangStructure` |
| 博士流曜占位 | ✅ | 大运层 `dayun.boshi_stars` + 宫位 `dayun_boshi` 已实现；杂曜层不重复 |

---

## 5. 测试覆盖（Phase 3）

| 套件 | 覆盖 |
|------|------|
| `test_ziwei_engine.py` | 黄金案例 + Phase 1B/2/3 |
| `test_stars_aux.py` | T-01 |
| `test_decorative.py` | T-02 |
| `test_liunian_doujun.py` | T-03 |
| `test_ziwei_variants.py` | T-04 |
| `test_design_doc_fixtures.py` | T-05 |
| `test_ziwei_api.py` | HTTP 集成 |

---

## 6. 建议后续（Phase 4 之后）

1. ~~扩展 `ZiweiRequest` 暴露 Z-01 ~ Z-05 及 `flow_*` 参数~~ ✅
2. ~~流日/流时 `include_flow_liuri` 默认可选~~ ✅
3. ~~格局 `rule_id` 与 `evidence_chain` 对齐八字侧~~ ✅
4. ~~OpenAPI / `openapi.json` 与前端 `schema.d.ts` 同步~~ ✅（`make sync-frontend-types`）
5. ~~`structural_summary` 纯结构化拆分~~ ✅ P4

---

## 7. 变更记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-06-xx | v1.0 | 初版缺口清单 |
| 2026-07-11 | v2.0 | Phase 0–3 完成后全面更新 |
| 2026-07-11 | v2.1 | P3：flow 默认、analysis_structured、前端 types、博士流曜注释澄清 |
| 2026-07-11 | v2.2 | P4：`structural_summary` 结构化 + `ziwei_structural_summary` 子块 typed |
| 2026-07-11 | v2.3 | 月德全书口径复核通过；新增 **天德** 安星（`stars_aux.py`） |
