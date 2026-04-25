# 全栈代码检查与优化规划（2026-04-01）

## 1. 检查范围
- 前端：`frontend/`（Vue3 + TS + Vitest + Vite）
- 后端：`run.py`、`routers/`、`services/`、`app/`、`db.py`
- 底层与工程化：`scripts/`、`migrations/`、测试与质量配置

## 2. 体检结果（当日实测）
### 2.1 后端质量状态
- `pytest tests -q`：**2592 passed, 2 skipped**（全绿）
- `ruff check .`：**567 个问题**（历史技术债为主）
  - 高占比问题：`F401` 未使用导入、`E402` 顶层导入顺序、`F841` 未使用变量
  - 结构性问题：`run.py` 超长、跨域导入较多，导致可维护性下降

### 2.2 前端质量状态
- `npm run type-check`：通过
- `npm run test`：**341 passed**
- `npm run build`：初始失败（`ZiweiView.vue` 样式块未闭合），已修复

### 2.3 当前风险画像
- **功能正确性风险：低**（核心测试全绿）
- **可维护性风险：中高**（lint 债务集中、文件复杂度高）
- **交付稳定性风险：中**（构建类问题可能在后续迭代重复出现）

## 3. 优化目标
1. 不破坏现有功能（以回归测试为硬门槛）
2. 先清“高收益低风险”问题，再做结构重构
3. 建立分层质量基线（前端/后端/脚本）

## 4. 分层优化路线图

### Phase A（1-2天，低风险，立即执行）
- 前端
  - 修复构建阻塞项（已完成 1 项）
  - 为 `npm run build` 增加 CI 必跑门禁
- 后端
  - 对业务主目录启用增量 lint（先不扫 `tests/legacy` 与临时脚本）
  - 批量清理明显无副作用项：未使用导入、未使用局部变量
- 底层脚本
  - 将 `_compare_*`、`_check_*` 归档到 `scripts/dev_tools/`
  - 明确“生产代码 vs 临时脚本”边界，避免被统一质量门禁误伤

### Phase B（3-5天，中风险，结构整理）
- 后端
  - 拆分 `run.py`：
    - `app/bootstrap.py`（应用初始化）
    - `app/middlewares.py`（中间件注册）
    - `app/routes.py`（路由挂载）
  - 统一异常与日志上下文字段（request_id、user_id、route）
- 前端
  - 抽离 `ZiweiView.vue` 过大样式与模板片段（拆分子组件）
  - 建立按视图维度的样式文件边界，降低单文件复杂度

### Phase C（1-2周，中高风险，质量基线固化）
- 建立分目录 lint 策略：
  - `app/ routers/ services/`：严格
  - `tests/`：宽松但禁止明显错误（如裸 `except`）
  - `scripts/`：单独规则
- 引入复杂度阈值（函数长度、圈复杂度）并逐步收敛
- 完成一次“主干无新增 lint 债务”治理（new issues = 0）

## 5. 建议的执行顺序
1. 先做 Phase A，确保构建与增量质量门禁稳定
2. 再做 Phase B 的 `run.py` 拆分与前端大文件拆分
3. 最后做 Phase C 的规则固化，避免反复回潮

## 6. 验收标准
- 后端：`pytest tests -q` 全绿；主目录 lint 告警显著下降
- 前端：`type-check` + `test` + `build` 全通过
- 工程化：CI 阶段固定执行上述检查并阻断回归
