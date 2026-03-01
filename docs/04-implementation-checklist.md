# 开发前检查清单 & 实施指南 (v1.0)

## 目标
确保所有P0问题已解决，代码设计已冻结，开发可以开始。

---

## 📋 Part 1: Schema 文档检查

### Member Schema
- [ ] 所有字段在schemas.py中定义 (使用Pydantic v2)
- [ ] authorization.status枚举值在constants.py中
- [ ] relationship枚举值在constants.py中
- [ ] birth_info.location_lon验证范围硬编码 (70-140)
- [ ] Pydantic校验规则已实现 (validators, field_validators)
- [ ] 前端表单字段与schema对齐 (用JSON schema生成表单)
- [ ] 单元测试覆盖所有validation规则 (> 90%)

### Event Schema
- [ ] event_type枚举包含8个固定类型 + OTHER
- [ ] datetime_info precision验证逻辑正确
- [ ] status转移规则在service层实现
- [ ] scale_context默认值定义在constants中
- [ ] evidence文件上传逻辑已设计 (storage_location类型)
- [ ] computed_impact计算方法文档化
- [ ] Rule versioning字段已添加 (rule_id, rule_version, rule_reference)

### Scenario Schema
- [ ] variant_on逻辑: 若base_event_id 非null则为"假如"场景
- [ ] analysis_result生成后只读 (update时跳过此字段)
- [ ] timeline计算逻辑文档化 (impact_window_start/end_months)
- [ ] similar_historical_cases数据源已确定 (模板库或真实案例库)
- [ ] model_version格式定义 (e.g., v1_2026 or semantic versioning)
- [ ] confidence_score组合算法文档化
- [ ] 前端"高风险确认弹窗"实现方案已评审

### ConfidenceModel
- [ ] confidence_score = weighted_sum(birth_precision[0.4] + evidence_quantity[0.3] + historical_accuracy[0.3])
- [ ] how_to_improve建议生成逻辑已实现
- [ ] 前端显示细节分解的UI已设计
- [ ] 用户理解度测试: 命理师、普通用户是否理解confidence含义

---

## 🏗️ Part 2: 架构设计检查

### 工具箱管理
- [ ] tools/base.py定义ToolBase、ToolMetadata、ToolCategory
- [ ] tools/registry.py定义ToolRegistry单例
- [ ] 所有7个工具已在registry中注册计划书
- [ ] ToolMetadata.input_schema、output_schema格式已确定
- [ ] 动态表单生成逻辑已原型验证 (前端能否正确渲染schema)
- [ ] 工具执行timeout设定 (建议 2s)
- [ ] 工具错误处理统一: error_code库已设计

### API端点设计
- [ ] GET /api/v1/tools 返回所有工具元数据
- [ ] GET /api/v1/tools/categories 返回分类
- [ ] POST /api/v1/tools/{tool_id}/execute 执行工具
- [ ] POST /api/v1/tools/{tool_id}/execute-batch 批量执行
- [ ] 所有endpoint已在Swagger文档中定义
- [ ] 响应格式统一 (success/error/metadata)

### 前端架构
- [ ] 工具网格卡片UI已原型
- [ ] 动态表单生成已测试 (至少3种input类型: text/datetime/select)
- [ ] 结果展示容器设计完成 (支持表格、图表、SVG等)
- [ ] 工具之间无耦合 (各工具可独立开发)
- [ ] 页面性能目标定义 (工具列表加载 <500ms)

### 迁移计划
- [ ] routers/compute.py中所有7个工具的迁移路径清晰
- [ ] 旧API endpoint `/compute/*` 的deprecation plan已确定
- [ ] 工具迁移顺序: 优先级已排序 (难度 + 使用频率)
- [ ] 是否保留旧endpoint向后兼容? → 决策已记录

---

## 🔐 Part 3: 权限 & 审计设计检查

### RBAC实施
- [ ] 5个核心角色已在constants.py中定义
- [ ] 权限矩阵在代码中硬编码 (或从config表读取?)
- [ ] AuthContext类已实现has_permission()方法
- [ ] @require_permission装饰器已实现
- [ ] DELEGATE权限过期逻辑已实现 (定时任务检查expires_at)
- [ ] GUEST角色通过shared_link实现 (需设计shared_link表)
- [ ] 前端菜单根据role动态显示 (但后端仍需权限检查!)

### 审计日志实施
- [ ] AuditLog数据结构在schemas中定义
- [ ] 所有16个审计事件类型在constants.py中定义
- [ ] 敏感字段脱敏规则在constants中硬编码
- [ ] audit_repo (DAO) 已实现 (create, find, get_range)
- [ ] AuditIntegrityService类已实现链签名逻辑
- [ ] 定时任务 (每周) 验证审计链完整性
- [ ] 审计日志导出功能已规划 (三种格式: csv/json/pdf)
- [ ] 审计日志保留政策已确定 (>= 3年)

### 前端权限展示
- [ ] 无权操作时显示提示: "您无权修改他人数据"
- [ ] 操作者身份标记: "(自己)", "(代理输入)", "(家族成员)" 
- [ ] 脱敏数据标记: "📋 [已脱敏]"
- [ ] 权限升级入口已设计 (例: 从FAMILY_MEMBER申请变为OWNER权限)

---

## 📝 Part 4: 数据模型检查

### ER图与外键
- [ ] Member.owner_id → User.user_id (FK)
- [ ] Event.owner_id → User.user_id (FK)
- [ ] Event.trigger_member_id → Member.member_id (FK)
- [ ] Scenario.base_event_id → Event.event_id (FK, optional)
- [ ] 所有FK都有cascade规则定义 (delete/update behavior)
- [ ] 已检查循环依赖问题

### 数据库表设计
- [ ] 所有表都有: created_at, updated_at, created_by, updated_by
- [ ] 所有timestamp字段用UTC+索引
- [ ] Member表上的唯一索引: (owner_id, alias)
- [ ] Event表上的索引: owner_id, trigger_member_id, status, created_at
- [ ] Scenario表上的索引: owner_id, created_at
- [ ] AuditLog表特殊处理: append-only, 不能UPDATE/DELETE (业务逻辑)

### 迁移脚本
- [ ] 创建Member表的SQL脚本已编写
- [ ] 创建Event表的SQL脚本已编写
- [ ] 创建Scenario表的SQL脚本已编写
- [ ] 创建AuditLog表的SQL脚本已编写
- [ ] 所有脚本已在SQLite上测试
- [ ] 回滚脚本已编写 (DROP TABLE操作)
- [ ] 迁移脚本的执行顺序已文档化

---

## 🧪 Part 5: 测试计划检查

### 单元测试
- [ ] schemas.py验证逻辑 (test_pydantic_validators.py)
  - Member.birth_info.location_lon范围校验
  - Event.status状态转移规则
  - Scenario.variant_on逻辑
  
- [ ] 权限检查逻辑 (test_authorization.py)
  - OWNER可创建自己的Event
  - DELEGATE不能删除Event
  - FAMILY_MEMBER只能读被授权的Member
  - GUEST只能读共享链接内容
  
- [ ] 审计日志链 (test_audit_integrity.py)
  - 新增日志时是否正确形成链
  - 篡改检测: 修改hash后验证失败
  - 篡改检测: 修改signature后验证失败

- [ ] 各个工具单独测试 (test_dayun_tool.py, test_lunar_tool.py, ...)

### 集成测试
- [ ] 创建Member → 审计日志是否自动生成
- [ ] 修改Event状态 → 是否检查权限? 是否记录审计?
- [ ] 导出数据 → 敏感字段是否脱敏?
- [ ] DELEGATE代理输入 → 数据是否标记为"代理"?

### 端到端测试
- [ ] OWNER创建Event → 邀请FAMILY_MEMBER → FAMILY_MEMBER是否能读取?
- [ ] OWNER修改Member信息 → 是否只能OWNER修改?
- [ ] 执行Scenario分析 → 结果是否返回所有4个impact_scores?
- [ ] 导出Event报告 → 文件格式正确? 脱敏规则是否应用?

### 性能测试
- [ ] 工具执行性能: 单个工具 < 2秒
- [ ] 批量查询权限: 1000条records过滤 < 1秒
- [ ] 审计链验证: 全表扫描5年数据 < 30秒

### 安全测试
- [ ] SQL注入: 所有查询都用参数化查询
- [ ] CSRF: 所有POST需要CSRF token
- [ ] 权限越级: 是否能绕过@require_permission装饰器?
- [ ] 审计日志伪造: 是否能直接UPDATE审计表?

---

## 📊 Part 6: 文档检查

### API文档
- [ ] Swagger/OpenAPI已生成 (或使用Pydantic自动生成)
- [ ] 所有新端点已在docs/openapi.json中
- [ ] 权限要求已标注 (e.g., "需要OWNER角色")
- [ ] 错误响应已文档化 (403 Forbidden, 422 Validation Error等)

### 数据字典
- [ ] Member所有字段的数据类型、约束、示例已列表
- [ ] Event所有字段的数据类型、约束、示例已列表
- [ ] Scenario所有字段的数据类型、约束、示例已列表

### 操作手册
- [ ] ADMIN如何审查审计日志?
- [ ] OWNER如何邀请FAMILY_MEMBER?
- [ ] OWNER如何撤销DELEGATE权限?
- [ ] 如何运行审计链完整性检查?
- [ ] 如何导出/备份数据?

---

## 🚀 Part 7: 部署检查

### 环境配置
- [ ] 环境变量文件 (.env.prod) 已创建模板
- [ ] 数据库连接字符串已配置
- [ ] 日志级别已设置 (INFO for prod, DEBUG for dev)
- [ ] 审计日志signing_key已生成并安全存储 (HSM或环境变量)
- [ ] CORS配置已设定 (允许哪些origin)

### 构建与打包
- [ ] requirements.txt已更新 (所有依赖已列)
- [ ] Dockerfile已编写 (若需容器化)
- [ ] docker-compose.yml已编写 (数据库容器)
- [ ] CI/CD流程已配置 (自动化测试、构建)

### 数据迁移
- [ ] 现有数据 (如旧的工具执行历史) 是否需迁移?
- [ ] 迁移脚本已编写并测试
- [ ] 迁移前后数据验证脚本已准备
- [ ] 回滚计划已准备 (若迁移失败)

### 监控与告警
- [ ] 错误日志告警已配置 (ERROR级别自动告警)
- [ ] 审计链完整性异常告警已配置
- [ ] API延迟KPI告警已配置 (>1s告警)
- [ ] 数据库连接池告警已配置

---

## ✅ Part 8: 即刻行动清单 (next 48 hours)

### Day 1 (今天)
- [ ] 将本文档内容添加到项目Wiki/README
- [ ] 组织架构评审会议 (2小时)
  - 讨论: 权限矩阵是否有遗漏?
  - 讨论: 工具箱架构是否太复杂?
  - 讨论: 审计日志retention政策是否合理?
  - Decision: 哪些内容需进一步细化?
  
- [ ] 确认开发顺序
  - Phase 1 (Week 1-2): 创建Member表、Event表、Scenario表
  - Phase 2 (Week 2-3): 实现权限检查中间件
  - Phase 3 (Week 4-5): 实现审计日志系统
  - Phase 4 (Week 6-10): 工具箱架构 + 迁移7个工具
  
- [ ] Technical Lead分配
  - 后端主设计: 谁负责schema设计? 谁负责权限层?
  - 前端主设计: 谁负责工具UI? 谁负责表单生成?
  - DevOps: 谁负责部署流程?

### Day 2 (明天)
- [ ] 创建Trello/Jira Board用于任务管理
- [ ] 第一个Sprint (Week 1) 的user stories已编写
- [ ] 开发环境已准备 (本地数据库setup脚本)
- [ ] Git Branch策略已确定 (例: main/develop/feature/*)
- [ ] Code Review流程已文档化

---

## 🎯 Success Criteria (本检查清单完成后)

```
✅ 所有P0问题已解决
   - 3套Schema文档已完成 (Member/Event/Scenario)
   - 工具箱架构已冻结 (ToolBase + Registry)
   - 权限矩阵已冻结 (5个角色 + 12个resource×action)
   - 审计系统已设计 (16事件类型 + 链签名)

✅ 人力分配确定
   - 后端开发: N人
   - 前端开发: M人
   - QA测试: K人
   - DevOps: 1人
   - Product/Design: 1人

✅ 交付时间表已定
   - Phase 1: X周
   - Phase 2: Y周
   - Phase 3: Z周
   - 总时间: <24周 ✓

✅ 代码规范已共识
   - Linting rules已配置 (pylint/ruff)
   - Type hints要求: 100%覆盖
   - Test coverage要求: >80%
   - Code review checklist已准备

✅ 风险缓解计划已制定
   - 工具集成复杂性 → Phase 1用prototype验证
   - 权限检查性能 → Phase 2用基准测试验证
   - 审计链篡改防护 → Phase 3用密码学review
```

---

## 📞 遇到问题时

| 问题 | 联系人 | 是否需要重新评审 |
|------|--------|-----------------|
| 新的业务需求出现 | Product Manager | 是 |
| Schema字段不够 | 技术Lead + PM | 是 |
| 权限规则冲突 | RBAC Designer + 法务 | 是 |
| 工具执行超时 | 后端Lead | 否 (优化即可) |
| 测试覆盖不足 | QA Lead | 否 (补充测试) |

---

## 📎 附录: 常见问题解答 (FAQ)

**Q: 为什么需要3个多月完成这个项目?**
A: 
- 设计P0问题 (权限、审计) 不能跳过，否则后期无法修复
- 工具迁移 (7个工具从混合状态拆分) 需要仔细测试
- 权限检查贯穿全系统，每个endpoint都要经过review
- 审计系统requires密码学验证，测试必须充分

**Q: 能否先开发前端，后端慢慢跟?**
A: 不建议。因为:
- 前端表单依赖schemas (input_schema需要稳定)
- 权限逻辑在后端实现，不能并行
- 建议: 后端schema定义完 → 前端根据schema自动生成 → 并行开发

**Q: 审计日志的链签名真的必要吗?**
A: 
- 对于普通应用: 可选
- 对于involving user financial data + rule versioning的应用: 必要
- 因为用户未来可能会说"你2年前告诉我的建议是错的，是基于什么规则?"
- 链签名让我们能证明"这是当时的rule version, 现在的rule已更新"

**Q: 如何评估实际完成时间?**
A:
- 用历史sprint velocity推算
- 建议: Week 1用3个故事作为calibration
- 如果完成度<60%, 需要调整范围
- 每周五进行retrospective，调整下周计划

