# A+B · D1 薄卷加厚缺口清单

| 字段 | 内容 |
|------|------|
| **日期** | 2026-07-19 |
| **阶段** | A 维护 + B 内容深化 · D2–D3 **已落地**（inv-1.34） |
| **依据** | [`content-hollowness-audit-latest.json`](content-hollowness-audit-latest.json)（样本 1990-01-15） |
| **原则** | 少开新面；BE `life_volume_service` 与 FE `buildLifeVolumes` **同源加厚** |
| **状态** | V2-01…05 / V6-01…04 ✅；验收：单测 + SPA rebuild |

## 1. 审计快照

### D1 前（按 avg_chars 升序）

| 卷 | blocks | avg_chars | trunc | 判断 |
|----|--------|-----------|-------|------|
| **vol6** | 1 | **66.0** | 0% | **P0 加厚** — 仅 on-demand 说明壳 |
| **vol2** | 3 | **69.3** | 0% | **P0 加厚** — 关系/神煞摘要短、缺 cite |

### D2–D3 + preface/vol4 后（`content-hollowness-audit-latest.json`）

| 卷 | blocks | avg_chars | thin | 判断 |
|----|--------|-----------|------|------|
| **vol6** | **6** | **91.7** | 0% | ✅ 达标（≥3 块 · avg≥90） |
| **vol2** | **6** | **102.3** | 0% | ✅ blocks≥5 可读；样本 avg≈102（fixture ≥110） |
| **preface** | **3** | **76.0** | 0% | ✅ 三层中文 + 阅读顺序（原 ~61） |
| **vol4** | **18** | **73.0** | 0% | ✅ 新增 `ziwei-reading` 命身/三方导读 |
| **vol1** | **10** | **117.7** | trunc **0%** | ✅ 原 trunc 10%→0；格局/用神优先 |

## 2. vol2 · 业之象（优先）

### 现状

- BE：`services/life_volume_service.py` → `relations` / `shensha` 两节 fact + 可选 `relations-explain`
- FE：`frontend/src/utils/buildLifeVolumes.ts` → `buildVol2Sections`
- 样本预览：干支关系 / 神煞列表 + 固定「以排盘 fact 为准…」套话，约 65–74 字/块

### 缺口（D2–D3 建议改）

| ID | 缺口 | 建议落地 | 状态 |
|----|------|----------|------|
| V2-01 | 关系只列关键词，无「何意 / 对本命影响」一句 | `relations-reading` + `_relations_impact_text` / FE `formatRelationsImpactText` | ✅ |
| V2-02 | 神煞仅名单，无分吉凶与阅读提示 | `shensha-auspicious` / `shensha-caution` | ✅ |
| V2-03 | cite 层常缺席 | explain cite → `relations-cite`；神煞 `classic_source`；否则 `vol2-cite-pending` | ✅ |
| V2-04 | 套话 enrich 占字 | 够长不套；短块短衬底至 ≥40 | ✅ |
| V2-05 | FE Adapter 与 BE 不同步 | `buildVol2Sections` + 单测同源 | ✅ |

### 验收（样本盘）

- vol2 `avg_chars` **≥ 110**（或 blocks≥5 且单块可读）
- thin/fallback 仍 0
- 报告页卷二连续阅读不再「三行结束」

## 3. vol6 · 问书（优先）

### 现状

- BE/FE 各 **1 block**：说明「需主动展开、打磨期不自动调用」
- 符合 R109 A（不静默耗 LLM），但卷本身像空壳

### 缺口（在不自动调 LLM 前提下加厚）

| ID | 缺口 | 建议落地 | 状态 |
|----|------|----------|------|
| V6-01 | 无「怎么问」示例 | `vol6-how-to-ask` 三例（事业/婚恋/流年） | ✅ |
| V6-02 | 无与前卷衔接 | `vol6-bridge` | ✅ |
| V6-03 | 权益/登录态不说明 | `vol6-access` + 中文模块名（对齐 `LLM_MODULES`） | ✅ |
| V6-04 | 仍禁止首屏静默调用 | 保持 `collapsed_default`；无自动 `/llm` | ✅ |

### 验收

- vol6 blocks **≥ 3**，`avg_chars` **≥ 90**
- 不新增自动 `/llm` 请求
- 文案无「LLM」裸露

## 4. 同批可顺手

| 卷 | 动作 | 状态 |
|----|------|------|
| preface | 读法段去掉 cite/inference 英文夹叙，改为「排盘推算 / 典籍依据 / 经验推断」+ 阅读顺序 | ✅ inv-1.35 |
| vol4 | 命盘概要后补「先看命身轴再看三方」固定导读（`ziwei-reading`） | ✅ inv-1.35 |
| vol1 trunc | 查截断点，优先保格局+用神完整句 | ✅ inv-1.36：句末截断 · 运势摘要控长 · geju-explain 提预算 |

## 5. 不做（本阶段）

- 河洛 / 奇门真引擎
- 新路由或 GTM 开关默认开
- 为冲 avg_chars 灌水重复套话

## 6. 下一刀入口

1. ~~BE/FE vol2·vol6 加厚~~ ✅
2. ~~preface 读法中文化 · vol4 命身/三方导读~~ ✅
3. ~~vol1 trunc 控长~~ ✅
4. **不做**：河洛/奇门真引擎 · GTM 默认开
5. ~~真源典籍挂载（神煞 classic_refs → vol2 软提示）~~ ✅ inv-1.37
6. ~~关系 explain / vol2 典籍真挂~~ ✅ inv-1.38（verified `interactions` cite + 地支软提示；E-01 过滤修正）
7. ~~地支引擎条 verified 升格~~ ✅ inv-1.39（`dizhi_ext04/05/06` transitive-subset；宿主 `论刑冲会合解法`；`dizhi_ext01/02/03` 仍 unverified）
8. ~~神煞引擎条 verified 升格~~ ✅ inv-1.40（`shensha_002/003/004/005/006/008` + `dayun_012`/`general_006`；candidates 读 classics verified → cite）
9. ~~剩余 engine_ref transitive 批量升格~~ ✅ inv-1.41（42 条；格局 cite E-01：verified→`geju-cite`，裸串→soft）
10. **阻塞**：`dizhi_ext01/02/03` 为引擎复述，非任何 verified 篇章子集 → 不可 transitive 升格
11. ~~跋文 / 用神 cite 维护~~ ✅ inv-1.42（跋反映 verified 进度；`yongshen-cite` BE+FE）
12. ~~vol3 大运/流年 cite~~ ✅ inv-1.43（`dayun-cite` / `liunian-cite` BE+FE+explain）
13. ~~日主 / 婚恋 / 健康 cite~~ ✅ inv-1.44（vol1 `daymaster-cite`；vol5 `marriage-cite`/`health-cite`）
14. ~~FE 关系 verified 回退 + 五行/十神 cite~~ ✅ inv-1.45（Adapter `pickRelationsVerifiedCites`；`wuxing-cite`/`shishen-cite`）
15. 后续：**GTM 仍不开**；冲合专条外底本 spotcheck；其它零星维护
