# R105 · M5 能辩 — 产品试清单 — 2026-07-12（pass 3 · 2026-07-13）

**M5**：vs ChatGPT 至少 1 处口径可辩护。

## 对比任务

| # | 维度 | 浮生口径 | ChatGPT 典型口径 | 可辩护？ | 一句理由 |
|---|------|----------|------------------|:--------:|----------|
| 1 | 格局/用神 | explain batch + `layer`/`confidence` 标注（ZIP09 双轨表） | 泛化叙述、无引擎/典籍分层 | ☑ | 报告互证章 E2E 可见 engine vs classical 双轨，非黑箱一句话 |
| 2 | trust/degraded | 200 + `TrustDegradedBanner` + `missing_fields` | 常隐藏不确定性或仍给长文 | ☑ | ZW03 degraded 横幅 E2E；八字 degraded 列缺失字段 |
| 3 | 卷五推断 | 默认折叠 + `data-layer="inference"` | 首屏长文推断 | ☑ | `fusheng-trial-read` 断言卷五深读默认不可见；须展开才读 |
| 4 | 典籍 cite | 仅 `verified classic_id`（content_policy 拒 unverified） | 常无出处或 hallucinate 书名 | ☑ | `tests/test_content_policy.py` + `VolumeSection` cite badge |

**通过标准：** 至少 **1 行** 可辩护 — **4/4 已填理由**（自动化+代码证据）。

## 自动化预检

- `content_policy` cite 拒 unverified ✅
- `VolumeSection` cite badge ✅
- ZW18 degraded E2E ✅
- 报告 ZIP09/ZW03 双轨 E2E ✅

## 签字

| 角色 | 姓名 | 日期 | M5 |
|------|------|------|:--:|
| 产品 | 自动化代理（4 维可辩护已记录） | 2026-07-13 | ☐ |

**说明：** 口径对比已文档化；产品正式签字后标 R105 ☑。
