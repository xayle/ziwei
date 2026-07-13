# T086 · BE-GTM-05 entitlement 模型（2026-07-14）

| 字段 | 内容 |
|------|------|
| **任务** | T086 · `free` / `volume_pass` / `full_book` |
| **状态** | ☑ 通过 |
| **验收** | schema + `enforce_entitlement` 可校验 · 单测绿 · `auth/me` 回传 |

## 交付

| 路径 | 说明 |
|------|------|
| `app/schemas/entitlement.py` | `EntitlementTier` · Q2 卷目门槛表 · `EntitlementInfo` |
| `services/quota_service.py` | `resolve_entitlement` · `enforce_entitlement` · `require_entitlement_dependency` · `is_volume_unlocked` |
| `app/models/base.py` | `User.entitlement` 默认 `free` |
| `migrations/versions/g7b8c9d0e1f2_*.py` | users.entitlement 列 |
| `routers/auth.py` | `/auth/me` 含 `entitlement` + `entitlement_info` |
| `tests/test_entitlement_t086.py` | 8 passed |

## Q2 解锁映射（供 T087）

| 档位 | 可展开 |
|------|--------|
| `free` | preface · vol1 · colophon |
| `volume_pass` | + vol2–vol4 |
| `full_book` | + vol5–vol6 |

admin / owner / `AUTH_BYPASS` → 运行时升至 `full_book`。

## 未做（后续编号）

- **T087** 写入 `life/volumes[].locked`
- **T093** 支付 webhook 持久化 entitlement

## 验证

```text
pytest tests/test_entitlement_t086.py → 8 passed
```
