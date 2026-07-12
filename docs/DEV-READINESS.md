# 浮生 · 开发就绪状态（实机同步版）

| 字段 | 内容 |
|------|------|
| **版本** | readiness-1.3 |
| **日期** | 2026-07-13 |
| **实操手册** | [**FUSHENG-DEV-HANDBOOK**](FUSHENG-DEV-HANDBOOK.md) ⭐ 开工/插件/命令 |
| **主清单** | [FUSHENG-EXECUTION-REMAINING](plan/FUSHENG-EXECUTION-REMAINING.md) ⭐ 当前执行 |
| **用途** | 文档与实机差距快照；**非** W14 收官签字 |

---

## 一、结论（30 秒）

| 维度 | 状态 | 说明 |
|------|------|------|
| **文档体系** | ✅ | REMAINING + INTEGRATED + 契约已齐 |
| **设计真源（skin）** | ✅ M1 | targets 三截图已冻 |
| **后端引擎** | ✅ | scorecard **24/24**；explain/disclaimer/trust 已接线 |
| **前端三页+报告** | 🟡 | 八字/紫微/报告六卷主路径已落地；R060/R071/R101–R110 待人工 |
| **质量门** | ✅ | W14 auto PASS；`quality_gate --section frontend` 绿；lint **0 warning** |

**当前阶段**：块 F 接近完成，块 G 进行中，块 H 需产品/设计人工勾选。

---

## 二、实机已落地（勿返工）

- **六卷+跋** Report：`life-volume@1.0`，无旧「11 章」导航
- **explain/batch** → vol1/vol2/vol5；`VolumeSection` cite 仅 verified
- **ZW18 degraded**：`TrustDegradedBanner` + iztro 双轨表
- **八字/紫微三档深度**：overview / structure / deep
- **卷五推断默认折叠**；卷六 LLM 需主动展开
- **E2E**：**47/47**（含快照恢复）；`fusheng-report` 10/10

---

## 三、仍待人工 / 签字

| ID | 内容 |
|----|------|
| R060 | P1 Gate：15 分钟建档→报告试读 |
| R071 / R079 | 紫微页防丑五问 + 三页截图签字 |
| R082 | 报告 Network ≤4 截图留档 |
| R101–R110 | W14 产品 11 项 + 预警 7 项 |

---

## 四、验收命令（R084 / R106）

```powershell
python scripts/audit_scorecard.py
python scripts/quality_gate.py --section backend
python -m pytest -q tests/test_explain_batch.py tests/test_explain_section_map.py tests/test_zw18_trust.py

cd frontend
npm run type-check
npm run test
npm run build
npm run test:e2e -- fusheng-flow fusheng-bazi-ziwei fusheng-report fusheng-responsive

rg "linear-gradient|PageHead|#334155|-ok-bg|四维分析" src
```

---

## 五、修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| readiness-1.2 | 2026-07-12 | 同步 R061–R074、explain、E2E、scorecard 实机状态 |
| readiness-1.1 | 2026-07-12 | 开工前文档准备版 |
