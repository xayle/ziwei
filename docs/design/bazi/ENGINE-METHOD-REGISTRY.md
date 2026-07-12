# 八字引擎方法注册表

版本：v1.0  
日期：2026-07-11  
状态：**已确认（Phase 0–4）**

---

## 决策总表

| 编号 | 争议点 | 决策 | 执行 Phase |
|------|--------|------|------------|
| B-01 | wuxing / strength / yongshen | **统一为 `services/bazi_engine/` 新引擎** ✅ | 1 完成 |
| B-02 | self_seat（自坐） | **十二长生**（本柱天干×地支） ✅ | 2 完成 |
| B-03 | 财富估算 | **接入 `estimate_wealth`** ✅ | 2 完成 |
| B-04 | ENGINE_V2 | **四柱层已切换至 `bazi_engine.pillars.v2`**；flag 控制 API 代际 | 4 完成 |
| B-05 | 流日/流时 | **`liuri.py` 最小实现** + `liuri_liushi` 响应 ✅ | 3 完成 |
| B-06 | 换运提示 | **`start_age_days` + `transition_hint`** ✅ | 3 完成 |

---

## B-01 五行 / 强弱 / 用神

### 权威模块

| 字段 | 模块 |
|------|------|
| `wuxing_score` | `services/bazi_engine/wuxing.py` |
| `day_master_strength` | `services/bazi_engine/strength.py` |
| `yongshen` | `services/bazi_engine/yongshen.py` |

统一入口：`services/bazi_full_service.py::compute_core_metrics()`（内部委托上述引擎模块）。

`_calculate_v1` 与 `bazi/full` 均经 `compute_core_metrics` 填充五行/强弱/用神，不再存在 legacy shim。

---

## B-02 自坐（self_seat）

- **年 / 月 / 日 / 时柱**：该柱天干 × 该柱地支 → 十二长生名
- **大运 / 流年柱**：大运/流年天干 × 对应地支 → 十二长生名
- 无法计算时：`self_seat: null` + `missing` 含 `"self_seat"`，**禁止**无说明的 `"缺失"` 硬编码

**Phase 2 状态**：✅ 已实现（年/月/日/时/大运/流年全柱）

已有参考：`bazi_full_service._pillar_self_seat()`、`STAGE_NAMES`

---

## B-03 财富估算

- 权威：`services/bazi_engine/analysis/wealth_estimate.py::estimate_wealth`
- 接入点：`bazi_engine_service._enrich_v2_analysis` 或 `_calculate_v1` 财富区间段
- 删除与 `estimate_wealth` 重复的内联系数逻辑

**Phase 2 状态**：✅ `_calculate_v1` 大运 enrich 已接入

---

## B-05 流日 / 流时

- 权威：`services/bazi_engine/liuri.py::get_liuri_liushi`
- 触发：`BaziFullRequest.target_date`（可选 `target_hour`）
- 响应：`BaziFullResponse.liuri_liushi`
- 口径：日柱由公历日期推 60 甲子；时柱五鼠遁；十神相对本命日干

**Phase 3 状态**：✅ 最小实现（未含运限联动评分）

---

## B-06 换运提示

- 字段：`dayun.start_age_days`、`dayun.transition_hint`
- 来源：`services/bazi_engine/dayun.py` + `bazi_full_service.build_dayun`

**Phase 3 状态**：✅

## B-04 ENGINE_V2

| 项 | 说明 |
|----|------|
| 环境变量 | `ENGINE_V2=true`（默认，见 `app/config.py`） |
| 四柱层 | **一律**经 `services.bazi_engine.pillars.compute_pillars()` |
| `pillars_layer` | 响应 `methods.pillars_layer` = `bazi_engine.pillars.v2` |
| `engine_version` | `ENGINE_V2=true` → `v2`；`false` → `v1`（四柱层相同） |
| API v2 门闸 | `/api/v2/*` 在 `ENGINE_V2=false` 时返回 501 |
| v1 shim | `app/core/verify.verify_full` 仍委托同一 pillars 实现（兼容） |

---

## 四柱 / 真太阳时

| 项 | 权威模块 |
|----|----------|
| 四柱计算（v2 权威） | `services/bazi_engine/pillars.py` |
| 四柱计算（v1 shim） | `app/core/verify.py` → 委托 pillars |
| 真太阳时 | `services/bazi_engine/solar_time_v2.py`（含 EoT） |
| 废弃 | `app/core/solar_time.py`（仅经度修正，无 EoT）— 不得在新代码中引用 |

---

## B-07 格局双轨（geju dual_track）

ZIP09 等边界案例在 `geju` 块暴露双轨字段（非嵌套 `geju.dual_track` 对象）：

| 字段 | 含义 |
|------|------|
| `dual_track_id` | 如 `ZIP09` — 引擎格局 vs 录盘格局分歧标识 |
| `dual_track_note` | 人读说明；Report 互证章展示，**不覆盖 canonical 主盘** |

验收：`pytest tests/test_geju_api_payload.py tests/test_bazi_dual_track.py`

---

## 变更记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-07-11 | v1.0 | Phase 0 口径确认 |
| 2026-07-12 | v1.2 | B-04：四柱层正式切换，`pillars_layer` 暴露至 API |
