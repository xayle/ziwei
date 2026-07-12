# 浮生 · 字体子集（F1-4 / T013）

| 字段 | 内容 |
|------|------|
| **定案** | [FUSHENG-DESIGN-MASTERPLAN.md](../../../docs/design/FUSHENG-DESIGN-MASTERPLAN.md) §三 |
| **执行** | T013（方案）· T021（@font-face 上线） |

---

## 字体栈（已在 `variables.css`）

| Token | 栈 | 用途 |
|-------|-----|------|
| `--font-display` | LXGW Neo ZhiSong → Source Han Serif SC → STSong | 卷名、干支、典籍引文 |
| `--font-ui` | 系统无衬线（PingFang / 微软雅黑 / Segoe UI） | 导航、按钮、表头、脚注 |
| `--font-mono` | JetBrains Mono → Consolas | 版本号、口径代码 |

**禁止**：Inter、Roboto 作主 UI 字。

---

## 自托管计划（T021）

1. 从 [LXGW Neo ZhiSong](https://github.com/lxgw/LxgwNeoZhiSong) 子集化常用汉字 + 干支 + 卷名用字
2. 输出 `LXGWNeoZhiSong-subset.woff2` 放本目录
3. 在 `variables.css` 增加：

```css
@font-face {
  font-family: "LXGW Neo ZhiSong";
  src: url("/fonts/LXGWNeoZhiSong-subset.woff2") format("woff2");
  font-display: swap;
  font-weight: 400 700;
}
```

4. 验收：Network 见 woff2；卷名与盘面用 display 栈渲染

---

## S0.5 签字门禁

字体子集 **上线并实测对比度** 后，方可在 EXECUTION-PRIORITY 将 T021 标 ☑。打磨期可暂用系统 fallback。
