# 五书无人值守 Autopilot · 设计规格

| 字段 | 内容 |
|------|------|
| **日期** | 2026-07-16 |
| **状态** | 已批准 · 执行中 |
| **计划书** | [FUSHENG-FIVE-CLASSICS-VERIFIABLE-PLAN-2026-07-16.md](../../plan/FUSHENG-FIVE-CLASSICS-VERIFIABLE-PLAN-2026-07-16.md) |
| **方案** | A · 矩阵空洞优先 → 再冲数字 |
| **verified 规则** | 规范化后，passage 必须是公开底本全文的**连续子串** |

## 1. 目标

在无人值守条件下，循环推进至：

1. 类目矩阵无空白（尤其 C-调候·穷通、C-日主·三命）  
2. §4 数字门禁：穷通≥40 · 三命≥30 · 渊海≥20 · 子平≥45 · 滴天≥80 · 合计≥215  

禁止：模型复述冒充 verified；无底本子串匹配时不得升格。

## 2. 内容优先级（固定顺序）

| 序 | 目标 | 出口 |
|----|------|------|
| P1 | C-调候 · 穷通格 = Y | ≥1 条 verified 穷通调候 |
| P2 | C-日主 · 三命格 = Y | ≥1 条 verified 三命日主 |
| P3 | 穷通 verified ≥40 | M1 |
| P4 | 三命 ≥30 | 部分 M2 |
| P5 | 渊海 ≥20 | M2 |
| P6 | 子平 ≥45 | 部分 M3 |
| P7 | 滴天 ≥80 | M3 |
| P8 | 合计 ≥215 + 矩阵全绿 | M3 全开闸 |

## 3. 流水线（单轮）

```text
fetch_bases()           # 维基文库/既有 imported/daizhige/ctext 缓存
  → upgrade_existing()  # classics 已有条 vs 底本子串 → 自动 verified
  → chunk_fill_gaps()   # 按优先级从底本切可引用段 → 入库
  → substring_verify()  # 新条立即子串校验升格
  → append_spotcheck()  # 机读台账 docs/reports/spotcheck-ctext.md
  → report_coverage()   # E-03
  → 若门禁未绿且本轮有进展 → 重复；无进展 → 退出并写 blocker
```

## 4. 底本源（按书）

| 书 | 主源 | 备注 |
|----|------|------|
| 穷通宝鉴 | zh.wikisource 《穷通宝鉴》 | CC0/公有领域；API parse |
| 子平真诠 | ctext（若有 key）/ daizhige 评注 | 已有 import |
| 滴天髓 | daizhige 阐微 | 已有 import |
| 三命通会 | 维基/本地缓存（若可拉） | 缺源记 blocker |
| 渊海子平 | bazi-skills yuanhai.json + 章节合集 | 已有；升格靠子串或同源 |

## 5. 切条规则

- 长度：80～800 字（过短合并、过长按句号切）  
- tags：由篇名/季节/天干关键词映射到 C-*  
- id：`auto.{book}.{slug}.{n}` 稳定哈希，可重复跑幂等  
- title：`《书名》·节标题`  

## 6. 规范化与子串

`normalize(s)`：去空白、全角标点→半角、繁简可选统一（本轮用「去空白 + NFKC」）。  
`verified` ⇔ `normalize(passage)` in `normalize(base_fulltext)`。

## 7. 退出码

| code | 含义 |
|------|------|
| 0 | M3 全绿 |
| 1 | 未达标但写了报告（正常未完成） |
| 2 | 无底本进展（blocker） |

## 8. CLI

```bash
python scripts/five_classics_autopilot.py
python scripts/five_classics_autopilot.py --max-rounds 5
python scripts/five_classics_autopilot.py --books 穷通宝鉴
```

## 9. 非目标

- 不改 cite 白名单（E-04）  
- 不恢复 GTM T100（待 M2）  
- 不删非五书语料  
