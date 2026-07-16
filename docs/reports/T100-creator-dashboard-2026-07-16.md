# T100 · 创作者 Dashboard FE（2026-07-16）

| 字段 | 内容 |
|------|------|
| **任务** | T100 / FE-GTM-05 · 创作者 Dashboard |
| **状态** | ☑ 通过 |
| **依赖** | T099 `GET /api/v1/creator/stats` |

## 交付

| 路径 | 说明 |
|------|------|
| `/creator` | `CreatorDashboardView.vue` |
| `api/creatorStats.ts` | 拉取 stats + 转化率格式化 |
| Vitest | `api/__tests__/creatorStats.spec.ts` |

## 行为

- 未登录 → 跳转登录（带 redirect）
- 非管理员 / 403 → 明确提示，不展示表
- 管理员 → 汇总、漏斗条、主题转化表；窗口 7/14/30/90 天

## 验证

```text
cd frontend && npm run test -- --run src/api/__tests__/creatorStats.spec.ts
```
