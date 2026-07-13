# T088 · BE-GTM-02 utm 归因（2026-07-14）

| 字段 | 内容 |
|------|------|
| **任务** | T088 · `utm_source` / `utm_campaign` / `content_id` |
| **状态** | ☑ 通过 |
| **验收** | 注册/建档可存抖音视频 ID · auth/me 回传 |

## 交付

| 路径 | 说明 |
|------|------|
| `app/schemas/utm.py` | `UtmAttributionFields` 校验 |
| `app/models/base.py` · `case.py` | User / Case 列 |
| `migrations/.../h8c9d0e1f2a3_*.py` | users + cases 加列 |
| `routers/auth.py` | register 写入 · `/auth/me` 回传 |
| `routers/cases.py` | 建档写入；缺省继承用户首触 |
| `tests/test_utm_attribution_t088.py` | 6 passed |

## 验证

```text
pytest tests/test_utm_attribution_t088.py → 6 passed
```
