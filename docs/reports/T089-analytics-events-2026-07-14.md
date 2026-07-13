# T089 · BE-GTM-01 analytics events（2026-07-14）

| 字段 | 内容 |
|------|------|
| **任务** | T089 · `POST /api/v1/analytics/events` |
| **状态** | ☑ 通过 |
| **验收** | 批量卷目阅读/术语点击可落库；PII 键剥离 |

## 交付

| 路径 | 说明 |
|------|------|
| `routers/analytics_events.py` | 批量埋点端点（可匿名） |
| `services/analytics_events_service.py` | 写入 `analytics_events` |
| `app/schemas/analytics_events.py` | 事件类型 + `scrub_properties` |
| `app/models/analytics_event.py` | 表模型 |
| `migrations/.../i9d0e1f2a3b4_*.py` | 建表 |
| `tests/test_analytics_events_t089.py` | 4 passed |

## 事件类型

`volume_view` · `volume_dwell` · `volume_unlock_prompt` · `glossary_click` · `term_click` · `funnel_step` · `share_card_export` · `landing_cta_click`

## PII

`properties` 中 `name` / `birth_*` / `email` / `phone` 等键会被剥离，并出现在响应 `scrubbed_pii_keys`（对齐 T090 FE 禁令）。

## 验证

```text
pytest tests/test_analytics_events_t089.py → 4 passed
```
