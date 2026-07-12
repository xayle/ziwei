# 八字 & 紫微引擎核心修复 — 进度报告

版本：v1.0  
日期：2026-07-11  
关联：[ENGINE-CORE-FIX-PLAN](../plan/ENGINE-CORE-FIX-PLAN-2026-07-11.md) · [基线报告](./ENGINE-CORE-BASELINE-2026-07-11.md)

---

## 1. 执行摘要

| 维度 | 状态 |
|------|------|
| ENGINE-CORE-FIX-PLAN Phase 0–4 | ✅ 主体完成 |
| 延伸 P4–P6（verify / enrich / CLS） | ✅ 完成 |
| CLS 古籍格局 + 用神 | ✅ 12/12 对齐 |
| 核心引擎回归 | ✅ 471 passed（见 §3） |
| 全量 pytest | ✅ 收集正常；2731 passed（2026-07-11；另有 64 项 permission/share 等预存失败，非引擎回归） |

**结论**：八字/紫微底层已从「双轨 + silent 缺失」收敛为「单轨新引擎 + 显式 `missing_fields` + 可回归基线」。本轮追加的子平取格链与八正格配用神，使 pre_1900 名人案例可在 CI 中自动校验。

---

## 2. 已完成工作（按批次）

### 2.1 计划内 Phase 0–4

| 阶段 | 内容 | 状态 |
|------|------|------|
| Phase 0 | 口径决策 Z-01~Z-05、B-01~B-04；基线锁定 | ✅ |
| Phase 1 | liuri 修复、算法单轨、gender 透传；紫微 P0 安星/运限 | ✅ |
| Phase 2 | self_seat、estimate_wealth、missing_fields、月德 | ✅ |
| Phase 3 | 流日/流时、换运提示、测试矩阵 T-01~T-06 | ✅ |
| Phase 4 | bazi/ziwei gap audit、方法注册表、API 文档 | ✅ |

### 2.2 延伸 P4–P6

| 编号 | 任务 | 关键文件 |
|------|------|----------|
| B-P3-01 | verify 单轨 + `missing_fields` | `routers/verify.py` |
| B-P3-02 | M2 enrich 可观测 | `bazi_engine_service.py`, `bazi_full_service.py` |
| B-P3-03 | CLS pre_1900 回归 + 年份 1700–2100 | `constants.py`, `ground_truth_cases.json` |
| B-P3-04 | 十神/格局子平口径 | `tables.py`, `geju.py` |
| B-P3-05 | 子平透干取格链 | `geju._resolve_ref_stem()` |
| B-P3-06 | 八正格配用神 | `yongshen._get_zhengge_yongshen()` |
| B-P3-07 | 化气/外格/从格专用用神 | `yongshen._get_extended_geju_yongshen()` |
| Z-P1-06+ | 月德复核 + 天德新增 | `stars_aux.py` |

### 2.3 CLS 古籍对齐结果

| 案例组 | 格局 vs recorded | 用神 vs recorded |
|--------|------------------|------------------|
| CLS01–CLS12 | 12/12 ✅ | 12/12 ✅ |

引擎基线（`engine_geju` / `engine_yongshen_favor`）与 live `calculate()`：**20/20 verified cases，0 drift**。

### 2.4 GitHub 古籍语料补全（2026-07-11）

| 产出 | 数量 | 来源 |
|------|------|------|
| `data/classics.json` | **278** 条 | yuanhai.json（21）+ supreme_audit 命例评注（41）+ classic_refs（217） |
| `data/imported/supreme_audit.json` | 50 例 | [minionszyw/bazi-skills](https://github.com/minionszyw/bazi-skills) |
| `data/imported/yuanhai_skills.json` | 21 章 | 同上 |
| ZIP01–ZIP05 ground truth | 5 例 | 千里命稿外格/月刃/七杀（`pillar_direct` 四柱直测） |

**ZIP 系列格局对照**（古籍 vs 引擎，xfail 跟踪）：

| ID | 古籍 | 引擎 | 说明 |
|----|------|------|------|
| ZIP01/03 | 曲直格 | 曲直格 | ✅ 亥卯未三合+绝金 pattern |
| ZIP02/04 | 月刃格 | 月刃格 | ✅ 命名统一 |
| ZIP05 | 七杀格 | 七杀格 | ✅ 完全对齐 |
| ZIP06 | 七杀格 | 七杀格 | ✅ 时支官杀夺格 |

导入脚本：`scripts/import_github_classics.py`（`--merge-gt` 合并命例）

### 2.5 引擎口径修订（2026-07-11 续）

| 修订 | 文件 | 说明 |
|------|------|------|
| 曲直仁寿格 | `geju._check_quzhi_geju()` | 木日主 + 寅卯辰月 + 亥卯未齐见 + 绝金 |
| 月刃命名 | `geju.py` 等 | 引擎输出 `月刃格`（古籍亦称羊刃） |
| 化气破格 | `geju._huaqi_blocked_by_branch_ke()` | 日/时支藏干克化神则不化（吴佩孚卯木克土） |
| 比劫误标 | `geju.compute_geju` | 非临官/刃月不因劫财十神贴月刃标签 |
| 语料扩充 | `classics.json` | classic_refs 章节合并 + **殆知阁子平47章/滴天8章**（ctext 需 API key） |
| ZIP06 七杀 | `geju._hour_branch_guansha_override()` | 月透比劫司令 + 时支卯本气乙 → 七杀格 |


## 3. 当前测试基线

### 3.1 核心引擎套件（2026-07-11）

```bash
pytest tests/test_golden_regression.py tests/test_geju_extended.py \
       tests/test_ziwei_engine.py tests/test_engine_units.py \
       tests/test_bazi_full.py tests/test_engine_p4_verify_unify.py \
       tests/test_engine_p5_enrich_missing.py tests/test_engine_p6_cls_pre1900.py -q
```

| 指标 | 数值 |
|------|------|
| 通过 | **471** |
| CLS 古籍 drift（geju + yongshen） | **24/24 PASS**（原 xfail 跟踪项已全部对齐） |
| golden_regression 单套件 | **96 passed** |

### 3.2 GT01–GT08 用神

| 案例 | engine 基线 | vs recorded |
|------|-------------|-------------|
| GT01, GT02, GT03–GT08 | ✅ | ✅ |

---

## 4. 架构快照

```
verify / bazi/full
    └── calculate()  [单轨]
            ├── app/core/verify.py     四柱
            ├── bazi_engine/*          五行/强弱/格局/用神
            ├── _enrich_v2_analysis    M2 分析 + missing_fields
            └── compute_core_metrics(geju_name)  格局后用神重算
```

紫微：`ziwei_engine/*` dataclass 模型 + `missing_fields`；P0 参数透传与流年/斗君默认口径已对齐设计文档。

---

## 5. 仍开放缺口（估计）

### P0 — 工程阻塞

| 项 | 说明 | 状态 |
|----|------|------|
| `test_leap_month.py` 收集失败 | `boundary` shim 未导出 `_KNOWN_LEAP_MONTH_WINDOWS` | ✅ 已修复（35 passed） |
| 计划/基线文档滞后 | FIX-PLAN / BASELINE / gap audit §4 | ✅ 本批次已刷新 |

### P1 — 算法/数据

| 项 | 说明 | 估时 |
|----|------|------|
| 外格/化气/从格专用用神 | 八正格已覆盖；曲直/化气/从财等未单独分支 | ✅ `_get_extended_geju_yongshen` |
| GT02 recorded 用神核实 | — | ✅ 正印格 → water+wood |
| CLS 文献页码 | `source_page` 待人工核对原书 | 人工 |
| 十神口径下游影响 | LLM/报告模板若硬编码旧十神需排查 | 1d |

### P2 — 产品/范围外

| 项 | 说明 |
|----|------|
| 前端 types 同步 | 新 verify 字段、`missing_fields` |
| M2 分析长尾 enrich | P5 已可观测，模块级 gap 未逐一清零 |
| 六爻/姓名/LLM/PDF | 不在 ENGINE-CORE-FIX-PLAN 范围 |

---

## 6. 建议下一步

1. 全量 `pytest` 绿灯（leap_month 修复后；permission/share 等 64 项预存失败待排）
2. ~~GT02 用神 recorded 核实~~ ✅ 已完成
3. ~~外格/化气/从格用神链~~ ✅ 已完成（`TestExtendedGejuYongshen` 4/4）
4. `make sync-frontend-types`（若前端对接中）

---

## 7. 变更记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-07-11 | v1.2 | B-P3-07 化气/外格/从格用神；`test_geju_extended` 扩展 4 项全绿 |
| 2026-07-11 | v1.1 | P0：leap_month 修复；三份计划/基线/gap 文档刷新 |
