# 资料文件夹可复用清单

## 可直接纳入 c2 的资料

- `D:\Users\Administrator\Desktop\资料\c1\data\ground_truth_cases.json`
- `D:\Users\Administrator\Desktop\资料\c1\data\glossary.json`
- `D:\Users\Administrator\Desktop\资料\c1\data\cities.json`
- `D:\Users\Administrator\Desktop\资料\c1\docs\openapi.json`
- `D:\Users\Administrator\Desktop\资料\c1\docs\samples`
- `D:\Users\Administrator\Desktop\资料\学习文件\ziwei-main` 中与八字、紫微直接相关的算法文档

## 适合做参考，不建议直接覆盖

- `D:\Users\Administrator\Desktop\资料\bazi-master`
- `D:\Users\Administrator\Desktop\资料\bazi-lib-main`
- `D:\Users\Administrator\Desktop\资料\lunar-python-master`
- `D:\Users\Administrator\Desktop\资料\iztro-main`
- `D:\Users\Administrator\Desktop\资料\react-iztro-main`

## 高价值主题

- 八字：
  - 十神
  - 藏干
  - 纳音
  - 空亡
  - 神煞
  - 调候
  - 格局
  - 大运流年
- 紫微：
  - 命宫 / 身宫
  - 五行局
  - 14 主星
  - 辅星 / 杂曜
  - 四化
  - 大限 / 流年 / 流月

## 资料整理建议

- 先迁“数据和契约”，再迁“算法文档”，最后才考虑代码。
- 能用于对照的原始数据优先保留，不做无必要的格式转换。
- 若同类文件在 c2 已存在，默认差异合并，不直接覆盖。
