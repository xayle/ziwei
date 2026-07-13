# T091 · FE-GTM-01 LandingVolume（2026-07-14）

| 字段 | 内容 |
|------|------|
| **任务** | T091 · 抖音落地页卷首摘要 + CTA 建档 |
| **状态** | ☑ 通过 |
| **验收** | 375px 无横滚 · Vitest + E2E 绿 |

## 交付

| 路径 | 说明 |
|------|------|
| `views/landing/LandingVolume.vue` | 无壳落地页：品牌 · 卷首 · CTA · disclaimer |
| `constants/landingVolume.ts` | 试读文案 |
| `utils/utmCapture.ts` | 查询参数 → sessionStorage（对齐 T088） |
| `e2e/douyin-landing.spec.ts` | 375px 无横滚 + CTA 透传 utm |
| 路由 `/landing` | `meta.public` · App 裸渲染 |

## 验证

```text
npm run test -- LandingVolume utmCapture → 5 passed
npx playwright test e2e/douyin-landing.spec.ts → 2 passed
```
