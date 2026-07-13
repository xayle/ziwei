# T087 · 卷目 locked 规则（2026-07-14）

| 字段 | 内容 |
|------|------|
| **任务** | T087 · Q2：卷0–1 免费，2–4 pass，5–6 full_book |
| **状态** | ☑ 通过 |
| **前置** | T086 entitlement |

## 交付

| 路径 | 说明 |
|------|------|
| `services/life_volume_service.py` | `_apply_volume_locks` · 锁定卷改为占位节 |
| `routers/life.py` | `resolve_entitlement(user=)` 传入生成逻辑 |
| `tests/test_life_volume_locks_t087.py` | fixture 覆盖 free/pass/full_book |

## 行为

- `locked=true` 的卷不返回原文 sections，仅「本卷未解锁」占位（防 payload 泄露）
- `owner` / `admin` / `AUTH_BYPASS` → `full_book`（与 T086 一致，本地 E2E 仍全开）
- FE 锁墙 UI 仍属 **T092**

## 验证

```text
pytest tests/test_life_volume_locks_t087.py tests/test_life_volumes_api.py → 绿
```
