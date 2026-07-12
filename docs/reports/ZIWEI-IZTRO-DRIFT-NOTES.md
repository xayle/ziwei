# 紫微黄金盘 × iztro 交叉核验说明

> 生成工具：`make verify-iztro` / `make verify-iztro-calibrate`  
> 最新机器报告：`docs/reports/ziwei-iztro-diff-latest.json`

## 根因与修复（2026-07-11）

### ZW02–08 主星 0/14 → **已修复**

**原因**：`services/ziwei_engine/stars_main.py` 中 `_place_ziwei()` 未实现设计文档的「奇退偶进」偏移，与 `docs/design/ziwei/03-紫微星定位.md` 及 iztro `getStartIndex()` 不一致。

**修复**：按设计文档重写 `_place_ziwei()`；`python scripts/snapshot_ziwei_golden.py` 刷新 golden 坐标。

**修复后 iztro 主星对齐**：

| ID | main vs iztro | verified |
|----|---------------|----------|
| ZW01/02/04/05/06/07/08 | 14/14 | ✅（辅煞右弼仍 ±1 差） |
| ZW09–ZW12 | 14/14 | ✅（2026-07-12 校准；辅煞右弼仍 ±1 差） |
| ZW03 | 0/14 | ❌ 边界用例 |

### ZW03 边界用例（双轨，未改 canonical golden）

| 轨道 | 参数 | 命宫 | 说明 |
|------|------|------|------|
| **c2 引擎 canonical** | `year_divide=lichun` + `day_divide=solar_next` | 乙丑 | 黄金盘 / API 默认 |
| **iztro 对照** | `year_divide=normal` + `day_divide=forward` + ti=12 | 癸丑 | 交叉核验轨 |

详见 [`ZW03-DUAL-TRACK.md`](./ZW03-DUAL-TRACK.md)。

**决策**：保留引擎为产品 canonical；Report/API 通过 `iztro_crosscheck.advisory` 提示分歧。

### 晚子时换日（day_divide）

| 值 | 行为 |
|----|------|
| `solar_next`（默认） | 23:00–23:59 公历进次日再排盘 |
| `forward` | 公历不换日；**仅安星**农历日 +1（对齐 iztro `dayDivide=forward`） |
| `current` | 不换日 |

## 常用命令

```bash
make verify-iztro-calibrate
make verify-iztro
make verify-iztro-hour    # 右弼 hour 口径，辅煞 0 diff（ZW01–12 除 ZW03）
python scripts/snapshot_ziwei_golden.py
node scripts/verify_ziwei_iztro.mjs --write-verified
node scripts/verify_ziwei_iztro.mjs --youbi=hour
```

## Report / API

- `POST /api/v1/ziwei/full` 响应含可选字段 `iztro_crosscheck`
- `status=life_palace_only` → 「与 iztro 主星未对齐」
- `status=life_palace_mismatch` → 年界/晚子时口径提示（典型：ZW03 类盘）

## 辅煞漂移

各盘 **右弼** 与 iztro 差 1 宫为 `youbi_method=month` 流派差（iztro 依生时安右弼），不阻断主星验盘。引擎在 `engine_warnings` 中标注此差异。
