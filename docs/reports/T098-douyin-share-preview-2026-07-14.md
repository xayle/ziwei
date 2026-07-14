# T098 · 竖版分享预览 + 导出（2026-07-14）

| 字段 | 内容 |
|------|------|
| **任务** | T098 / FE-GTM-07 · 竖版分享预览 + 导出 |
| **状态** | ☑ 通过 |
| **验收** | 纸纹 + 卷名 + 事实句 |

## 交付

| 路径 | 说明 |
|------|------|
| `api/exportCard.ts` | `downloadCaseShareCard(layout=douyin)` |
| `components/fusheng/DouyinShareCard.vue` | 9:16 预览 · 导出 PNG · `share_card_export` 埋点 |
| `ReportView.vue` | snippets/卷一事实句驱动预览；有 case 可导出 |
| `LandingVolume.vue` | 示意预览（无 case 不导出） |

## 验证

```text
npm run test -- DouyinShareCard → 2 passed
E2E douyin-landing 含 douyin-share-preview
```
