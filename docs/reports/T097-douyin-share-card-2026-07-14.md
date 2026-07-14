# T097 · 抖音竖版分享卡导出（2026-07-14）

| 字段 | 内容 |
|------|------|
| **任务** | T097 / BE-GTM-11 · `export/card?layout=douyin` 9:16 |
| **状态** | ☑ 通过 |
| **验收** | PNG 输出 |

## 交付

| 路径 | 说明 |
|------|------|
| `services/pdf_exporter.py` | `render_douyin_share_card_html` · `generate_share_card(layout=)` |
| `routers/export.py` | `GET …/export/card?layout=douyin` |
| `tests/test_export_card_douyin_t097.py` | HTML 9:16 + API 传参 |

## 规格

- 视口 **1080×1920**（9:16）
- 内容：品牌「浮生」· 卷名 · 格局 · 钩子事实句 · disclaimer
- `layout` 仅 `default` \| `douyin`；非法 → 422

## 验证

```text
pytest tests/test_export_card_douyin_t097.py tests/test_share_card_exporter.py → 6 passed
```
