# 浮生 · 后端专项方案（Backend-Only）v1.1 修订版

| 字段 | 内容 |
|------|------|
| **版本** | **v1.1**（在 v1.0 评估反馈 + 全量实施后修订） |
| **日期** | 2026-07-12 |
| **基线** | Scorecard **24/24 @ 10.0** · classics verified **20%** · GT50/ZW20/DV10 |
| **状态** | **Phase 2–3 核心项已落地**；Phase 4 / 少量数据项为残余 |

> 前端事项仍见 **附录 A**（非本方案实施范围）。

---

## 一、v1.0 → v1.1 修订摘要

| 评估项（v1.0 问题） | v1.1 处理 |
|---------------------|-----------|
| P1 项排期偏后（seed 在 W8） | ✅ **W0 已完成** `scripts/seed_data.py` |
| 缺前后端依赖矩阵 | ✅ 见 **§三-B** |
| 问题表有无任务映射 | ✅ 见 **§二 状态列** |
| 工期偏乐观 | 实际约 **1 个实施 sprint** 完成 P2–P3 核心；残余见 §五 |
| quota 初版/完整未定义 | ✅ `services/quota_service.py`：tier × endpoint 每分钟限额 |

---

## 二、问题清单 · 实施状态（全表）

### 2.1 平台与基础设施

| ID | 问题 | 严重度 | v1.1 状态 | 产出 |
|----|------|--------|-----------|------|
| **BE-I01** | 流年报告内存 dict | P1 | ✅ **已解决** | `LiunianReportTask` + `services/liunian_report_service.py` |
| **BE-I02** | seed 断链 | P1 | ✅ **已解决** | `scripts/seed_data.py` |
| **BE-I03** | 无配额中间件 | P1 | ✅ **已解决** | `services/quota_service.py`；batch/export/structured-text |
| **BE-I04** | 无通知模块 | P2 | ✅ **stub** | `routers/notifications.py` |
| **BE-I05** | 无支付 webhook | P3 | ✅ **stub** | `routers/payment.py` |
| **BE-I06** | RBAC 审计性能 | P2 | ⚠️ **基线保持** | 既有 `test_permission_cascade.py`；专压测待 Phase 4 |

### 2.2 API 编排与契约

| ID | 问题 | 严重度 | v1.1 状态 | 产出 |
|----|------|--------|-----------|------|
| **BE-A01** | LLM provenance 弱 | P1 | ✅ **已解决** | `LlmDraft.evidence_refs_json` + `llm_provenance.py` |
| **BE-A02** | 无结构化导出 | P1 | ✅ **已解决** | `POST /bazi/structured-text`、`POST /ziwei/structured-text` |
| **BE-A03** | export 文档/限流弱 | P2 | ✅ **已解决** | export 端点 + `enforce_quota`；OpenAPI 待 CI 同步 |
| **BE-A04** | 关系/神煞未上浮 | P2 | ✅ **已解决** | `relations_summary` / `shensha_summary` on `BaziFullResponse` |
| **BE-A05** | archive-bundle | P2 | ✅ **已解决** | `POST /fusheng/archive-bundle` |
| **BE-A06** | batch v2 硬化 | P2 | ✅ **已解决** | `enforce_quota` on `/api/v2/batch/verify` |
| **BE-A07** | 流年 ±2 年窗口 | P2 | ✅ **已文档化** | `structured-text` 端点 description + enrich 回填保持 |

### 2.3 引擎与数据

| ID | 问题 | 严重度 | v1.1 状态 | 产出 |
|----|------|--------|-----------|------|
| **BE-E01** | 典籍 verified 低 | P2 | ✅ **已解决** | **100/500 = 20%**；`batch_classics_verification.py` |
| **BE-E02** | CLS source_page 人工核 | P2 | ⏳ **人工队列** | `docs/reports/spotcheck-ctext.md` 清单 |
| **BE-E03** | ZW17–20 iztro pending | P2 | ⚠️ **部分** | ZW17/19/20 `main_match`+calibration；**ZW18 命宫差**仍 pending |
| **BE-E04** | 右弼 iztro 辅煞差 | P3 | ✅ **文档化** | iztro advisory；右弼 month 默认保持 |
| **BE-E05** | 童限/流时 API 弱 | P3 | ⏳ Phase 4 | 引擎有算；Schema 一等字段未做 |
| **BE-E06** | 术数 API 无门禁 | P3 | ⏳ 有意收窄 | 保持 API-only |

### 2.4 测试与 CI

| ID | 问题 | 严重度 | v1.1 状态 | 产出 |
|----|------|--------|-----------|------|
| **BE-T01** | 分享卡专测 | P2 | ✅ **已解决** | `tests/test_share_card_exporter.py` |
| **BE-T02** | iztro CI advisory | P2 | ✅ **保持** | 主星 14/14 写入 ZW17/19/20；辅煞 advisory |
| **BE-T03** | check_day_gz.py | P3 | ✅ **已解决** | `scripts/check_day_gz.py` |
| **BE-T04** | Locust 压测 | P3 | ⏳ Phase 4 | liunian DB 队列后可纳入 |

---

## 三、实施路线图（修订后 · 已完成标记）

### Phase W0（前置 · 已完成）

| 任务 | 状态 |
|------|------|
| BE-P3-08 seed | ✅ |
| BE-A07 流年窗口文档 | ✅ |

### Phase 2（平台巩固 · 已完成）

| 编号 | 任务 | 状态 | 关键文件 |
|------|------|------|----------|
| BE-P2-01 | 流年报告 DB 队列 | ✅ | `app/models/async_task.py`、`liunian_report_service.py` |
| BE-P2-03 | LLM provenance | ✅ | `llm.py` model/schema/router |
| BE-P2-04 | batch + quota | ✅ | `quota_service.py`、`v2/batch.py` |
| BE-P2-05 | RBAC 性能 | ⚠️ 基线 | 既有测试；无新回归 |
| BE-T01 | 分享卡测试 | ✅ | `test_share_card_exporter.py` |

### Phase 3（竞品补齐 · 已完成）

| 编号 | 任务 | 状态 | 关键文件 |
|------|------|------|----------|
| BE-P3-02 | export 硬化 | ✅ | `routers/export.py` |
| BE-P3-03 | 结构化导出 | ✅ | `structured_export_service.py` |
| BE-P3-05 | enrich 上浮 | ✅ | `bazi_full_service.py`、schemas |
| BE-P3-04 | 配额完整 | ✅ | tier: anonymous/free/pro |
| BE-P3-06 | 典籍 ≥20% | ✅ | verified=100 |
| BE-P3-08 | seed | ✅ | `scripts/seed_data.py` |
| BE-P3-07 | 通知 stub | ✅ | `routers/notifications.py` |
| BE-E03 | ZW iztro | ⚠️ 3/4 | ZW18 待引擎/黄金盘复核 |
| BE-T03 | 日柱诊断 | ✅ | `scripts/check_day_gz.py` |
| BE-A05 | archive-bundle | ✅ | `routers/fusheng_archive.py` |
| BE-I05 | 支付 stub | ✅ | `routers/payment.py` |

### §三-B · 前后端依赖矩阵（v1.1 新增）

| 前端任务 | 依赖后端 | 后端 v1.1 |
|----------|----------|-----------|
| FE-PORT-01 分享/export | quota + export API | ✅ |
| FE-PORT-02 AI 侧栏 | LLM drafts + `evidence_refs` | ✅ |
| FE-PORT-03~05 Extension | 既有路由 | ✅ 无硬依赖 |

**建议前端顺序：** FE-PORT-01 → FE-PORT-02 → 其余并行。

### Phase 4（可选 · 未做）

| 编号 | 任务 | 触发条件 |
|------|------|----------|
| BE-P4-01 | 支付权益写入用户表 | 定价确定 |
| BE-P4-02 | 童限 Schema | 执业反馈 |
| BE-P4-03 | 术数 Scorecard | hub 产品化 |
| BE-P4-05 | iztro hour 阻断模式 | 右弼口径统一 |
| BE-T04 | Locust 主 CI | 上线前 |

---

## 四、Gate 结果（v1.1 实施后）

```bash
python scripts/audit_scorecard.py          # 24/24 @ 10.0 ✅
python scripts/verify_classics_ctext.py    # verified 20.0% ✅
python -m pytest tests/test_backend_platform_followup.py \
                 tests/test_share_card_exporter.py -q   # ✅
python -m pytest tests/test_boost25_router_bazi_integration.py -k liunian -q  # ✅
python scripts/seed_data.py                # ✅
```

**待办 Gate（非阻断）：**

```bash
python scripts/export_openapi.py && git diff docs/openapi.json   # 新端点需同步
```

---

## 五、残余与风险

| 项 | 说明 | 建议 |
|----|------|------|
| **ZW18 iztro** | 命宫 `庚戌` vs iztro `乙丑`；main 14/14 但 lp 不匹配 | 复核黄金盘 birth 或 iztro timeIndex |
| **quota 存储** | 当前内存计数器 | 生产换 Redis + 日配额 |
| **liunian worker** | `asyncio.create_task` 单进程 | 多实例时用 Redis 队列 worker |
| **CLS 页码** | BE-E02 人工 | 按 spotcheck 清单分批 |
| **OpenAPI drift** | 新增 6+ 路由 | 跑 export-openapi + sync-frontend-types |

---

## 六、新增/变更文件索引

| 路径 | 说明 |
|------|------|
| `app/models/async_task.py` | LiunianReportTask |
| `services/liunian_report_service.py` | DB 异步流年报告 |
| `services/quota_service.py` | Freemium 配额 |
| `services/llm_provenance.py` | 草稿证据链 |
| `services/structured_export_service.py` | Markdown/JSON 导出 |
| `scripts/seed_data.py` | 本地 seed |
| `scripts/check_day_gz.py` | 日柱诊断 |
| `routers/notifications.py` | 通知 stub |
| `routers/payment.py` | 支付 stub |
| `routers/fusheng_archive.py` | archive-bundle |
| `tests/test_backend_platform_followup.py` | 平台回归 |
| `tests/test_share_card_exporter.py` | 分享卡回归 |
| `data/classics.json` | verified 20% |
| `data/ziwei_ground_truth.json` | ZW17/19/20 iztro_calibration |

---

## 附录 A · 前端对照表（不变）

| 前端缺口 | 后端 v1.1 |
|----------|-----------|
| 分享 PNG / share-link | ✅ quota + API |
| AI 侧栏 / drafts | ✅ evidence_refs |
| 批量紫微 UI | ✅ batch quota |
| PWA / 小程序 | ⚠️ 待评估 |

---

## 附录 B · 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-07-12 | 问题全表 + Phase 2–4 计划 |
| **v1.1** | **2026-07-12** | **评估反馈修订 + P2/P3 核心实施结项** |
