# 八字 & 紫微引擎核心基线报告

日期：2026-07-11  
环境：Windows · Python 3.14.0 · pytest 8.4.2  
关联计划：[ENGINE-CORE-FIX-PLAN-2026-07-11.md](../plan/ENGINE-CORE-FIX-PLAN-2026-07-11.md)

---

## 1. 口径决策状态

| 文档 | 状态 |
|------|------|
| [紫微方法注册表](../design/ziwei/ENGINE-METHOD-REGISTRY.md) | ✅ v1.0 已确认 |
| [八字方法注册表](../design/bazi/ENGINE-METHOD-REGISTRY.md) | ✅ v1.0 已确认 |

**默认原则**：紫微安星/运限以 `docs/design/ziwei/` 为准；八字计算以 `services/bazi_engine/` 新引擎为准。

---

## 2. 已知阻塞问题

| 问题 | 验证命令 | 修复前 | 修复后（B-P0-01） |
|------|----------|--------|-------------------|
| `liuri.py` 语法损坏 | `python -c "import services.bazi_engine.liuri"` | ❌ SyntaxError | ✅ 可 import |

---

## 3. 回归测试结果

### 3.1 核心套件 A（2026-07-11 刷新）

```bash
pytest tests/test_golden_regression.py tests/test_ziwei_engine.py tests/test_geju_v2.py -q
```

| 指标 | 数值（Phase 4 后） | 数值（P4–P6 后） |
|------|-------------------|------------------|
| golden_regression | 148/149 | **96/96** |
| 失败 | GT04 用神 | **0** |
| CLS 古籍 drift | xfail 跟踪 | **24/24 PASS** |

### 3.2 核心引擎组合（P4–P6 后）

```bash
pytest tests/test_golden_regression.py tests/test_geju_extended.py \
       tests/test_ziwei_engine.py tests/test_engine_units.py \
       tests/test_bazi_full.py tests/test_engine_p4_verify_unify.py \
       tests/test_engine_p5_enrich_missing.py tests/test_engine_p6_cls_pre1900.py -q
```

| 指标 | 数值 |
|------|------|
| 通过 | **457+** |
| 失败 | **0** |

### 3.3 核心套件 B

```bash
pytest tests/test_golden.py tests/test_bazi_full.py -q
```

| 指标 | 数值 |
|------|------|
| 收集 | 40 |
| 通过 | **40** |
| 失败 | 0 |
| 耗时 | ~0.63s |

---

## 4. 基线摘要

| 模块 | 测试基线 | 已知问题 |
|------|----------|----------|
| 紫微引擎 | 81/81（test_ziwei_engine） | 安星/运限与文档偏差（见方法注册表） |
| 格局 v2 | 32/32（test_geju_v2） | — |
| Golden 四柱+CLS | 96/96 回归 | CLS 格局/用神古籍全对齐 |
| Golden HTTP | 36/36 | — |
| bazi/full | 7/7 | gender 已传 ✅ |
| liuri | 3/3 | ✅ |
| leap_month | 27/27 | ✅ boundary shim 导出修复 |

---

## 5. Phase 0 完成清单

- [x] 紫微口径决策表（Z-01 ~ Z-05）
- [x] 八字口径决策表（B-01 ~ B-04）
- [x] 基线测试运行并记录
- [x] 确认 liuri 损坏为已知 P0 问题 → **B-P0-01 已修复**

**Phase 0 状态：完成**

---

## 6. B-P0-01 修复记录（2026-07-11）

| 项 | 结果 |
|----|------|
| `liuri.py` 语法修复 | ✅ 可 import |
| 玄空飞星代码迁出 | ✅ `services/fengshui_engine/xuankong.py` |
| 新增测试 | ✅ `TestLiuriModule`, `TestXuankongModule`（3 passed） |

```bash
pytest tests/test_engine_units.py::TestLiuriModule tests/test_engine_units.py::TestXuankongModule -q
```

---

## 7. B-P0-02 修复记录（2026-07-11）

| 项 | 结果 |
|----|------|
| `compute_core_metrics()` 统一入口 | ✅ `services/bazi_full_service.py` |
| `_calculate_v1` / `routers/verify.py` 切换 | ✅ |
| 羊刃格用神补食伤 | ✅ `yongshen.py` |
| GT04 用神回归 | ✅ 144/144 核心套件通过 |

**语义变更**：`wuxing_score` 现为 0–100 加权百分比（非 legacy 原始计数）；`day_master_strength.score` 为 0–100 多因子分。

## 8. B-P0-03 修复记录（2026-07-11）

| 项 | 结果 |
|----|------|
| `BaziFullRequest.gender` | ✅ `male` / `female` / `None` |
| `bazi_full()` → `calculate(gender=...)` | ✅ |
| 回归测试 | ✅ 阳年男顺女逆（GT04 案例） |

---

## 10. Phase 1B 修复记录（2026-07-11）

| 任务 | 结果 |
|------|------|
| Z-P0-01 `day_branch_idx` | ✅ `lunar.py` |
| Z-P0-02 昌曲/右弼 | ✅ 默认 hour/month；legacy 参数保留 |
| Z-P0-03 流年命宫 | ✅ 默认 `taisui`（太岁直落） |
| Z-P0-04 斗君流月 | ✅ 默认 `doujun`；`simplified` 可选 |
| Z-P0-05 router | ✅ `branch_idx` 映射修复 |
| 测试 | ✅ 156 passed（含 7 项新回归） |

---

## 11. Phase 2–4 完成记录（2026-07-11）

### Phase 2（P1 结构）

| 模块 | 任务 | 状态 |
|------|------|------|
| 八字 | self_seat、estimate_wealth、city_tier | ✅ |
| 紫微 | LiuyueInfo、missing_fields、小限、月德 | ✅ |

### Phase 3（P2 + 测试矩阵）

| 模块 | 任务 | 状态 |
|------|------|------|
| 八字 | liuri_liushi、换运提示 | ✅ |
| 紫微 | 流日/流时、格局增强、天德地支 | ✅ |
| 测试 | T-01 ~ T-06 | ✅ |

**回归（Phase 3 后）**：286+ 项核心套件通过（ziwei + golden + zeri + engine_units）。

### Phase 4（文档）

| 编号 | 交付物 | 状态 |
|------|--------|------|
| D-01 | `docs/design/bazi/bazi-gap-audit.md` | ✅ |
| D-02 | `docs/design/ziwei/ziwei-gap-audit.md` | ✅ |
| D-03 | 方法注册表 v1.1 | ✅ |
| D-04 | `docs/design/api.md` 同步 | ✅ |
| D-05 | `docs/README.md` 索引 | ✅ |
| D-06 | ENGINE_V2 README + 代码注释 | ✅ |

---

## 13. P4–P6 延伸批次（2026-07-11）

| 任务 | 结果 |
|------|------|
| verify 单轨 + missing_fields | ✅ |
| M2 enrich 可观测 | ✅ |
| CLS pre_1900 + 年份 1700–2100 | ✅ |
| 子平十神 + `_resolve_ref_stem` | ✅ |
| 八正格配用神 | ✅ |
| CLS01–CLS12 格局/用神 vs 袁书 | ✅ 12/12 |
| 月德复核 + 天德 | ✅ |

详见 [ENGINE-CORE-PROGRESS-2026-07-11.md](./ENGINE-CORE-PROGRESS-2026-07-11.md)。

---

## 14. 基线 delta 跟踪

| 日期 | 变更 |
|------|------|
| 2026-07-11 | P4–P6 完成；golden 96/96；GT04 用神已绿；leap_month 收集修复 |
