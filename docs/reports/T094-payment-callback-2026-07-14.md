# T094 · 支付成功刷新 entitlement（2026-07-14）

| 字段 | 内容 |
|------|------|
| **任务** | T094 · 支付回调页刷新权益并解锁卷三~五 |
| **状态** | ☑ 通过 |
| **验收** | 回调后卷目可展开 |

## 交付

| 路径 | 说明 |
|------|------|
| `views/payment/PaymentCallbackView.vue` | `/payment/callback?plan=volume_pass` |
| `stores/entitlement.ts` | `refreshFromServer` · `sandboxPurchase` |
| `api/auth.ts` | `fetchAuthMe` · `postSandboxPaymentWebhook` |
| `ReportView.vue` | 权益解锁覆盖 · `?unlocked=1` 重拉 volumes |
| `VolumePaywall.vue` | 登录态模拟解锁调沙箱 webhook |

## 流程

```text
登录 → /payment/callback?plan=volume_pass
  → POST /payment/webhook（T093）
  → GET /auth/me
  → /report?unlocked=1#report-volume-vol3
```

## 验证

```text
npm run test -- entitlement PaymentCallback VolumePaywall → 6 passed
```
