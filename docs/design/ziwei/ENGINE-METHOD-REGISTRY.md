# 紫微引擎方法注册表

版本：v1.3  
日期：2026-07-12  
状态：**已确认（Phase 0–4）**  
原则：**默认以 `docs/design/ziwei/` 设计文档为准**；旧实现通过 `*_method` 参数保留，便于回归对比。

---

## 决策总表

| 编号 | 争议点 | 默认方法 | 旧实现（legacy） | 参数名 | Phase |
|------|--------|----------|------------------|--------|-------|
| Z-01 | 流年命宫 | **太岁直落**（子年→子宫） | 寅宫起 `(2+branch)%12` | `liunian_life_method` | 1 |
| Z-02 | 流月 | **斗君法** | 流年命宫 + month-1 | `liuyue_method` | 1 |
| Z-03 | 右弼 | **戌起正月逆数月** | 戌起子时逆数时辰 | `youbi_method` | 1 |
| Z-04 | 文昌/文曲 | **按时辰安星** | 按年支安星 | `wenchang_method` | 1 |
| Z-05 | 小限起点 | **文档三合表**（见下） | 男寅/女申（寅午戌组） | `xiaoxian_start_method` | 2 ✅ |
| Z-06 | 流日/流时 | **流月初一顺行、流日子时顺行** | — | `flow_lunar_day` 等 | 3 ✅ |
| Z-07 | 缺失字段 | **`missing_fields` 数组** | silent pass | — | 2 ✅ |
| Z-08 | 流年四化 | **流年天干 `year_stem`**（《全书》§三） | 流年命宫宫干 `life_palace_stem`（陆斌兆） | `liunian_sihua_method` | 4 ✅ |
| Z-09 | 年干支界 | **立春换年**（sxtwl 节气年） | 正月初一换年（农历 `getLunarYear`） | `year_divide` | 5 ✅ |
| Z-10 | 晚子时换日 | **公历进次日**（`solar_next`） | 农历日+1 安星（`forward`，对齐 iztro）/ 不换日（`current`） | `day_divide` | 5 ✅ |

**默认值（API 未传参时）**：全部使用「默认方法」列，即设计文档口径。

---

## Z-01 流年命宫

### 默认：`taisui`（太岁直落）

依据：`docs/design/ziwei/01-大限流年.md` §三

```
流年命宫地支索引 = 流年地支索引
子年 → 0（子宫），丑年 → 1，…，亥年 → 11
```

### Legacy：`yin_start`

```
流年命宫 = (2 + branch_idx) % 12
```

当前代码位置：`services/ziwei_engine/liunian.py`

---

## Z-02 流月

### 默认：`doujun`（斗君法）

依据：`01-大限流年.md` §四

1. 找到流年地支所在宫位 `start`
2. 从 `start` 起正月，**逆数**至生月：`step2 = (start - (birth_month - 1)) % 12`
3. 从 `step2` 起子时，**顺数**至生时：`doujun = (step2 + birth_hour) % 12`
4. 正月 = 斗君所在宫；各月顺数：`doujun + month - 1`

### Legacy：`simplified`

```
流月命宫 = (liunian_life_branch + month - 1) % 12
```

未实现斗君时，响应须含：

```json
"missing": ["doujun_liuyue"],
"liuyue_method": "simplified"
```

---

## Z-03 右弼

### 默认：`month`（月系）

依据：`05-安星诀-辅煞星.md` §一

```
右弼 = (10 - month + 12) % 12   # 戌(10)起正月逆数
```

### Legacy：`hour`

```
右弼 = (10 - hour_branch) % 12
```

左辅不变：`(3 + month) % 12`（辰起正月顺数）。

---

## Z-04 文昌 / 文曲

### 默认：`hour`（时系）

依据：`05-安星诀-辅煞星.md` §二

```
文昌 = (10 - hour + 12) % 12   # 戌起子时逆数
文曲 = (4 + hour) % 12         # 辰起子时顺数
```

### Legacy：`year_branch`

```
文昌 = (9 - year_branch) % 12
文曲 = (4 + year_branch) % 12
```

---

## Z-05 小限起点

### 默认：`standard`（设计文档表）

依据：`01-大限流年.md` §二 + 伪代码

| 出生年支组 | 起始宫位（地支索引） |
|-----------|---------------------|
| 寅、午、戌 | 辰 **4** |
| 申、子、辰 | 戌 **10** |
| 亥、卯、未 | 丑 **1** |
| 巳、酉、丑 | 未 **7** |

行运：男顺女逆（与现实现一致）。

### Legacy：`gender_split`

寅午戌组：男起寅(2) / 女起申(8)（旧 `__init__.py` 实现）。

**Phase 2 状态**：✅ 默认 `standard`

---

## Z-06 流日 / 流时

### 默认：`standard`（设计文档 §五）

```
流日命宫 = (流月命宫 + lunar_day - 1) % 12
流时命宫 = (流日命宫 + hour_branch_idx) % 12
```

引擎入口：`ziwei_full(..., flow_lunar_day=, flow_liuyue_month=, flow_hour_branch=)`  
响应：`ZiweiChart.liuri_liushi` → API `liuri_liushi`

**Phase 3 状态**：✅ 引擎 + HTTP（`ZiweiRequest.flow_*`）均已暴露

---

## Z-08 流年四化

### 默认：`year_stem`（流年天干）

依据：`docs/design/ziwei/01-大限流年.md` §三 — 「流年四化由当年天干决定」

### Legacy：`life_palace_stem`

流年命宫所在宫的宫干起四化（陆斌兆体系）。

代码位置：`services/ziwei_engine/__init__.py` · API 默认与引擎一致（`year_stem`）

**Phase 4 状态**：✅ HTTP / 引擎 / 文档默认已对齐

---

## Z-07 缺失字段机制

- 引擎：`ZiweiChart.missing_fields` / `engine_warnings`
- 示例：`true_solar_time` 修正失败时写入 missing

**Phase 2 状态**：✅

---

## 参数默认值汇总（引擎入口）

建议在 `ziwei_full()` 增加或使用以下默认值：

```python
DEFAULT_ZIWEI_METHODS = {
    "liunian_life_method": "taisui",
    "liuyue_method": "doujun",
    "youbi_method": "month",
    "wenchang_method": "hour",
    "xiaoxian_start_method": "standard",
}
```

> **API 注意**：`/api/v1/ziwei/full` 当前仅透传部分参数（见 [ziwei-gap-audit.md](ziwei-gap-audit.md) §4.1）。完整流派控制需调用 Python `ziwei_full()` 或后续扩展 `ZiweiRequest`。

---

---

## Z-09 年干支界

### 默认：`lichun`（立春换年）

- 使用 sxtwl `getYearGZ()`，与八字节气年一致
- 影响：五虎遁月干、命宫天干、年支系星（魁钺、天马等）

### Legacy / 对照：`normal`（正月初一）

- 使用 `getLunarYear()` 推算年柱，与 iztro `yearDivide=normal` 对齐
- 典型边界：立春后、春节前（如 1988-2-4 晚子 → 1988-2-5 仍属丁卯年）

```json
{ "year_divide": "normal" }
```

---

## Z-10 晚子时换日

### 默认：`solar_next`（公历进次日）

- `late_zishi=true` 且 hour=23 时，公历日期 +1 后再取农历排命宫与安星
- 与多数「晚子作次日」排盘软件一致

### 对照：`forward`（农历日 +1 安星）

- 公历不换日；**仅** `place_main_stars` 使用「公历次日的农历日」
- 对齐 iztro `dayDivide=forward`；常与 `year_divide=normal` 联用（ZW03 边界）

### Legacy：`current`（不换日）

```json
{ "day_divide": "forward" }
```

详见 `docs/reports/ZW03-DUAL-TRACK.md`。

---

## Z-11 童限（起运前运限）

### 状态：**草案 · 未 HTTP 一等字段**（P2-05 / R043）

童限指大限起运前的运限段。当前引擎通过 `dayun.items[0].start_age` 表达起运年龄；**独立童限 horoscope 字段未上线**。

| 层级 | 行为 |
|------|------|
| 引擎 | 大限 `items` 首段 `start_age` / `start_year` 为起运锚点 |
| API | 未实现专章 `tongxian` 时，可在 `missing_fields` 含 `tongxian_horoscope`（advisory） |
| FE Timeline | 首段 `start_age > 1` 时标注「起运前」；不伪造童限流年 |
| 报告卷三 | 展示引擎 `dayun` 表；童限细表待 P3 |

Schema 草案（W16 前，非 breaking）：

```json
"tongxian": {
  "start_age": 3,
  "pre_limit_years": 2,
  "palace_name": "命宫",
  "trust_level": "advisory",
  "note": "对齐文墨童限表；主盘仅供参考"
}
```

与 **ZW18 裁决**（1998-01-28 命宫 trust）区分：ZW18 属本命 trust 黄金集；Z-11 属运限扩展轨。

---

## P2-09 Horoscope 运限对照

### 状态：**advisory 脚本轨**（R041–R042 待脚本落地）

| 脚本 | 用途 | 状态 |
|------|------|------|
| `make verify-iztro` | 本命主星对照 | ✅ CI 可选 |
| `make verify-iztro-hour` | 右弼 `hour` 口径 | ✅ |
| `scripts/verify_ziwei_horoscope_iztro.mjs` | 大限/流年抽样 diff | ✅ R041 |
| `scripts/wenmo_engine_diff.py --horoscope` | 文墨 xlsx 运限表 | ✅ R042 |

原则（对齐 PRODUCT.md 双轨）：

1. 差异仅写入 `engine_warnings` / `colophon.wenmo_advisory` / explain `inference` 层
2. **不**静默修正主盘或覆盖 `palaces`
3. WM01 等黄金集 diff 报告为 **non-blocking** advisory

---

## 变更记录

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-07-11 | v1.0 | Phase 0 口径确认，默认对齐设计文档 |
| 2026-07-12 | v1.3 | Z-11 童限草案 + P2-09 horoscope 对照轨（R078） |
| 2026-07-11 | v1.2 | Z-10 day_divide；ZW03 双轨文档 |
