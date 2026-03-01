# 优化方案汇总 & 决策建议 (v1.0)

**生成日期**: 2026-02-25  
**对应user request**: "优化或者方案"

---

## 📊 3个优化方向决策表

### 1️⃣ 权限检查性能问题

**现状**: API每次调用都检查权限 + 过滤results，可能>1000ms

| 方案 | 实现成本 | 性能提升 | 维护难度 | 推荐程度 |
|------|--------|--------|--------|---------|
| **A (缓存)** | 低 | 99%<2ms ✓ | 低 | ⭐⭐⭐⭐ |
| **B (SQL)** | 中 | 95%<10ms | 中 | ⭐⭐⭐ |
| **C (两层)** | 中 | 97%<3ms | 中 | ⭐⭐⭐⭐⭐ **首选** |

**👉 建议采纳: 方案C (两层缓存)**
```
Layer 1 (快速路径): 
  resource_owner == user_id → 直接通过 (<1ms)

Layer 2 (缓存): 
  permission_cache.get_permission() → (<1ms, 99% hit rate)

Layer 3 (数据库):
  检查delegate/family关系 (~50ms, <1% case)
```

**立即行动**:
```python
# Week 2-3
- 创建 middleware/authorization_cached.py
- 全局permission_cache实例
- 所有@require_permission使用缓存
- 基准测试: 1000条results过滤 <5ms ✓
```

📄 详见: [OPTIMIZATION-1-permission-performance.md](OPTIMIZATION-1-permission-performance.md)

---

### 2️⃣ Event推荐理由生成

**问题**: system_recommendation.reasoning 由谁生成?

| 方案 | 是否可用 | 精准度 | 可维护性 | 成本 | 推荐程度 |
|------|--------|--------|---------|------|---------|
| **A (规则引擎)** | ✓ | 高 ✓ | 中 | 免费 | ⭐⭐⭐⭐ |
| **B (模板)** | ✓ | 中 | 低 | 免费 | ⭐⭐⭐ (MVP用) |
| **C (LLM)** | ✓ | 中 | 低 | $0.01/API | ⭐⭐ (风险高) |
| **Z (混合)** | ✓  | 高 | 中 | 免费+可选 | ⭐⭐⭐⭐⭐ **首选** |

**👉 建议采纳: 混合方案Z (分阶段)**

```
Phase 1 (Week 1): 用模板快速上线 ✓
  └─ 1天完成，获得用户反馈
  
Phase 2 (Week 3-4): 迁用规则引擎 ✓
  └─ 命理师编写50+规则, JSON格式
  └─ 替换硬编码模板，精准度提升
  
Phase 3+ (Month 2): 可选LLM
  └─ 用于非标准case
  └─ LLM生成 → 命理师审核 → 转为规则
```

**立即行动** (Week 1):
```python
# 快速实现模板方案B
RECOMMENDATION_TEMPLATES = {
    ("投资", "HIGH"): [
        {"reason": "大运与主星冲克，主财运不利", "recommendation": "建议推迟..."}
    ],
    # ... 其他 event_type × risk_level 组合
}

# Week 3后迁到规则引擎
class RuleEngineService:
    async def generate_recommendations(member, event) → dict
```

📄 详见: [OPTIMIZATION-2-event-recommendation.md](OPTIMIZATION-2-event-recommendation.md)

---

### 3️⃣ 数据模型调整

**问题**: 当前schema是否有冗余或遗漏?

**建议的4项调整**:

| 编号 | 调整 | 模型 | 优先级 | Impact |
|------|------|------|--------|--------|
| **A1** | 移除`is_time_uncertain`, 用`time_of_birth==null` | Member | P2 | 低 |
| **A2** | 添加`location_lat`, `location_tz_offset` | Member | P2 | 低 |
| **B1** | 表拆分: event主表 + details + impact + recommendations | Event | P2 | 中 |
| **C1** | 添加`scenario_type`, 明确timeline计算 | Scenario | P2 | 低 |

**👉 建议采纳: 部分调整 (分优先级)**

```
Phase 1 (Week 1-2): 无需改 "Just works"
  │
Phase 2 (Week 3-5): 内部优化
  ├─ A1: Member字段精简 (5分钟)
  ├─ A2: 添加location_lat/tz_offset (10分钟)
  └─ C1: Scenario字段标准化 (1小时)
  │
Phase 3+ (Week 6-10): 表拆分 (可选)
  └─ B1: Event表拆分成5个表 (高回报但需谨慎迁移)
```

**立即行动** (Week 2-3):
```python
# 简单调整 (无数据迁移)
# 1. Member.time_of_birth == null 表示不确定
#    (而不是is_time_uncertain字段)

# 2. Member新增字段 (向后兼容)
#    - location_lat: Optional[float]
#    - location_tz_offset: Optional[float]  
#    - is_lunar: bool = false

# 3. Scenario明确timeline语义
#    event_trigger_date = "2026-05-01"
#    impact_window:
#      start_months_after: 2  # 5月后的第2个月 = 7月
#      end_months_after: 12
```

📄 详见: [OPTIMIZATION-3-data-model.md](OPTIMIZATION-3-data-model.md)

---

## 🎯 综合时间表 & 优先级

### 建议的开发顺序

```
Week 1-2: Phase 1 (MVP Core)
  □ 后端: schemas.py + Event/Member/Scenario CRUD
  □ 前端: 表单UI (自动由input_schema生成)
  □ 推荐: 用方案B (模板) ← 简单
  │
Week 2-3: Phase 2 (权限+审计)
  □ 后端: @require_permission装饰器 + 缓存
  □ 后端: AuditLog记录系统
  □ 数据: Member/Scenario字段调整 A1, A2, C1 ← 低风险
  │
Week 4-5: Phase 3 (业务API)
  □ 后端: Event/Member/Scenario的查询优化
  □ 推荐: 迁到方案A (规则引擎) ← 精准
  │
Week 6-10: Phase 4 (工具箱)
  □ 后端: tools/base.py + registry
  □ 前端: tools.html + 动态表单生成
  □ 可选: Event表拆分B1 (高risk, 最后做)
  │
Week 11-20: Phase 5-6 (前端UI + 测试)
```

### 关键指标

| 阶段 | 时间 | 可交付物 | 风险 |
|------|------|--------|------|
| **P1** | Week 1-2 | Member/Event/Scenario CRUD | 低 |
| **P2** | Week 2-3 | 权限检查 + 审计日志 | 中 |
| **P3** | Week 4-5 | 规则引擎推荐 | 低 |
| **P4** | Week 6-10 | 工具箱统一 | 高 |
| **P5-6** | Week 11-20 | UI + 测试 | 中 |

---

## ⚠️ 风险提示

### 高风险项
1. **Event表拆分 (B1)**
   - 需要数据迁移脚本 + 回滚计划
   - 建议在已有数据量<1万时执行
   - **推荐**: 延后到Phase 3+ (先积累数据)

2. **规则引擎 (推荐方案A)**
   - 需要命理师编写规则库
   - 若规则不准导致用户投诉
   - **缓解**: Phase 1用模板过渡, 时间充足再迁

3. **权限检查缓存 (方案C)**
   - 权限变更后缓存需及时失效
   - 若失效时间过长可能用户看到过期权限
   - **缓解**: 设置较短TTL (5分钟) + 实时失效机制

### 中风险项
1. 推荐理由的"来源可追踪性" (rule_id/version)
   - 需要管理规则库版本
   - **缓解**: 使用git存储rules.json

2. Member字段扩展 (location_lat/tz_offset)
   - 需要前端支持经纬度输入/选择
   - **缓解**: 可用地图库 (OSM/Google Map API)

### 低风险项
- Scenario、Event简单字段调整
- 常量化confidence计算公式

---

## 📋 决策建议

### 推荐采纳的优化

| 优化 | 理由 | 优先级 | Timeline |
|------|------|--------|----------|
| ✅ 权限缓存 (方案C) | 性能提升10倍，维护简单 | P0 | Week 2-3 |
| ✅ 推荐混合方案 (Z) | Phase 1快速上线，Phase 2可升级 | P1 | Week 1-4 |
| ✅ Member字段调整 | 无数据迁移，逻辑更清晰 | P2 | Week 2-3 |
| ⚠️ Scenario标准化 | 低成本，推荐采纳 | P2 | Week 2-3 |
| 🚫 Event表拆分 | 高风险，建议延后 | P3+ | Week 6+ |

### 不推荐的优化

| 优化 | 原因 |
|------|------|
| 🚫 LLM推荐方案 | 成本高 + 可信度低 + 需人工审核 |
| 🚫 Event表拆分Phase 1 | 数据敏感，需充分测试 |
| 🚫 SQL层权限过滤 | 维护成本高，缓存方案已足够 |

---

## ✅ 立即行动清单

### 项目 Leader (今天)

- [ ] 审阅3份优化文档
- [ ] 决策: 采纳/调整/拒绝各方案
- [ ] 更新project timeline (如需调整)
- [ ] 分配模块owner

### 后端 Lead (明天)

```python
# Week 2-3优先实现
- [ ] middleware/authorization_cached.py (权限缓存)
- [ ] services/recommendation_templates.py (模板推荐)
- [ ] 测试: 权限检查性能 <5ms
- [ ] 测试: 推荐生成 <100ms
```

### 前端 Lead (明天)

```javascript
// Week 2开始
- [ ] 整理input_schema → JSON Schema标准格式
- [ ] 动态表单生成器 (支持text/datetime/select/number)
- [ ] 测试: 表单加载 <200ms
```

---

## 📞 Questions & Answers

**Q: 能不能一开始就用最优化的设计?**  
A: 不建议。MVP阶段追求"快速验证 → 对";优化阶段最小化风险。推荐: Phase 1简单 + Phase 2优化。

**Q: 权限缓存5分钟TTL会不会太长?**  
A: 实际上很少有用户权限在5分钟内发生变化。可设置: 新增DELEGATE时立即失效 + TTL=5min。

**Q: 为什么推荐延后Event表拆分?**  
A: (1) 数据量小时改动风险低; (2) MVP验证产市场匹配度后再优化; (3) 现在表还不太大，性能问题不严重。

**Q: 规则库该放在数据库还是JSON文件?**  
A: **建议**: JSON文件 + git版本管理 (rules/ 目录)。原因: 规则变更频繁，需要审计trail和版本控制。

**Q: 模板方案会不会显得生硬?**  
A: 是的。但MVP阶段用户反馈比完美度更重要。Phase 2迁到规则引擎时会大幅提升质量。

---

## 📚 文档导航

| 文档 | 何时阅读 | 用途 |
|------|--------|------|
| [01-schemas.md](01-schemas.md) | 开发前 | 数据结构定义 |
| [OPTIMIZATION-1-permission-performance.md](OPTIMIZATION-1-permission-performance.md) | 权限层开发时 | 实现参考 |
| [OPTIMIZATION-2-event-recommendation.md](OPTIMIZATION-2-event-recommendation.md) | 推荐层开发时 | 算法选择 |
| [OPTIMIZATION-3-data-model.md](OPTIMIZATION-3-data-model.md) | Phase 2规划时 | 迁移指南 |
| [04-implementation-checklist.md](04-implementation-checklist.md) | 每周 | 进度跟踪 |

---

## 🎯 Success Metrics

开发完成时，验收以下指标：

```
✅ 权限检查延迟 < 5ms (99% case)
✅ 推荐生成延迟 < 200ms
✅ Member/Event/Scenario CRUD 功能完整
✅ 审计日志完整记录所有操作
✅ 单元测试覆盖率 > 80%
✅ 权限穿透测试: 0个漏洞
```

---

**综合建议**: 采纳所有3个优化方向，按推荐时间表执行。总体工作量 **增加10-15%**，但整体质量提升 **30-40%**。值得! ✓

