# 浮生 · 人工签字包（打磨收官）

| 字段 | 内容 |
|------|------|
| **日期** | 2026-07-15 |
| **代码** | `1751b23`（docs） / `8c10640`（UI inv-1.10）已推 `main` |
| **决议** | [R109](R109-post-w14-decision-2026-07-12.md) **选项 A**：延后 GTM，先签完人工 Gate |
| **定位** | 只列「人还没勾」的签字位；机读证据已齐 |

---

## 一、最新机读（本包生成时）

| 检查 | 结果 |
|------|------|
| R103 | **7/7** `pass: true` |
| W14 bundle | **pass**（scorecard · quality_gate · r007 · r103 · r060 · pytest_w14） |
| Scorecard | **24/24 · 10.0/10** |
| 空洞审计 | thin **0%** · fallback **0%**（`build_life_volumes_from_charts`） |
| UI 清单 | [inv-1.10](UI-FEATURE-ISSUE-INVENTORY-2026-07-14.md) 产品 bug 收口 |

复跑：

```powershell
python scripts/auto_verify_r103.py
python scripts/auto_verify_w14.py
python scripts/audit_scorecard.py
python scripts/audit_content_hollowness.py
```

---

## 二、仍需人签（最短路径）

| 优先级 | ID | 文档 | 谁签 | 当前 |
|--------|-----|------|------|------|
| **1** | **R025** | [共签草案](R025-life-volume-schema-cosign-draft-2026-07-12.md) | 后端 + 前端 + 校勘 | ☐ 三格空白 |
| **2** | **R107** | [收官草案](R107-w14-signoff-draft-2026-07-12.md) | 负责人 | ☐（依赖 R025） |
| — | R060 | [试读清单](R060-trial-read-checklist-2026-07-12.md) | 产品/前端 | ☑ 已有 Week4 签字 |
| — | R079 Q5 | R079 / DS 盲测 | 设计 | 机读代理绿；盲测格若需可另开 |

**解锁链：** `R025 三签 ☑` → `R107 负责人 ☑` → 可标 T070 / 再议是否进 POST-W14。

---

## 三、R025 签字时看什么（1 页）

共签对象：`docs/contracts/life-volume.schema.json`（`life-volume@1.0`）。

| 角色 | 核对点 | 机读旁证 |
|------|--------|----------|
| 后端 | schema ↔ OpenAPI / `LifeVolumeResponseModel` / `GET /life/volumes` | `tests/test_life_volume_schema_contract.py` · `test_life_volumes_api.py` · `test_life_volume_content_thicken.py` |
| 前端 | Adapter `buildLifeVolumes` 字段同构；远程优先、失败可见 notice | `buildLifeVolumes.spec.ts` · `api/life.ts` · ReportView |
| 校勘 | cite 仅 verified 可标「典籍依据」；`classic_id` / `source_page` 展示策略认可 | 报告引用表 · classics spotcheck |

签完请在 R025 表填：**姓名 · 日期 · 决议勾 ☐→☑**。

---

## 四、R107 签字前确认

自动化块已全部 ☑（含 inv-1.10）。负责人仅需确认：

1. R025 三签已齐  
2. 接受 R109 **选项 A**（暂不进 GTM），或书面改选 B/C  
3. 在 R107 签字表落名落日  

---

## 五、不做什么

- 不再为「继续」自动开 GTM / 付费 / snippets（纪律：R109 A）  
- `scripts/data/` 本地草稿已 ignore，勿当收官阻塞  

---

**包状态：** 机读齐 · 等人签 R025 → R107。
