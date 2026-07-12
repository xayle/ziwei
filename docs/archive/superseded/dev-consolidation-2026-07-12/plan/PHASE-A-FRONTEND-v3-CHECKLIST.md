# Phase A 前端 v3 — 实施清单

| 字段 | 内容 |
|------|------|
| **周期** | 2 周（2026-07-12 起） |
| **设计** | [v3 信任深度方案](../design/2026-07-12-fusheng-frontend-v3-trust-depth.md) |
| **线框** | [mockups/](../design/mockups/) |

---

## 进度总览

| 状态 | 数量 |
|------|------|
| ✅ 已完成 | 14 |
| 🔄 本批落地 | 6 |
| ⏳ Phase B | 5 |

---

## A. 信任层与八字（B-06 / B-09 / B-10）

| ID | 任务 | 状态 | 验收 |
|----|------|------|------|
| A1-01 | `BaziStructuralRelations` 刑冲/空亡/神煞 | ✅ | 无数据显式「缺失」 |
| A1-02 | `BaziLiuriTodayCard` 流日卡片 | ✅ | 八字页 + 报告章 |
| A1-03 | `EngineTrustPanel` + `useEngineTrustDisplay` | ✅ | missing/provenance/双轨 |
| A1-04 | `AnalysisPanel` heuristic 默认折叠 | ✅ | + `PatternTierBadge` |
| A1-05 | 八字页四层区块顺序 | ✅ | NewBaziView |

---

## B. 紫微（Z-07 / Z-10）

| ID | 任务 | 状态 | 验收 |
|----|------|------|------|
| A2-01 | `buildPatternAnalysisBlocks` + tier | ✅ | classical vs heuristic |
| A2-02 | `PalaceAnalysisGrid` 十二宫 structured | ✅ 本批 | 紫微页 + 可复用 |
| A2-03 | `PatternTierBadge` | ✅ 本批 | AnalysisPanel 标题 |
| A2-04 | 紫微页 Trust + 飞星 + Algo | ✅ | FushengZiweiView |

---

## C. 档案 Profile（P 9.0→9.5）

| ID | 任务 | 状态 | 验收 |
|----|------|------|------|
| A3-01 | `ProfileTabNav` 组件 | ✅ 本批 | 四 Tab |
| A3-02 | Tab：基础 / 八字口径 / 紫微口径 / 云端 | ✅ 本批 | zi_day_rule 迁到八字 Tab |
| A3-03 | `AlgoPresetBar` 右弼 preset | ✅ 本批 | hour/month + invalidate |
| A3-04 | 云端 Case + 快照迁入云端 Tab | ✅ 本批 | 侧栏仅保留摘要 |
| A3-05 | 口径变更 invalidate 缓存 | ✅ | fushengReport |

---

## D. 报告 Report（X-03）

| ID | 任务 | 状态 | 验收 |
|----|------|------|------|
| A4-01 | `DualTrackTable` 固定清单 | ✅ 本批 | 互证章 |
| A4-02 | iztro 双轨表 + 右弼 hour 按钮 | ✅ | ReportView |
| A4-03 | 八字/紫微 Trust 嵌入各章 | ✅ | compact/full |
| A4-04 | E2E 双轨断言 | ⏳ | fusheng-report.spec |

---

## E. 工程与文档

| ID | 任务 | 状态 |
|----|------|------|
| A5-01 | Draw.io 线框 3 张 | ✅ |
| A5-02 | Cursor 扩展说明 | ✅ |
| A5-03 | vitest `phaseAComponents.spec.ts` | ✅ 本批 |
| A5-04 | `npm run type-check && npm run test` | ✅ 61 passed |

---

## Phase B 预告（下一迭代）

1. `useZiweiOverlayState` — 方盘 ↔ 时间轴状态共享  
2. `FortuneStrip` — 时间轴四格运限（部分已有 `YunxianSummaryStrip`）  
3. Trust 层「简洁 | 完整」切换  
4. Report PDF Trust 块打印展开 QA  
5. Playwright：档案改 ziDayRule → 重算断言  

---

## 本批变更文件

```
frontend/src/components/fusheng/
  ProfileTabNav.vue          (新)
  AlgoPresetBar.vue          (新)
  DualTrackTable.vue         (新)
  PalaceAnalysisGrid.vue     (新)
  PatternTierBadge.vue       (新)
  AnalysisPanel.vue          (改)
  __tests__/phaseAComponents.spec.ts (新)

frontend/src/views/
  ProfileView.vue            (四 Tab + preset)
  ReportView.vue             (DualTrackTable)
  new/FushengZiweiView.vue   (PalaceAnalysisGrid)

docs/plan/PHASE-A-FRONTEND-v3-CHECKLIST.md (本文件)
```

---

## Gate（Phase A Done）

- [x] `npm run type-check && npm run test` 通过（61 tests）
- [ ] `make quality-gate-frontend` 通过  
- [ ] 档案四 Tab E2E 或手动 QA 1 遍  
- [ ] 互证章双轨表 ≥3 行可见  
- [ ] 改右弼 preset 后紫微页重算  
