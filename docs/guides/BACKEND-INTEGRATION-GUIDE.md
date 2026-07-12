# 后端接入说明

这份说明面向前后端联调，目标是把当前 `c2` 的后端入口、路由前缀、前端请求方式和本地排查路径一次说清楚。

## 1. 后端入口

### 启动入口

- `run.py` 是当前 FastAPI 应用入口。
- `app/entrypoint_factory.py` 负责创建应用。
- `app/app_assembly.py` 负责组装中间件、路由、静态资源和健康检查。

### 关键启动流程

1. `run.py` 初始化日志。
2. `create_application(logger=logger)` 创建 FastAPI 实例。
3. `app/bootstrap.py` / `app/app_assembly.py` 挂载中间件与路由。
4. `app/static_routes_setup.py` 提供静态站点和 `/new`、`/bazi`、`/ziwei` 等页面入口。
5. `app/openapi_docs.py` 提供 `/openapi.json`。

### 本地启动

推荐方式：

```bash
uvicorn run:app --host 127.0.0.1 --port 8000
```

Windows 下也可以使用项目已有的启动脚本。如果 8000 被占用，实际端口以启动日志为准。

## 2. 路由结构

### 主要 API 前缀

- 八字：`/api/v1/bazi`
- 紫微：`/api/v1/ziwei`
- 校验：`/api/v1/verify`
- 健康检查：`/health`
- OpenAPI：`/openapi.json`

### 路由挂载来源

- `app/router_setup.py` 负责将各个 `routers/*` 模块挂载到 FastAPI。
- `routers/bazi.py` 内部声明 `prefix="/api/v1/bazi"`。
- `routers/ziwei.py` 内部声明 `prefix="/api/v1/ziwei"`。

### 当前前端主要调用

- `frontend/src/api/bazi.ts`
- `frontend/src/api/ziwei.ts`
- `frontend/src/api/client.ts`

## 3. 前后端调用方式

### API 基础地址

前端会优先读取：

- `VITE_API_BASE_URL`

如果没有配置，默认走同源 `/`。

### 请求拦截

`frontend/src/api/client.ts` 做了两件事：

- 自动从 `localStorage.token` 读取 token，并注入 `Authorization: Bearer <token>`
- 遇到 `401` 清除本地 token 并派发 `app:unauthorized`
- 遇到网络错误或 `5xx` 派发 `app:backend-unavailable`

这意味着前端报错时，优先看：

1. 后端是否真正返回了 500
2. 是否是网络断开或 API baseURL 配错
3. 是否是鉴权失败导致的 401

## 4. 核心接口

### 八字

#### `POST /api/v1/bazi/full`

前端主入口。

请求由 `frontend/src/api/bazi.ts` 的 `computeBazi()` 发起。

这个接口用于八字全量排盘，包含：

- 四柱
- 十神
- 用神
- 格局
- 大运
- 流年
- 五行
- 神煞
- 各种扩展分析

#### 其他八字接口

- `POST /api/v1/bazi/liunian-domain`
- `POST /api/v1/bazi/dayun-report`
- `POST /api/v1/bazi/compatibility`
- `POST /api/v1/bazi/monthly`
- `POST /api/v1/bazi/analyze`
- `GET /api/v1/bazi/jieqi`
- `POST /api/v1/bazi/geju`
- `POST /api/v1/bazi/calendar-compare`
- `POST /api/v1/bazi/batch-compare`
- `POST /api/v1/bazi/liunian-report`
- `GET /api/v1/bazi/liunian-report/{task_id}`
- `GET /api/v1/bazi/golden-cases`

### 紫微

#### `POST /api/v1/ziwei/full`

前端主入口。

请求由 `frontend/src/api/ziwei.ts` 的 `computeZiwei()` 发起。

这个接口用于紫微斗数完整排盘，包含：

- 农历信息
- 命宫 / 身宫
- 五行局
- 宫位列表
- 主星 / 辅星
- 大运 / 流年 / 流月
- 飞星盘
- 格局、建议、摘要

#### 其他紫微接口

- `GET /api/v1/ziwei/demo`
- `POST /api/v1/ziwei/compatibility`
- `POST /api/v1/ziwei/multi_compat`
- `POST /api/v1/ziwei/batch`
- `POST /api/v1/ziwei/flying`

## 5. 本地联调

### 前端开发模式

如果前端单独启动，建议配置：

- `VITE_DEV_API_TARGET=http://127.0.0.1:8000`
- 或者直接设置 `VITE_API_BASE_URL=http://127.0.0.1:8000`

### 建议联调用法

1. 启动后端。
2. 启动前端。
3. 打开首页或直接访问排盘页面。
4. 先用最小输入跑八字和紫微的全量接口。
5. 确认响应结构后，再调复杂模块。

### 推荐先验接口

先验证这两个接口：

- `POST /api/v1/bazi/full`
- `POST /api/v1/ziwei/full`

如果这两个接口正常，说明基础排盘链路基本通了。

## 6. 500 排查路径

当前你遇到的 `Request failed with status code 500`，建议按下面顺序查：

### 第一步：确认请求是否真的打到后端

- 看浏览器 Network
- 看请求 URL 是否正确
- 看是否被发到了错误的 baseURL

### 第二步：确认后端是否启动成功

- 访问 `GET /health`
- 访问 `GET /openapi.json`
- 如果这两个都失败，先修启动问题，不要继续看业务接口

### 第三步：确认八字 / 紫微核心接口

- 八字看 `POST /api/v1/bazi/full`
- 紫微看 `POST /api/v1/ziwei/full`

如果这两个接口返回 500，优先查看：

- 入参格式
- 时间字段是否缺失
- 经度或时区是否不合法
- 算法引擎内部异常

### 第四步：看后端日志

当前项目会在 FastAPI 异常抛出时直接返回 `detail`，所以日志里通常能看到具体异常栈。

重点关注：

- `ValueError`
- `HTTPException`
- 时间解析失败
- 紫微引擎计算失败
- 数据库读取失败

### 第五步：做最小请求

如果复杂表单报错，先用最小化数据测试：

- 八字：固定一个合法出生时间、时区、经度
- 紫微：固定一个合法出生年月日时和性别

这样可以快速确认是“算法问题”还是“表单映射问题”。

## 7. 接入约定

- `c2` 旧前端保留，不要把新页面逻辑直接塞回旧路由。
- 新前端和新排盘页优先走 `/new`、`/bazi`、`/ziwei` 的新版入口。
- 后端 API 以 `/api/v1/...` 为主，不建议前端直接拼旧静态页面路径。
- `openapi.json` 是接口对齐的机器可读基准，前后端改接口时先对它。

## 8. 最小示例

### 八字

```bash
curl -X POST http://127.0.0.1:8000/api/v1/bazi/full \
  -H "Content-Type: application/json" \
  -d '{
    "dt": "1990-01-15T08:30:00",
    "lon": 121.4737,
    "tz": "Asia/Shanghai",
    "mode": "dual",
    "solar_time_enabled": false,
    "gender": "male"
  }'
```

### 紫微

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ziwei/full \
  -H "Content-Type: application/json" \
  -d '{
    "year": 1990,
    "month": 1,
    "day": 15,
    "hour": 8,
    "minute": 30,
    "gender": "男",
    "template_version": "standard"
  }'
```

## 9. 结论

如果你的目标是让前端稳定接上后端，当前优先级应该是：

1. 先保证 `/health` 正常
2. 再保证 `/api/v1/bazi/full` 正常
3. 再保证 `/api/v1/ziwei/full` 正常
4. 最后再做首页和页面展示优化

