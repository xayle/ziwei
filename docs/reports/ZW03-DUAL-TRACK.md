# ZW03 双口径说明（lichun golden vs normal+forward iztro）

> 用例：`1988-02-04 23:45 男` — 立春前一日 + 晚子时边界

## 两条合法口径

| 轨道 | 参数 | 命宫 | 产品角色 |
|------|------|------|----------|
| **引擎 canonical（golden）** | `year_divide=lichun` + `day_divide=solar_next` + `late_zishi=true` | **乙丑** | 默认 API / 黄金回归 / Report 主盘 |
| **iztro 对照** | `year_divide=normal` + `day_divide=forward` + `late_zishi=true` | **癸丑** | 交叉核验 / advisory 提示 |

## 口径差异来源

1. **年界**：引擎默认立春换年（对齐八字节气年）；iztro 默认正月初一换年（`yearDivide=normal`）。
2. **晚子换日**：
   - `solar_next`（默认）：23:00–23:59 公历进次日，再取农历排命宫与安星。
   - `forward`（iztro `dayDivide=forward`）：公历不换日；**仅安星**时农历日 +1（等价于取公历次日的农历日）。
3. **立春前一日**：1988-02-04 仍属丁卯年（正月初一界）/ 戊辰年（立春界），故命宫干支分歧最大。

## API 用法

```json
{
  "year": 1988, "month": 2, "day": 4, "hour": 23, "minute": 45, "gender": "男",
  "year_divide": "normal",
  "day_divide": "forward"
}
```

响应 `iztro_crosscheck` 在 `/full` 与 `GET /demo?crosscheck=true` 可用；ZW03 类边界可能仍显示 advisory（辅煞如右弼 ±1 宫属流派差）。

## 决策

- **不**将 iztro 口径静默覆盖引擎 golden。
- Report 展示 `iztro_crosscheck.advisory`、**双轨对照表**（`report-iztro-dual-track`）与年界/换日 meta。
- 详见 [`ZIWEI-IZTRO-DRIFT-NOTES.md`](./ZIWEI-IZTRO-DRIFT-NOTES.md)。
