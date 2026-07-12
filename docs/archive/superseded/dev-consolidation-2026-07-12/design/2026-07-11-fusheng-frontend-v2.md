# 浮生前端方案 v2.4

日期：2026-07-11  
状态：已落地（c2 仓库）— 稳 9.5+ 冲刺项

## v2.5 变更摘要（P2 续）

| 项 | 实现 |
|----|------|
| 姓名↔用神 | `utils/nameBaziCrossRef.ts` + 报告姓名章对照区 |
| PDF 分章 | `useReportPdfExport` 按 `.report-chapter` 分页 + 动态 import |
| 死代码清理 | 删除 `NewZiweiView.vue`（23KB，已无路由引用） |
| E2E 安装 | `scripts/install-playwright.ps1` + CI `playwright install` |
| **服务端 PDF** | `POST /api/v1/fusheng/report/pdf` + Playwright HTML 渲染；前端优先服务端，失败回退客户端 |

## v2.4 变更摘要

## v2.4 变更摘要

| 项 | 实现 |
|----|------|
| 姓名分析 | `api/name.ts` + `givenName` 档案字段 + 报告姓名章（五格/三才） |
| 城市选择 | `CityPicker` 接入档案出生地/现居地 |
| PDF 导出 | `html2canvas` + `jspdf` 客户端下载（保留打印） |
| 批注持久化 | `stores/reportNotes.ts` 按档案 localStorage |
| 流程遥测 | `utils/flowAnalytics.ts` 轻量事件记录 |
| E2E | Playwright `e2e/fusheng-flow.spec.ts` 主路径 + 守卫 |
| 测试 | 24 项 vitest + 2 项 e2e |

## 1. 目标

将 c2 前端收敛为**单一品牌、单一主路径、三层语法**的命理档案产品：

```
首页 → 档案 → 八字/紫微 → 报告 → PDF
```

品牌：**浮生** · 浮生若寄，知命知心

## 2. 信息架构

| 页面 | 路由 | 职责 |
|------|------|------|
| 首页 | `/` | 预览档案 + 主路径入口 |
| 档案 | `/profile` | 唯一资料编辑中心 |
| 八字 | `/new/bazi` | 结构验证 + 分层分析 |
| 紫微 | `/new/ziwei` | 传统方盘 + 格局宫位 |
| 报告 | `/report` | 正式交付件 + 打印 PDF |

## 3. 三层内容语法（全局）

1. **摘要层** — `SummaryStrip`：3~5 项关键指标，始终可见  
2. **结构层** — 表格 / 方盘 / 时间轴，默认展开  
3. **解释层** — `AnalysisPanel`：默认折叠，点击展开  

## 4. 视觉系统

### Token（`variables.css`）

- `--brand-ink` 深墨
- `--brand-paper` 暖米白
- `--brand-gold` / `--brand-gold-dark` 铜金主色
- `--brand-cinnabar` 印章朱红（仅预警/缺失）

### 共享样式

- `assets/fusheng-page.css` — 页面头、卡片、按钮
- `assets/report-print.css` — 报告打印增强
- `components/fusheng/` — `SummaryStrip`、`AnalysisPanel`、`FlowProgress`、`PageHead`、`ProfileReadinessCard`

### 共享逻辑

- `utils/fushengFlow.ts` — 主路径步骤定义
- `composables/useFushengFlow.ts` — 完整度、导航守卫
- `stores/fushengReport.ts` — 八字/紫微会话缓存，避免重复请求
- `utils/profileReadiness.ts` — 阻断项 vs 增强项、空档案判定
- `utils/buildChartRequests.ts` — 时辰精度/历法口径统一入 API
- `utils/crossValidation.ts` — 八字紫微互证

## 5. 模块设计

### 5.1 档案页

- 左：基础信息 / 时间地点 / 现居地 / 关注重点
- 右：完整度进度条、时间可信度、缺失字段清单
- 顶：`FlowProgress` 主路径步骤条
- 数据源：`utils/profileMetrics.ts`

### 5.0 全局壳层（v2.2）

- 桌面：顶栏胶囊导航，未填出生时间时锁定八字/紫微/报告
- 移动：底部固定五步导航 + 安全区适配
- 全站：`FlowProgress` 步骤条（首页/档案/八字/报告页可见）

### 5.2 八字页

- 摘要条 → 六柱表 → 分析面板（6 模块可展开）
- 与品牌色统一，移除旧蓝白科技风

### 5.3 紫微页（档案驱动）

- 路由 `/new/ziwei` → `FushengZiweiView.vue`（替代 800 行 `NewZiweiView`）
- **无独立出生表单**，仅读档案 + `fushengReport` 缓存
- 方盘组件 `FushengZiweiPlate`（四化/庙旺/完整辅星）
- 展示口径横幅（精度/历法/夏令时）

### 5.4 报告页

- 左：章节目录（封面 / 档案 / 八字 / 紫微 / 综合）
- 中：正文（摘要 → 结构 → 解释）
- 操作：重新生成、打印导出 PDF
- 并行请求八字 + 紫微 API 聚合

## 6. 技术边界

### 保留

- Vue 3 + Vite + Pinia
- `紫薇` 项目移植的紫微方盘组件（51 组件 + 37 composables）
- c2 自有八字 API

### 暂未接入（已隐藏 UI）

- 案例保存 / 快照 / 相似命盘
- AI 解读面板
- 择日跳转
- 紫微预测 Tab

占位 API 存在于 `api/admin.ts` 等，不暴露给用户。

## 7. 验收标准

- [x] 五页导航闭环：首页 / 档案 / 八字 / 紫微 / 报告
- [x] 品牌 Logo + 铜金配色全站一致
- [x] 档案完整度 + 时间可信度可见
- [x] 八字/紫微遵循摘要→结构→解释
- [x] 紫微 compact 模式无占位功能报错
- [x] 报告页可打印导出（全章节打印 + 八字表 + 紫微方盘）
- [x] 移动端方盘可横向阅读
- [x] 报告数据加载 composable（`useFushengReport`）
- [x] 八字列构建工具（`buildBaziColumns`）
- [x] 紫微页重型组件懒加载
- [x] 单元测试：`profileMetrics`、`buildBaziColumns`
- [x] 姓名分析对接 `POST /api/v1/name/analyze`
- [x] 档案页 `CityPicker` 城市选择器
- [x] 客户端 PDF 下载（`useReportPdfExport`）
- [x] 在线批注按档案 localStorage 持久化
- [x] 服务端 PDF 导出（`POST /api/v1/fusheng/report/pdf`，客户端回退）
- [x] 主路径步骤条 `FlowProgress` 全站可见
- [x] 移动端底部五步导航
- [x] 八字/报告数据会话缓存（`fushengReport` store）
- [x] 共享页头 `PageHead`、档案就绪卡 `ProfileReadinessCard`
- [x] 单元测试：`fushengFlow`、`profileReadiness`、`buildChartRequests`、`crossValidation`、路由守卫
- [x] 空档案默认（禁止 demo 假数据排盘）
- [x] 路由守卫 `requiresArchive`
- [x] 紫微档案单真相源 + 轻量视图
- [x] 报告 10 章（口径/互证/大运/十二宫/批注区）
- [x] 导航收敛为壳层一处（移除页内 FlowProgress）

## 8. 后续迭代（P2）

1. ~~姓名章与八字用神对照说明~~ ✅ v2.5
2. ~~删除遗留 `NewZiweiView.vue` 死代码~~ ✅ v2.5
3. ~~报告 PDF 分章分页优化~~ ✅ v2.5（按章截图）
4. ~~服务端 PDF（Playwright 后端导出，减小前端包体）~~ ✅ v2.5
5. CI E2E 在 Ubuntu 跑通后纳入质量门禁
