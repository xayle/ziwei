# T096 · 钩子句一键复制（2026-07-14）

| 字段 | 内容 |
|------|------|
| **任务** | T096 / FE-GTM-04 · 钩子句复制（接 T076 snippets） |
| **状态** | ☑ 通过 |
| **验收** | 一键复制拍视频 |

## 交付

| 路径 | 说明 |
|------|------|
| `api/life.ts` | `fetchLifeSnippets` |
| `components/fusheng/SnippetHooksPanel.vue` | 单条/全部复制 + funnel 埋点 |
| `utils/copyText.ts` | clipboard 封装 |
| `ReportView.vue` | 登录且有 case 时拉取 snippets 展示 |
| `LandingVolume.vue` | 示意钩子句（无实盘）可复制 |
| `constants/landingHooks.ts` | 落地页示例句 |

## 流程

```text
Report：登录+remoteCase → GET /life/snippets → 复制字幕
Landing：示意 3 句 → 复制全部/单条 → funnel_step snippet_copy
```

## 验证

```text
npm run test -- SnippetHooksPanel copyText → passed
E2E douyin-landing 含 snippet-hooks 可见
```
