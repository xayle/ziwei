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

## 自托管状态（T021 ✅）

1. ~~从 LXGW Neo ZhiSong 子集化~~ → **已完成**：`LXGWNeoZhiSong-subset.woff2`（约 4.3MB）
2. **路径**：本目录 + `static/app/fonts/`（**均已 git 跟踪**；pre-commit 对 woff2 豁免体积检查）
3. `@font-face` 见 `frontend/src/assets/variables.css`
4. 验收：autopilot **A33** · Network 见 woff2

---

## S0.5 签字门禁

字体子集 **上线并实测对比度** 后，方可在 EXECUTION-PRIORITY 将 T021 标 ☑。打磨期可暂用系统 fallback。
