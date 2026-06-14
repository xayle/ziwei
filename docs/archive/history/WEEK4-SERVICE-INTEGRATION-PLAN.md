# Week 4 - 服务层集成和路由重构计划

**状态**: 🟡 规划中 (0% - 待开始)  
**预计工期**: 4-5 天  
**优先级**: P0 (关键)

---

## 📋 工作分解结构 (WBS)

### Phase 1: 服务层集成 (2-3 小时)

#### 1.1 auth_service.py 更新
- [x] 添加 AuthenticationException 和 AuthorizationException 导入
- [x] 更新 verify_token 异常处理
- [x] 更新 verify_refresh_token 异常处理
- [x] 更新 create_access_token 异常处理
- [x] 添加 @handle_exceptions 装饰器到关键函数
- [x] 编写和运行单元测试

#### 1.2 delegation_service.py 更新
- [x] 替换 PermissionDelegationError 为 AppException 家族
- [x] 使用 AuthorizationException 处理权限检查失败
- [x] 使用 ValidationException 处理验证失败
- [x] 使用 ResourceNotFoundException 处理资源不存在
- [x] 编写集成测试

#### 1.3 bazi_full_service.py 更新
- [x] 替换 HTTPException 为标准异常
- [x] 使用 ValidationException 处理验证错误
- [x] 使用 BusinessException 处理业务逻辑错误
- [x] 添加 @handle_exceptions 装饰器
- [x] 编写业务逻辑测试

#### 1.4 其他服务更新
- [x] permission_service.py
- [x] permission_cascade_service.py
- [x] case_service.py (如果存在)
- [x] member_service.py (如果存在)

### Phase 2: 路由层集成 (1-2 小时)

#### 2.1 认证路由 (routers/auth.py)
- [x] 更新异常处理
- [x] 使用新的异常类
- [x] 添加 @handle_exceptions 装饰器
- [x] 测试错误响应

#### 2.2 其他关键路由
- [x] routers/cases.py
- [x] routers/members.py
- [x] routers/events.py
- [x] routers/delegations.py
- [x] routers/scenarios.py
- [x] routers/snapshots.py

### Phase 3: 测试和验证 (1-2 小时)

- [x] 运行完整测试套件
- [x] 验证错误响应格式
- [x] 性能基准测试
- [x] 集成测试

---

## 📊 关键指标

| 指标 | 当前 | 目标 |
|------|------|------|
| 服务异常处理覆盖 | 60% | 100% |
| 路由异常处理覆盖 | 50% | 100% |
| 测试通过率 | 81.7% | 95%+ |
| 错误响应标准化 | 30% | 100% |

---

## 🎯 完成标准

✅ **所有服务**使用新的异常类  
✅ **所有路由**返回标准化错误响应  
✅ **测试通过率** >95%  
✅ **文档完成** 100%  

---

## 时间线

```
2026-02-28 09:00 - 规划完成 ✅
2026-02-28 09:30 - Phase 1.1: auth_service.py
2026-02-28 11:00 - Phase 1.2: delegation_service.py
2026-02-28 12:30 - Phase 1.3: bazi_full_service.py
2026-02-28 14:00 - Phase 1.4: 其他服务
2026-02-28 15:30 - Phase 2: 路由集成
2026-02-28 17:00 - Phase 3: 测试验证
2026-02-28 18:00 - 完成和交付
```

---

## 风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 现有路由中断 | 中 | 高 | 增量更新 + 完整测试 |
| 向后兼容破裂 | 低 | 高 | 保持接口签名 |
| 性能下降 | 低 | 中 | 性能基准测试 |

---

## 下一步

[等待开始实施...]
