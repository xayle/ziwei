# 本地端口文档一致性收尾报告（2026-04-05）

## 目标
统一本地开发文档口径：
- 默认端口为 8000
- 当 8000 被占用时，`start-local.ps1` / `deploy.ps1 -Environment local -Action up` 可能自动回退
- 示例优先使用 `BASE_URL` / `PORT` 变量，减少硬编码误导

## 本次已完成修改

### 1) 根文档变量化
- `README.md`
  - 快速启动示例新增 `PORT=8000`，`uvicorn` 命令改为 `--port ${PORT}`
  - API 访问示例改为 `${BASE_URL}/...`
  - Local Smoke 中 terminal A 命令改为 `PORT=8000; uvicorn ... --port ${PORT}`

### 2) 部署指南严格变量化（仅开发段落）
- `docs/DEPLOYMENT-GUIDE.md`
  - 集成测试、直接运行、启通验证三个开发段落改为 `PORT + BASE_URL` 形式
  - 保留 systemd / Docker 生产示例固定端口（符合生产部署语义）

### 3) 补齐非归档文档剩余硬编码入口
- `docs/README-DELIVERY.md`
  - 静态入口改为 `${BASE_URL}/static/index.html`，并保留默认示例
- `docs/QA-TAB-CHECKLIST.md`
  - 启动命令段改为 `PORT + BASE_URL` 与 `--port ${PORT}`

### 4) 测试文档对齐
- `tests/e2e/README.md`
  - 运行说明改为先设置 `BASE_URL`，并明确端口回退时应替换为实际端口

## 当前剩余“8000”引用判定

### A. 建议保留（默认值/示例说明）
- `docs/api.md`
- `docs/DEPLOY_SCRIPT_GUIDE.md`
- `docs/PERMISSION-MANAGEMENT-GUIDE.md`
- `README.md`
- `tests/e2e/README.md`

### B. 建议保留（生产部署示例）
- `docs/DEPLOYMENT-GUIDE.md` 中 systemd / Docker 示例

### C. 历史记录文档（可保留不改）
- `docs/ADDITIONAL-ISSUES-2026-02-25.md`
- `docs/DECISION-RECORD-2026-02-25.md`
- `docs/N7-gate-verification-report.md`
- 以及 `docs/archive/` 下历史材料

## 结论
本次收尾后，主干开发文档已实现“默认 8000 + 自动回退 + 变量化调用”的一致口径；
剩余固定端口文本主要为默认值示例、生产部署示例或历史审计记录，均为可接受保留项。