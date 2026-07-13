# T093 · BE-GTM-06 支付 webhook → entitlement（2026-07-14）

| 字段 | 内容 |
|------|------|
| **任务** | T093 · 沙箱回调写 `User.entitlement` |
| **状态** | ☑ 通过 |
| **验收** | 沙箱回调通 · entitlement 持久化 |

## 交付

| 路径 | 说明 |
|------|------|
| `routers/payment.py` | webhook 写入权益；`user_id` 必填 |
| `services/payment_entitlement_service.py` | plan → free/volume_pass/full_book |
| `tests/test_payment_webhook_t093.py` | 6 passed |

## 计划映射

| plan | entitlement |
|------|-------------|
| `free` | free |
| `volume_pass` / `pass` | volume_pass |
| `full_book` / `pro` / `book` | full_book |

## 沙箱

默认不验签。设 `PAYMENT_WEBHOOK_REQUIRE_SIGNATURE=true` 时返回 501（验签未实现），避免误开真签开关写权益。

## 验证

```text
pytest tests/test_payment_webhook_t093.py → 6 passed
```
