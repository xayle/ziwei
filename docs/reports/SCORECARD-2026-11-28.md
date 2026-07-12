# 10.0 Scorecard — Phase G 最终审计报告

**日期**：2026-11-28（更新 2026-07-12）  
**生成**：`python scripts/audit_scorecard.py` / `make scorecard`  
**JSON**：`docs/reports/scorecard-latest.json`  
**Gate G-G**：**通过** — 24/24 项 = 10.0

---

## 1. 总览

| 指标 | 值 |
|------|-----|
| Overall | **10.0 / 10** |
| 八字均值 (B-01~10) | **10.0** |
| 紫微均值 (Z-01~10) | **10.0** |
| 交叉项均值 (X-01~04) | **10.0** |
| 通过项 | **24 / 24** |
| GT 八字用例 | 42 |
| ZW 紫微用例 | 12（ZW01–ZW12，ZW09–12 iztro 主星 14/14） |
| GT 标签对齐率 | **100%**（含双轨登记） |
| 核心 pytest | PASS（含 golden / geju / ziwei / solar_zi） |
| dual_verify | **5 人**（DV01–DV05） |

---

## 2. 24 项明细

| ID | 名称 | 分数 | 状态 |
|----|------|------|------|
| B-01 | 四柱排盘与历法边界 | 10.0 | PASS |
| B-02 | 五行旺衰/日主强弱 | 10.0 | PASS |
| B-03 | 格局判定 | 10.0 | PASS |
| B-04 | 用神喜忌 | 10.0 | PASS |
| B-05 | 大运流年 | 10.0 | PASS |
| B-06 | 合冲刑害/神煞 | 10.0 | PASS |
| B-07 | 古籍语料 | 10.0 | PASS |
| B-08 | 黄金用例 | 10.0 | PASS |
| B-09 | 分析断语层 | 10.0 | PASS |
| B-10 | 八字产品呈现 | 10.0 | PASS |
| Z-01 | 安星诀 | 10.0 | PASS |
| Z-02 | 宫位/命宫身宫/五行局 | 10.0 | PASS |
| Z-03 | 四化体系 | 10.0 | PASS |
| Z-04 | 大限流年流月流日 | 10.0 | PASS |
| Z-05 | 格局判定 | 10.0 | PASS |
| Z-06 | 飞星/叠宫 | 10.0 | PASS |
| Z-07 | 断语与分析层 | 10.0 | PASS |
| Z-08 | 黄金用例 | 10.0 | PASS |
| Z-09 | 流派参数/真太阳时 | 10.0 | PASS |
| Z-10 | 紫微产品呈现 | 10.0 | PASS |
| X-01 | 体系统合 | 10.0 | PASS |
| X-02 | 可信度分层标注 | 10.0 | PASS |
| X-03 | 执业就绪度 | 10.0 | PASS |
| X-04 | 学术严谨度 | 10.0 | PASS |

---

## 3. Phase A–G 交付核对

| Phase | Gate | 关键交付 | 状态 |
|-------|------|----------|------|
| A | G-A | scorecard、ProvenanceLayer、ZW01–08、solar_zi 边界 | ✅ |
| B | G-B | 外格结构、破格救应、ZIP17–22、大运流年联动 | ✅ |
| C | G-C | patterns ZRULE_043–050、叠宫 forecast、8 盘满测 | ✅ |
| D | G-D | classical_narrative、紫微 COMBO_TABLE、语料软链 | ✅ |
| E | G-E | Fusheng 四化/时间轴/典籍链、Report 增强 | ✅ |
| F | G-F | 24/24 ≥9.5、dual_verify、PRODUCT 执业声明 | ✅ |
| G | G-G | stretch_perfect 门、ZW12+、DV5、ctext 门禁、10.0 | ✅ |

---

## 4. Tier-2 stretch 门（9.5 → 10.0）

每项在基线验证通过后，额外 `stretch_perfect` 检查（+0.5）：

| 域 | 代表门 |
|----|--------|
| 八字 | `pillars_layer` API、`dual_track` 注册表、合盘飞星化忌、`zi_day_rule` 档案同步 |
| 紫微 | ZW≥12、DV≥5、`ZiweiFlyingTab`、`brightness_method`/`youbi_method` 透传 |
| 语料 | `ziwei_classic_refs` 100+、`verify_classics_ctext.py` 门禁 |
| 交叉 | Report 双轨 UI、ENGINE-METHOD-REGISTRY v1.2 |

---

## 5. 仍须双轨展示的口径

| ID | recorded | engine | 产品要求 |
|----|----------|--------|----------|
| ZIP09 | 从官杀格 | 七杀格 | Report 双口径说明（见 PRODUCT.md） |
| ZIP21 | 食神制杀格 | 七杀格 | `derived_geju` 对照 |
| ZIP22 | 伤官佩印格 | 伤官格 | 同上 |
| ZIP01 | 土火 | 水木 | 用神双轨（notes 已登记） |
| ZIP04 | 金 | 土火金 | 用神双轨（notes 已登记） |
| ZIP05 | 火 | 火水 | 用神双轨（notes 已登记） |

---

## 6. 验证命令

```bash
make scorecard
make verify-classics-ctext

python -m pytest \
  tests/test_golden_regression.py \
  tests/test_geju_extended.py \
  tests/test_ziwei_golden_regression.py \
  tests/test_dual_verify_cases.py \
  tests/test_solar_zi_boundary.py \
  tests/test_import_classics_corpus.py \
  tests/test_ziwei_engine.py -q

python scripts/import_github_classics.py --merge-gt
```

---

## 7. 结论

**北极星达成**：全项 10.0 目标完成；`audit_scorecard.py` 24/24 stretch 门通过，综合评分 **10.0**，可进入发布候选。
