# T092 · FE-GTM-03 卷锁定态 UI（2026-07-14）

| 字段 | 内容 |
|------|------|
| **任务** | T092 · locked 卷显示锁 + 付费墙文案（可 mock） |
| **状态** | ☑ 通过 |
| **验收** | locked 卷显示锁+说明 · 沙箱模拟解锁 |

## 交付

| 路径 | 说明 |
|------|------|
| `components/fusheng/VolumePaywall.vue` | 锁印 + 档位说明 + 模拟解锁 CTA |
| `components/fusheng/VolumeSection.vue` | `locked` 节样式强化 |
| `constants/volumePaywall.ts` | 文案 · `fusheng-demo-volume-locks=1` 演示开关 |
| `views/ReportView.vue` | `volume.locked` / demo 锁 → 付费墙；mock 解锁本会话 |

## 演示

```text
localStorage.setItem('fusheng-demo-volume-locks', '1')
# 刷新报告页 → vol2–vol6 显示付费墙；点「模拟解锁」仅本会话打开该卷
```

真实支付写入 entitlement 见 **T093**。

## 验证

```text
npm run test -- VolumePaywall → 绿
vue-tsc --noEmit → 绿
```
