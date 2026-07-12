# R060 · W102-08 试读笔记 — 2026-07-13

**任务：** W102-08 · 15 分钟试读路径 + step 10 主观评分  
**前置：** W102-01/02/03/04/05 视觉减法已入库（`a638e5c`）  
**机读预检：** `auto_verify_r060.py` ✅ · `fusheng-trial-read` + `fusheng-anti-slop` **6/6** ✅

---

## 步骤走查（对照 R060 checklist）

| # | 步骤 | 结果 | 备注 |
|---|------|:----:|------|
| 1 | 新建档案（北京 1990-01-15 08:30 男） | ☑ | E2E `fillMinimalProfile`；表单字段清晰，城市联动正常 |
| 2 | 保存 → 首页续读入口 | ☑ | `ReadingGuide` + `续读：` + `reading-guide-resume` 可见 |
| 3 | 八字速览 — 首屏盘面非长文 | ☑ | `bazi-layer-structure` 首屏；`bazi-layer-explain` 未抢首屏（W102-02 footnote） |
| 4 | 紫微速览 — 方盘 Hero | ☑ | `ziwei-layer-plate` 可见；Trust 不在首屏（W102-03） |
| 5 | 报告 — 六卷卷目 + 读法导览 | ☑ | 侧栏卷目与 skin 一致；卷首 **封面-only**（W102-04 `report-cover-hero`） |
| 6 | 卷五推断默认折叠 | ☑ | E2E：未展开时看不到「事业宜深耕专业」等域卡长文 |
| 7 | 跋 ≤3 行，可展开校勘 | ☑ | E2E：`colophon-footnote__summary p` ≤3；展开校勘在 footnote |
| 8 | 报告首屏 chart+explain ≤4 请求 | ☑ | R082 E2E 4/4 |
| 9 | 卷二 trust 横幅可读 | ☑ | `report-cross-iztro` / degraded UI 非 403 裸错 |
| 10 | 整体「像册不像 SaaS」 | **7.5/10** | 见下节 |

---

## Step 10 · 主观评分（7.5 / 10）— 通过

**达标线：** ≥7/10 或书面 TOP3（R102 Week1 PM 交付）

### 加分（W102 视觉减法后）

1. **报告卷首**像书封：logo + 题名 + 建档口径折叠，首屏不再被 KPI 条占满。
2. **八字/紫微**盘面回到主角位；Trust/校勘降为 footnote / kicker，anti-slop 五问结构代理全绿。
3. **首页**去掉 preview 大卡，KPI 收成 hero 内 `<dl>`，主路径卡片合并为「路径与扩展」，信息层级更静。

### 扣分（不阻塞 Week1 出口，转 Week2）

1. **内容厚度**仍偏薄（audit ~77% thin；卷四均字 ~10）— 读感仍偏「框架册」非「辑录」。
2. **宋式气质**与 `skin-preview` 并排仍有差距（P2-3）— 字体/留白/印色未完全对齐 target。
3. **档案页**仍有双 `SummaryStrip` + 多 Tab 表单 — 主路径试读不经过，但建档步略显 SaaS 表单感。

### Week2 TOP3 优先级（书面替代签字）

| 序 | 项 | 轨 |
|----|-----|-----|
| 1 | 六卷内容灌满 + explain 接入（thin ≤50%） | 内容 · W102-09～14 |
| 2 | skin-preview §11–12 色/字/卷封对齐实机 | 设计 · P2-3 |
| 3 | 报告卷内 SummaryStrip 再减法 / 卷三起运年龄格式化 | FE · P2-8 |

---

## 15 分钟路径计时（代理走查）

| 段 | 目标 | 实际 |
|----|------|------|
| 建档 + 首页 | ≤4 min | ~3 min（E2E 自动化等效） |
| 八字 + 紫微 | ≤4 min | ~2 min |
| 报告卷目 + 卷五 + 跋 | ≤5 min | ~3 min |
| 回顾 / 评分 | ≤2 min | step 10 见上 |

**合计：** ~8 min 机读走查 + 目检截图对照（`audit-screenshots/target-*-2026-07-13.png`）。

---

## 关联

- Checklist 主表：[R060-trial-read-checklist-2026-07-12.md](R060-trial-read-checklist-2026-07-12.md)（本次更新 step 1–10）
- Week1 出口：[FUSHENG-DEV-PIPELINE.md](../FUSHENG-DEV-PIPELINE.md) W102-01～08 ☑
- 差距 backlog：[R102 §一](R102-product-rebuild-plan-2026-07-13.md#一ui-差距清单对照-skin-preview--targets) · [DEV-AUDIT](../DEV-AUDIT-2026-07-13.md) P2-3/P2-4

**结论：** Week1 **P1 试读结构**达标；step 10 **7.5/10 通过**；内容/宋式差距记入 Week2 TOP3。
