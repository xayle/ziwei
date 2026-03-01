# 🗂️ 交付前设计文档总览

**生成日期**: 2026-02-25  
**项目**: BaZi 命理平台 (Phase 2: 家族管理 + 工具箱)  
**状态**: 📋 P0 文档已完成，等待评审 & 开发启动

---

## 🌐 静态 UI 导航（直连 FastAPI，无构建）
- 入口: http://127.0.0.1:8000/static/index.html
- verify.html: POST /api/v1/verify，展示 primary/secondary/diff/warnings
- bazi.html: POST /api/v1/bazi/full，支持 mode/solar_time_enabled/liunian_years
- cases.html: 案例列表与创建，卡片显示最新 verify 摘要 pill
- case.html?id=<case_id>: 案例详情+快照；计算区调用 /cases/{id}/compute（mode/solar/liunian，任务可选），展示 compute_batch_id/任务状态/新增快照；复制按钮已缩短文案并带 hover 提示
- ziwei.html: 占位页（未开放）
- 默认参数: mode=dual，solar_time_enabled=false，liunian_years=[-2,2]

---

## 📑 文档导航

### 1️⃣ [01-schemas.md](01-schemas.md) — 数据模型定义 ✅
**用途**: 后端架构的基础  
**读者**: 全职能 (Product, Backend Dev, Frontend Dev, QA)

**包含内容**:
- ✅ Member 完整Schema (成员信息档案)
- ✅ Event 完整Schema (发生/计划事件记录)
- ✅ Scenario 完整Schema (假如场景分析)
- ✅ ConfidenceModel (置信度模型)
- ✅ 跨模型ER图与外键约束
- ✅ 版本控制与变更日志格式

**关键决策已冻结**:
- Member.authorization.status 流程: PENDING → APPROVED
- Event.status 转移: 拟办 → 已发生/已取消/搁置 (单向)
- Scenario 原理: 基于Event的"假如"推演
- ConfidenceScore 计算: 多因子加权 (birth_precision[40%] + evidence[30%] + historical[30%])

**立即行动**:
- [ ] Backend Lead: 在 schemas.py 中实现所有Pydantic模型
- [ ] QA Lead: 准备schema validation测试用例
- [ ] Frontend Lead: 根据input_schema自动生成表单

---

### 2️⃣ [02-architecture.md](02-architecture.md) — 工具箱架构设计 ✅
**用途**: 解决"7个工具不统一"问题  
**读者**: 后端架构师、工具开发者

**包含内容**:
- ✅ 工具统一接口规范 (ToolBase + ToolMetadata)
- ✅ Plugin注册中心 (ToolRegistry)
- ✅ 具体实现示例 (DayunTool)
- ✅ API端点设计 (/api/v1/tools/*)
- ✅ 前端动态UI生成 (从schema自动生成表单)
- ✅ 迁移计划 (routers/compute.py → tools/*)

**架构核心**:
```
routers/tools.py 
    ↓
tools/registry.py (ToolRegistry)
    ↓
tools/dayun_tool.py, lunar_tool.py, ... (各工具独立)
    ↓
前端: tools.html 
(从ToolRegistry拉取全部工具元数据 → 动态生成UI)
```

**性能承诺**:
- 工具执行时间 < 2秒
- 工具列表加载 < 500ms

**立即行动**:
- [ ] Backend Lead: 创建 tools/base.py + tools/registry.py
- [ ] Frontend Lead: 创建 tools-manager.js (动态UI生成)
- [ ] 工具开发者: 按优先级逐个迁移 (DayunTool → lunar → wuxing → ...)

---

### 3️⃣ [03-rbac-audit.md](03-rbac-audit.md) — 权限 & 审计系统 ✅
**用途**: 保障数据安全与合规  
**读者**: 后端安全设计、QA、合规团队

**包含内容**:
- ✅ 5个核心角色 (ADMIN, OWNER, DELEGATE, FAMILY_MEMBER, GUEST)
- ✅ 权限矩阵 (Feature × Action × Role)
- ✅ 权限检查中间件实现 (@require_permission装饰器)
- ✅ 16种审计事件类型
- ✅ 审计日志schema + 敏感字段脱敏规则
- ✅ 链式签名验证 (防止事后篡改)

**权限检查的"七层防御"**:
1. 前端菜单级别 (UX友好，非安全边界)
2. API端点装饰器 (@require_permission)
3. 业务逻辑过滤 (filter_results_by_role)
4. 字段级脱敏 (敏感数据自动隐藏)
5. 审计日志记录 (每个操作都有记录)
6. 链式完整性验证 (检测篡改)
7. 定期合规报表 (每周生成)

**审计链工作原理**:
```
AuditLog #1: hash=abc123, sig=HMAC(genesis+abc123)
    ↓
AuditLog #2: hash=def456, sig=HMAC(abc123+def456)
    ↓
AuditLog #3: hash=ghi789, sig=HMAC(def456+ghi789)
    ↓
若某条被篡改: 其sig会失效 ✗ 检测到！
```

**立即行动**:
- [ ] Backend Lead: 实现 AuthContext 类 + @require_permission装饰器
- [ ] Backend Lead: 创建 AuditLog 数据模型 + audit_repo DAO
- [ ] Backend Lead: 实现 AuditIntegrityService (链签名)
- [ ] QA: 准备权限穿透测试 (能否越级访问?)
- [ ] Compliance: 确认3年日志保留政策、脱敏规则

---

### 4️⃣ [04-implementation-checklist.md](04-implementation-checklist.md) — 开发前检查清单 ✅
**用途**: 确保所有P0问题已解决，代码可以开始  
**读者**: 项目经理、技术Lead、全职能

**包含内容**:
- ✅ 7个部分×60+个检查项
- ✅ 测试计划 (单元/集成/E2E/性能/安全)
- ✅ 部署清单 (环保配置/数据迁移/监控告警)
- ✅ 48小时行动计划
- ✅ Success Criteria (何时认为"完成")
- ✅ FAQ + 风险缓解

**Timeline概览**:
| Phase | 内容 | WeekN | 人力 | 风险 |
|-------|------|-------|------|------|
| P1 | Schema + 表结构 | 1-2 | 1 Backend | 低 |
| P2 | 权限 + 审计中间件 | 2-3 | 1 Backend | 中 |
| P3 | 业务API (Member/Event/Scenario) | 4-5 | 2 Backend | 中 |
| P4 | 工具箱架构 + 迁移 | 6-10 | 2 Backend + 1 Frontend | 高 |
| P5 | 前端UI (Dashboard + Member + Events) | 6-15 | 2 Frontend | 中 |
| P6 | 集成测试 + 部署 | 16-20 | 1 QA + 1 DevOps | 低 |

**总耗时**: ~20 weeks (不含上线后优化)

**立即行动** (今天):
- [ ] 项目经理: 组织架构评审会议 (讨论上表内容)
- [ ] 技术Lead: 分配每个module的owner
- [ ] 全职能: 认领检查清单里的任务

---

## 🎯 文档间的依赖关系

```
04-implementation-checklist.md (总协调者)
    ├─ 依赖 → 01-schemas.md (数据契约)
    │                    ├─ 告诉Frontend: input_schema是什么?
    │                    ├─ 告诉Backend: 需创建哪些表?
    │                    └─ 告诉QA: 需测试哪些validation?
    │
    ├─ 依赖 → 02-architecture.md (技术方案)
    │                    ├─ 告诉Backend: 如何设计工具插件?
    │                    ├─ 告诉Frontend: 如何自动生成工具表单?
    │                    └─ 告诉DevOps: 服务如何拆分部署?
    │
    └─ 依赖 → 03-rbac-audit.md (安全策略)
                        ├─ 告诉Backend: 是否有权创建Event?
                        ├─ 告诉Frontend: 隐藏哪些菜单?
                        ├─ 告诉QA: 如何测试权限?
                        └─ 告诉Compliance: 审计日志如何保存?
```

---

## ✅ 使用指南

### 场景1: "我是后端工程师，最近要写Event API"
1. 读完 [01-schemas.md](01-schemas.md) 的 Event章节
2. 在 schemas.py 中定义 EventModel (包含所有字段)
3. 创建 event_repository.py (CRUD操作)
4. 在 routers/bazi.py 中添加 POST /api/v1/events 端点
5. 添加 @require_permission("event", "create") 装饰器
6. 每次update时，在 AuditLog中记录操作
7. 查看 [03-rbac-audit.md](03-rbac-audit.md) 确认权限逻辑正确
8. 编写单元测试 (参考[04-implementation-checklist.md](04-implementation-checklist.md)的测试计划)

### 场景2: "我是前端工程师，要做工具箱页面"
1. 读完 [02-architecture.md](02-architecture.md) 的前端架构章节
2. 在 static/tools.html 中创建工具网格
3. 使用 tools-manager.js 的 renderFormFromSchema(schema) 方法
4. 调用 POST /api/v1/tools/dayun_overview/execute 执行工具
5. 根据output_schema的格式，renderResult()结果
6. 查看示例代码 ([02-architecture.md](02-architecture.md)的第4.2小节)

### 场景3: "我是QA，要测试权限系统"
1. 读 [03-rbac-audit.md](03-rbac-audit.md) 的权限矩阵部分
2. 创建测试用户: OWNER, DELEGATE, FAMILY_MEMBER, GUEST
3. 对每个权限矩阵格子写一个测试:
   - ✅ 允许操作 → assert响应200
   - ❌ 禁止操作 → assert响应403
4. 查看 [04-implementation-checklist.md](04-implementation-checklist.md) 的Part 5 (测试计划)
5. 运行审计链完整性验证 (参考03章的AuditIntegrityService)

### 场景4: "我是PM，要评估完成度"
1. 对照 [04-implementation-checklist.md](04-implementation-checklist.md) 的各个part
2. 每个part的完成度统计 (%)
3. 用Timeline表格追踪phase进度
4. 若发现新需求: 记录在[01-schemas.md](01-schemas.md)中作为v1.1

---

## 🚨 红旗项目 (高风险)

| 风险 | 类别 | 缓解方案 |
|------|------|--------|
| 工具集成复杂度高 | 技术 | Phase 1用1个简单工具(LunarTool)作prototype，验证架构可行 |
| 权限检查性能不足 | 性能 | Phase 2做基准测试，如果>100ms则加缓存 |
| 审计日志量巨大 | 存储 | 使用分表按日期 (audit_log_2026_02, audit_log_2026_03) |
| 用户对confidence不理解 | UX | Phase 1完成后做用户测试，调整展示方式 |
| 工具迁移产生bug | 质量 | 迁移时保留旧endpoint作并行验证，对比结果 |

---

## 📞 文档所有者 & 更新流程

| 文档 | Owner | 更新频率 | 联系方式 |
|------|-------|--------|---------|
| 01-schemas.md | Backend Lead | 需求变更时 | 项目Slack #backend |
| 02-architecture.md | 技术架构师 | 每个phase结束 | 项目Slack #architecture |
| 03-rbac-audit.md | 安全 & 合规 | 每季度审核 | 项目Slack #security |
| 04-implementation-checklist.md | 项目经理 | 每周更新 | 项目Slack #pm |

---

## 🗓️ 下一步 (立即行动)

### ✅ 今天 (2026-02-25)
- [ ] 将4份文档分享给全职能
- [ ] 组织1小时"架构评审"会议
  - 问题: 权限矩阵有遗漏吗?
  - 问题: 工具箱太复杂吗?
  - Decision: 是否冻结这些设计?

### ✅ 明天 (2026-02-26)
- [ ] Technical Lead创建git branch + 项目board
- [ ] 分配Sprint 1的故事 (Week 1-2)
- [ ] 发起code review process讨论
- [ ] 准备开发环境 (本地数据库)

### ✅ 本周五 (2026-02-28)
- [ ] Sprint 1规划完成 (Story size已估算)
- [ ] 开发环境可用 (所有人)
- [ ] 第一个PR已提交 (schema实现)

---

## 📚 相关文件

| 文件 | 位置 | 说明 |
|------|------|------|
| API文档 | docs/openapi.json | 自动生成，需更新 |
| 发布说明 | docs/release-notes/ | 记录每个version的change |
| 样本数据 | docs/samples/ | bazi_full.json等示例 |

---

## 版本控制

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-02-25 | 初始发布 (P0文档完成) |
| v1.1 | TBD | 架构评审反馈整合 |
| v1.2 | TBD | Phase 1完成后微调 |

---

**🎯 核心目标**: 通过这4份文档，**从模糊的需求 → 清晰的交付物**。  
开发过程中有疑问，**都能在这些文档中找到答案**。

**祝你们好运！** 🚀

