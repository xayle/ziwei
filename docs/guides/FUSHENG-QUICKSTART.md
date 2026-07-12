# 浮生 · 30 分钟快速上手

| 字段 | 内容 |
|------|------|
| **版本** | quickstart-1.1 |
| **日期** | 2026-07-13 |
| **实操手册** | [**FUSHENG-DEV-HANDBOOK.md**](../FUSHENG-DEV-HANDBOOK.md) ⭐ 30 秒开工 + 全部命令 |
| **主入口** | [**DEVELOPMENT.md**](../DEVELOPMENT.md) |
| **主文档** | [FUSHENG-INTEGRATED-DEV-PLAN](../plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md) |
| **顺序开发** | [**EXECUTION-PRIORITY**](../plan/FUSHENG-EXECUTION-PRIORITY.md)（T001–T070，免对话） |
| **前端开发** | [**FUSHENG-FRONTEND-DEV**](./FUSHENG-FRONTEND-DEV.md)（含预警 · FE-BE · 组件） |

---

## 我该读哪份文档？

| 角色 | 文档 |
|------|------|
| 全栈 / PM | [**EXECUTION-PRIORITY**](../plan/FUSHENG-EXECUTION-PRIORITY.md)（按 T001 依次做）· [INTEGRATED-DEV-PLAN](../plan/FUSHENG-INTEGRATED-DEV-PLAN-2026-07-12.md) |
| 只改后端 | 集成文档 §四 + [BACKEND-MASTER](../plan/BACKEND-MASTER-PLAN-2026-07-12.md) |
| 只改前端 | [**FRONTEND-DEV**](./FUSHENG-FRONTEND-DEV.md) + 集成文档 §五 |
| 改 UI | [DESIGN-MASTERPLAN](../design/FUSHENG-DESIGN-MASTERPLAN.md) + skin-preview + FRONTEND-DEV §9 |
| **开工前** | [**节点清单 + 插件**](./FUSHENG-NODE-CHECKLIST.md) |
| 前后端接口 | [FE-BE-DECISIONS](../plan/FE-BE-DECISIONS.md) + `docs/contracts/*.json` |

---

## 10 分钟：跑起来

```powershell
# 后端（项目根）
python -m uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

访问：`http://localhost:5173`（或 vite 提示端口）

---

## 10 分钟：改哪里

| 要改什么 | 文件 |
|----------|------|
| 八字盘面 | `frontend/src/views/new/NewBaziView.vue` |
| 报告六卷 | `frontend/src/views/ReportView.vue` → F4 拆子组件 |
| 六卷数据 | **新建** `frontend/src/utils/buildLifeVolumes.ts` |
| 八字 API | `routers/bazi.py` · `services/bazi_full_service.py` |
| Explain（计划） | **新建** `routers/explain.py` · `services/explain_service.py` |
| 样式 Token | `frontend/src/assets/variables.css` |

---

## 10 分钟：当前周计划（默认 W1）

| 后端 | 前端 |
|------|------|
| P0-07 ChartSnapshot | F0 QUICKSTART + 契约 types |
| P0-08 disclaimer | F1 skin-preview 六卷 |
| P0-02 OpenAPI CI | F2 删 PageHead |

---

## 契约（必知）

- 六卷 JSON 形状：`docs/contracts/life-volume.schema.json`
- explain 映射：`docs/contracts/explain-section-map.json`
- UI 三层标签：**排盘推算 / 典籍依据 / 经验推断**（见集成文档 §3.1）

---

## 验收命令

```powershell
make scorecard
cd frontend && npm run type-check && npm run test
```
