# 浮生 · 品牌标识 v2（简约国风）

| 字段 | 内容 |
|------|------|
| **版本** | brand-logo-2.0 |
| **日期** | 2026-07-13 |
| **取代** | `fusheng-logo.png`（墨金山水圆形徽章 · legacy） |
| **定案** | [`FUSHENG-MINIMAL-GUOFENG-DESIGN.md`](./FUSHENG-MINIMAL-GUOFENG-DESIGN.md) |

---

## 一、设计意图

| 旧 LOGO 问题 | v2 方向 |
|--------------|---------|
| 黑底满月山水 · 与暖纸 UI 打架 | **透明底**，直接落在纸面上 |
| 装饰过多（云、亭、鸟） | **墨 + 铜弧 + 朱线**，三件足矣 |
| AI 国风模板感 | **界画弧线**（宋式章法），非纹样堆砌 |

---

## 二、图形语法

```text
        ╭──────────╮
        │   浮生    │  ← 墨 #1a1410 · LXGW / 宋体
        ╰────┬─────╯
             │         ← 铜弧 #b8894d · 下开 · 寓「展卷」
             ▏         ← 朱线 #8b3a2a · 开口处 · 点睛
```

- **铜弧**：270° 界画圆，**下方开口** — 留白即结构  
- **朱线**：开口正中 1 笔，对应校勘/朱批，**不作满屏印章**  
- **字**：「浮生」二字，与产品 UI 同字体族  

---

## 三、资产清单

| 文件 | 用途 |
|------|------|
| `frontend/src/assets/brand/fusheng-mark.svg` | **主标识** · 导航 / favicon / 首页 |
| `frontend/src/assets/brand/fusheng-logo.svg` | **横排锁标** · 报告封面 / 打印 |
| `frontend/src/assets/brand/fusheng-logo.png` | 栅格导出（512 / 128 / 44 由脚本生成） |
| `frontend/src/assets/brand/fusheng-logo-legacy.png` | 旧版归档 · **勿再引用** |

---

## 四、使用规则

- 最小尺寸：**24px**（仅 mark）；导航 **40–44px**  
- 禁止：裁圆、加投影、叠渐变、与旧版混用  
- 深色底：可反色为纸 `#f5f0e6` 字 + 铜弧，朱线保留  

---

## 五、导出

```bash
python scripts/export_brand_logo_png.py
```

依赖 Playwright · 输出 `fusheng-logo.png` → `frontend/public/` 同步。
