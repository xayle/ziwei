# T090 · FE-GTM-06 analytics.ts（2026-07-14）

| 字段 | 内容 |
|------|------|
| **任务** | T090 · `utils/analytics.ts` 封装 |
| **状态** | ☑ 通过 |
| **验收** | 禁姓名/生日进 payload · Vitest 隐私用例绿 |

## 交付

| 路径 | 说明 |
|------|------|
| `frontend/src/utils/analytics.ts` | `track` / `flushAnalytics` / 卷目&术语快捷方法 |
| `frontend/src/utils/__tests__/analytics.spec.ts` | PII scrub + POST body 无姓名/生日 |
| `frontend/src/api/openapiTypes.ts` | Analytics* 类型 re-export |

## 隐私

- `scrubAnalyticsProperties` 剥离 `name` / `birth_*` / `email` / `phone` 等
- 发送前断言：POST body **不含**上述键（单测覆盖）
- 埋点失败静默，不打断主流程

## 验证

```text
cd frontend && npm run test -- src/utils/__tests__/analytics.spec.ts → 4 passed
```
