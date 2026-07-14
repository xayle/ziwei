# T099 · 创作者统计 API（2026-07-14）

| 字段 | 内容 |
|------|------|
| **任务** | T099 / BE-GTM-08 · topic→注册 cohort |
| **状态** | ☑ 通过 |
| **验收** | 仅管理员 RBAC |

## 交付

| 路径 | 说明 |
|------|------|
| `GET /api/v1/creator/stats` | `window_days` 查询；`is_admin` 必填 |
| `services/creator_stats_service.py` | utm cohort + paid 转化 + 漏斗计数 |
| `app/schemas/creator_stats.py` | `creator-stats@0.1` |

## 响应要点

- `topics[]`：`utm_source` / `utm_campaign` / `content_id` → registrations / paid_conversions / conversion_rate
- `funnel[]`：landing_cta / volume_view / share_card_export 等
- 非管理员 → **403**

## 验证

```text
pytest tests/test_creator_stats_t099.py → 4 passed
```
