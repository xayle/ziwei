# 📋 关键决策记录 (Decision Record)

**记录日期**: 2026年2月25日  
**记录人**: PM & CTO  
**有效期**: 整个项目周期  

---

## 决策1: 早子时(子时)的日期切割规则

**决策内容**: 早子时(23:00-00:00)采用sxtwl的计算结果，不做额外判断

**决策依据**:
- sxtwl是项目选定的主引擎，需要完全信任其计算
- 如果发现sxtwl有问题，通过"双库对比"机制(cnlunar验证)达到告警
- 避免自己判断，降低维护复杂度

**选项对比**:
| 选项 | 做法 | 优点 | 缺点 |
|-----|------|------|------|
| A | 早子时用前一天干 | 符合民间习俗 | 和sxtwl可能不同 |
| B | 早子时用当天干 | 某些软件做法 | 和sxtwl可能不同 |
| **C** | **信任sxtwl** | **简单、与引擎一致** | **万一sxtwl错了...** |

**推翻条件**: 
- 如果发现sxtwl在早子时计算上有documented bug
- 且有学术论文证明sxtwl is wrong
- → 改为选项A或B，并发大版本号

**责任人**: Backend Lead  
**实现截止**: Day 1 kickoff时验证sxtwl行为

---

## 决策2: 隐私模型

**决策内容**: 采用"诚实模型" - URL包含生日，但明确告知用户风险

**决策依据**:
- 完全本地化(WebAssembly)工作量太大，不在MVP范围内
- 当前技术栈(FastAPI+HTML)决定了参数必须过URL/JSON
- 对用户诚实比隐瞒更有道德性和法律合规性

**隐私声明更新**:
```
从: "本站不主动存储任何输入数据"
到: "此工具将您的生日通过URL参数传输。
     分享链接会在浏览器历史、ISP日志等位置保存。
     仅与完全信任的人分享。"
```

**后续计划**:
- Week 4-5: 考虑加入localStorage(本地缓存)选项
- Week 8+: 如果有资源，做WebAssembly纯本地计算版本

**责任人**: Frontend Lead + Legal Review  
**实现截止**: Day 2下午(隐私声明更新)

---

## 决策3: 项目Timeline

**决策内容**: 确认30周的现实工期，不承诺20周

**决策依据**:
- 代码现状: 2% vs 设计: 100% = 98%缺口
- 40+个identified issues需要systematic addressing
- 包括: models(1w), auth(2w), 推荐系统(3w), 前端(4w), 测试(2w), 部署(1w) = 13w MVP
- 加上bug fix, doc, training = 30去的合理预估

**三层Timeline方案**:
```
A计划 (20周): 只做快速版
  - 单用户(不做Member/Event)
  - L0验证(不做推荐)
  - 测试覆盖50%
  - 不做文档
  → 风险: 技术债极高，难以维护

B计划 (25周): 折中版
  - 完整功能
  - 测试覆盖70%
  - 基础文档
  → 风险: 仍然紧张，容易加班

C计划 (30周): 完整版 ← 我们选这个
  - 完整功能 + 多用户 + 推荐
  - 测试覆盖80%+
  - 完整文档 + 部署指南
  → 可持续，质量保证
```

**推翻条件**:
- 如果CTO/CEO强制要求20周 → 需要削减功能范围(MVP A to focus only on L0)
- 如果资源增加(+50% headcount) → 可以压缩到25周

**责任人**: PM & CTO签字  
**实现截止**: Day 1 kickoff确认

---

## 决策4: MVP定义 (最小可行产品)

**决策内容**: MVP采用"单用户快速迭代模式" (MVP-A)

**决策依据**:
- 可以在2-3周内打通完整流程而不是4-5周
- 快速上线测试市场反馈
- 后续迭代很容易加入多用户

**MVP功能清单**:
```
✅ 包括的功能:
  - 单用户验证 (输入生日 → 输出八字)
  - 完整的四柱计算 (pillars_primary, pillars_hidden)
  - 十神判定
  - L0/L1/L2/L3等级
  - 双库对比(sxtwl vs cnlunar)

❌ MVP不包括:
  - 多用户登录/权限
  - 事件保存
  - 推荐系统
  - 审计日志
  - 家族管理
  - 工具聚合
```

**迭代计划**:
```
V1 (第3周): MVP - 单用户验证工具
V2 (第8周): + 多用户 + 事件保存
V3 (第15周): + 推荐系统
V4 (第22周): + 完整工具集
V5 (第30周): Production hardened
```

**推翻条件**:
- 如果stakeholder要求V1就有多用户 → 改为25周而非20周
- 如果要求V1就有推荐系统 → 改为30周而非20周

**责任人**: PM  
**实现截止**: Day 1 kickoff确认

---

## 决策5: 主引擎 + 备份引擎处理方式

**决策内容**: sxtwl为主、cnlunar为备，策略为"信息一致性检查"

**计算逻辑**:
```
Step 1: 用sxtwl计算四柱
Step 2: 用cnlunar验证同一时刻
Step 3: 如果结果一致 → L级别+1(更可信)
Step 4: 如果结果不同 → 标注warning，展示两个
Step 5: 十神/推荐全部基于sxtwl
```

**代码结构**:
```python
result = {
    "primary": sxtwl_result,
    "backup": cnlunar_result,  # 如果不同，显示
    "consistency": sxtwl_result == cnlunar_result,
    "L_level": base_level + (1 if consistency else 0),
    "warnings": ["双库有差异，请谨慎参考"]
}
```

**责任人**: Backend Lead  
**实现截止**: Day 2 (完成sxtwl/cnlunar的verify endpoint)

---

## 决策6: 中文字符编码

**决策内容**: 采用UTF-8 + UnescapedJSON方案

**技术规格**:
```
HTTP Response: 
  Content-Type: application/json; charset=utf-8
  
JSON格式:
  {
    "stem": "壬",           // UTF-8原始字符(不是\u...)
    "branch": "午",
    "ten_gods": ["正官", "正财"],
    ...
  }

框架:
  FastAPI + Pydantic v2 + UnescapedJSONResponse
```

**验证方法**:
```bash
curl -s http://localhost:8000/api/v1/verify | grep -o '"stem":"[^"]*"'
# 应该输出: "stem":"壬" (而不是 "stem":"\u58ec")
```

**推翻条件**:
- 如果某个浏览器/客户端不支持UTF-8 → fallback到\uXXXX格式(但需要client side转换)

**责任人**: Backend Lead  
**实现截止**: Day 2验证(run_cases.py必须全部通过)

---

## 决策7: 监控和告警框架

**决策内容**: MVP阶段采用"日志优先"策略，Week 2-3考虑监控

**实现思路**:
```
Phase 1 (Week 1): 
  ✅ 结构化日志(JSON LOGs)
  ✅ 保存到文件(logs/app.log)
  ✅ 简单的错误计数

Phase 2 (Week 2-3):
  - 加入ELK(Elasticsearch + Logstash + Kibana)
  - 或使用CloudWatch/Datadog等SaaS
  
Phase 3 (Week 4+):
  - 加入metrics (Prometheus)
  - 加入distributed tracing (Jaeger)
  - 建立SLA dashboard
```

**责任人**: DevOps  
**实现截止**: Phase 1 in Week 1, Phase 2 in Week 2-3

---

## 6个关键决策的最终确认

**确认时间**: 2026年2月26日 09:00  
**确认地点**: Team Kickoff Meeting  
**确认方式**: 口头 + 签字

```
决策1 - 早子时规则 (sxtwl优先)
  [ ] PM确认     签字: ________________  
  [ ] CTO确认    签字: ________________
  [ ] Backend负责人确认  签字: ________________

决策2 - 隐私模型 (诚实声明)
  [ ] PM确认     签字: ________________
  [ ] CTO确认    签字: ________________
  [ ] Legal确认  签字: ________________

决策3 - Timeline (30周)
  [ ] PM确认     签字: ________________
  [ ] CTO确认    签字: ________________
  [ ] CEO/Boss确认 签字: ________________

决策4 - MVP范围 (单用户快速)
  [ ] PM确认     签字: ________________
  [ ] Stakeholder确认 签字: ________________

决策5 - 引擎策略 (sxtwl主+cnlunar备)
  [ ] Backend确认    签字: ________________
  [ ] CTO确认        签字: ________________

决策6 - 编码方案 (UTF-8 + Unescaped)
  [ ] Backend确认    签字: ________________
  [ ] QA确认         签字: ________________

决策7 - 监控框架 (日志优先)
  [ ] DevOps确认     签字: ________________
  [ ] CTO确认        签字: ________________
```

---

## 后续Review点

**一周后(3月4日)**:
- [ ] Week 1的6个表是否真的创建成功
- [ ] run_cases.py是否100%通过
- [ ] 有无发现新的"隐形问题"需要回调决策

**一个月后(3月25日)**:
- [ ] MVP (V1)是否如期上线
- [ ] 用户反馈是否导致决策调整
- [ ] Timeline是否在track

**三个月后(5月25日)**:
- [ ] 是否发现某个早期决策是错的
- [ ] 是否需要做"architecture review"

---

**记录人**: _________________  
**记录日期**: 2026年2月25日  
**生效日期**: 2026年2月26日  
**最后更新**: ____________

