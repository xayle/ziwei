# 穷通 ↔ 引擎调候对齐 / drift（QT-04 · 2026-07-16）

| 字段 | 内容 |
|------|------|
| **计划包** | QT-04 |
| **状态** | 初版 · 冲突登记 |

## 1. 源对照

| 源 | 路径 | 可进 cite？ |
|----|------|-------------|
| 引擎复述摘录 | `services/bazi_engine/classic_refs.py`（source 含穷通） | **否**，除非 classics 升格 verified |
| 引擎调候表 | `services/bazi_engine/tables.py` · `MONTH_CLIMATE_RULES` | **否**（算法 paraphrases） |
| 语料库 | `data/classics.json` 标题含「穷通宝鉴」 | 仅 `verification_status=verified` |

## 2. 当前经典摘录（引擎侧）

| classic_refs id | 性质判断 | classics id | 处置 |
|-----------------|----------|-------------|------|
| `wuxing_007` | 旺令通说，非穷通专章原文 | `engine_ref.wuxing_007` | 保持 unverified |
| `dayun_011` | 大运通则式复述 | `engine_ref.dayun_011` | 保持 unverified |
| `geju_e07` | 格局/用神/大运口诀式 | `engine_ref.geju_e07` | **曾误标 verified → 本轮降为 unverified** |
| `general_ext07` | 调候总纲式复述（最接近应收） | `engine_ref.general_ext07` | 待底本 spotcheck 后再升 |

## 3. Drift 原则

1. 引擎表决定 **算法行为**；典籍条决定 **讲解 cite**；冲突时双字段保留并记本表。  
2. 禁止把 `MONTH_CLIMATE_RULES` 文案批量写入 classics 并标 verified。  
3. C-调候矩阵「穷通格」以 **经 spotcheck 的调候条** 为准，不以引擎表行数代替。

## 4. 下一步（人工）

1. 选定底本版本（注明版本页码/章节）。  
2. 按 `qiongtong-intake-checklist-2026-07-16.md` QT-01→02 摘录。  
3. 每条升格前在 `docs/reports/spotcheck-ctext.md` 登一条。  
