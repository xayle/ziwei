# T095 · H5 短 token 免登录卷一摘要（2026-07-14）

| 字段 | 内容 |
|------|------|
| **任务** | T095 / BE-GTM-07 · H5 短 token 读卷一摘要 |
| **状态** | ☑ 通过 |
| **验收** | 落地页免登录试读 |

## 交付

| 路径 | 说明 |
|------|------|
| `services/auth_service.py` | `create_h5_preview_token` / `verify_h5_preview_token`（`token_use=h5_preview`，无 username） |
| `routers/auth.py` | `POST /api/v1/auth/h5-preview-token`（需登录，校验 case 归属） |
| `routers/life.py` | `GET /api/v1/life/preview/{case_id}`（`?token=` 或 Bearer） |
| `services/life_volume_service.py` | `project_h5_vol1_preview`（仅 preface+vol1，正文裁剪） |

## 流程

```text
登录 → POST /auth/h5-preview-token {case_id}
  → 短 JWT（默认 30min，env H5_PREVIEW_TOKEN_MINUTES）
落地页 → GET /life/preview/{case_id}?token=…
  → volumes = [preface, vol1] + disclaimer
正式 access JWT 不可用于 preview；preview JWT 不可当登录
```

## 验证

```text
pytest tests/test_h5_preview_token_t095.py → 6 passed
```
