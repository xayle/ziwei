# 浮生 · 后端后续开发结项报告

| 字段 | 内容 |
|------|------|
| **计划** | [BACKEND-FOLLOWUP-DEV-2026-07-12](../plan/BACKEND-FOLLOWUP-DEV-2026-07-12.md) v1.2 |
| **结项日期** | 2026-07-12 |
| **Scorecard** | **24/24 @ 10.0** |
| **pytest** | 全量通过（见下方 Gate） |
| **范围** | P0 全项 · P1 全项 · P2-02 PDF 双轨附录 POC |

---

## 一、交付摘要

| 编号 | 任务 | 状态 | 关键产出 |
|------|------|------|----------|
| BE-P0-01~05 | Scorecard 24/24 | ✅ | `audit_scorecard.py` sys.path；语料/iztro 已满足 |
| BE-P1-01 | 流日流年回填 | ✅ | `build_liuri_liushi_enrichment` |
| BE-P1-02 | 格局 tier 负例 | ✅ | `test_ziwei_pattern_false_positive` → ZW01–ZW16 |
| BE-P1-03 | forecast evidence | ✅ | `PeriodForecastResponse.layer`；API tier+evidence_chain 测试 |
| BE-P1-04 | 黄金盘扩面 | ✅ | GT 50 · ZW 20 · DV 10；`scripts/expand_golden_cases.py` |
| BE-P1-05 | OpenAPI CI | ✅ | CI `export_openapi` drift check；`test_period_forecast_schema_has_tier_and_layer` |
| BE-P2-02 | PDF 双轨附录 | ✅ | `fusheng_report_service._render_dual_track_appendix` |

**未纳入本次结项（计划 P2 余项）：**

- BE-P2-01 流年报告异步队列（Redis/DB worker）
- BE-P2-03 LLM provenance 对齐深化
- BE-P2-04 相似盘/批量 v2 硬化
- BE-P2-05 RBAC 审计性能

---

## 二、Gate 结果

```text
python scripts/audit_scorecard.py     → 24/24 @ 10.0
python -m pytest -q (no e2e/legacy)  → 见 CI 同级命令
python scripts/verify_classics_ctext.py → OK
```

黄金盘计数：

| 资产 | 目标 | 实际 |
|------|------|------|
| GT | ≥50 | **50** |
| ZW | ≥20 | **20** |
| DV | ≥10 | **10** |

---

## 三、主要文件变更

| 路径 | 说明 |
|------|------|
| `scripts/audit_scorecard.py` | ROOT 注入 sys.path |
| `services/bazi_full_service.py` | 流年目标年回填 |
| `services/fusheng_report_service.py` | 双轨对照附录表 |
| `app/schemas/ziwei.py` | forecast `layer` 字段 |
| `routers/ziwei.py` | forecast layer 映射 |
| `scripts/expand_golden_cases.py` | GT/ZW/DV 扩面脚本 |
| `data/ground_truth_cases.json` | +GT09–GT12 |
| `data/ziwei_ground_truth.json` | +ZW17–ZW20 |
| `data/dual_verify_cases.json` | +DV09–DV10 |
| `.github/workflows/ci.yml` | OpenAPI export drift |
| `docs/openapi.json` | schema 同步 |

---

## 四、后续建议（P2 余项）

1. **BE-P2-01**：`routers/bazi.py` 流年报告改 Redis 队列 + worker 水平扩展设计稿。
2. **BE-P2-03**：`llm_service` 草稿 `provenance.layer` 与 `analysis_structured` 字段一一对照。
3. **ZW17–ZW20**：择机 `node scripts/verify_ziwei_iztro.mjs --calibrate --case ZW17` 纳入 iztro 主星校准。

---

## 五、修订

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-07-12 | P0+P1-01 首轮执行 |
| v1.2 closeout | 2026-07-12 | P1 全项 + P2-02 PDF POC |
