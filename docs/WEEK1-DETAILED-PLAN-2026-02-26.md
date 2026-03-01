# 📅 Week 1 详细执行计划 (Week 1 Detailed Execution Plan)

**开始日期**: 2026年2月26日 (周三)  
**结束日期**: 2026年3月2日 (周末)  
**关键里程碑**: 完成P0基础设施，打通完整流程  

---

## 🎯 Week 1目标

| 目标 | 状态 | 负责人 |
|-----|------|------|
| models.py: 新增6个表 | `TODO` | Backend Lead |
| run.py: 添加auth middleware + 权限decorator | `TODO` | Backend Lead |
| auth_service.py: 基础认证逻辑 | `TODO` | Backend Dev |
| 10个table-level unit tests | `TODO` | QA Lead |
| run_cases.py 全部通过 | `TODO` | QA Lead |
| 团队文档同步会 | `TODO` | PM |

---

## 📋 Day 1 (2月26日，周三)

### Morning (9:00-12:00): 团队Kickoff会议

**与会人员**: PM, Backend Lead, Frontend Lead, QA Lead, DevOps  
**时长**: 90分钟  
**地点**: [会议室]

**议程**:
```
1. (10分钟) 项目现状概述
   → 展示: CODE-REVIEW-2026-02-25.md 的关键数据
   → "设计100%完整，代码只有2%"
   
2. (15分钟) 40+个问题的快速review
   → 展示: 13个P0 + 28个extended issues
   → 强调: 没有"隐形炸弹"，所有问题都已记录
   
3. (20分钟) 关键7个决策的确认 ✅
   → 早子时规则: [确认: sxtwl行为优先]
   → 隐私模式: [确认: 诚实声明，不url存数据]
   → Timeline: [确认: 30周，不是20周]
   → MVP: [确认: A型(单用户快速)]
   → 引擎方式: [确认: sxtwl主+cnlunar备]
   → 编码: [确认: UTF-8 UnescapedJSON]
   → 监控: [后续周考虑]
   
4. (15分钟) Week 1 & Week 1-2的P0清单
   → models: 哪6个表，什么顺序
   → auth: middleware和permission体系
   → tests: 最少要通过哪些
   
5. (15分钟) Daily standup流程
   → 每天10:00的10分钟standup
   → Slack或面对面
   → 重点: blocker和dependency
   
6. (15分钟) Q&A和环境检查
   → 所有人本地都能跑run_cases.py吗
   → 有没有遗漏的setup步骤

**会议输出**:
- [ ] 签字：上述7个decision都确认✅
- [ ] 发送会议纪要到所有人
- [ ] 更新任务分配表

---

### Afternoon (14:00-18:00): 环境准备 & Backlog Refinement

**Backend Lead** (14:00-15:30):
- [ ] 拉最新代码，运行`pytest -q`确认所有test通过
- [ ] 运行`python run_cases.py`，验证20个样例
  - 如果有失败，立即debug（可能是sxtwl版本问题）
  - 输出样例到`docs/run_cases_output.txt`作为baseline
- [ ] 新建branch: `feat/week1-p0-database`
- [ ] 在models.py中列出TODO注释，标注6个新表的位置

**QA Lead** (14:00-15:00):
- [ ] 创建"Test Specification"文档
  - 10个table-level tests的expected behavior
  - 权限测试用例（403, 401等）
  - 参考: FINAL-ACCURACY-VALIDATION清单中的F部分
  
**Frontend Lead** (14:30-15:30):
- [ ] 确认verify.html是否需要改动（关于隐私声明）
- [ ] 新建feature branch: `feat/week1-privacy-statement`
- [ ] 准备更新隐私声明的PR

**PM** (14:00-18:00):
- [ ] 创建Jira/GitHub Issues，对应40+个问题
  - Label: `p0`, `p1`, `p2`
  - Status: `backlog`
  - Link: 对应CODE-REVIEW和ADDITIONAL-ISSUES的section
- [ ] 创建"Decision Record"文档，记录7个关键决策
  - 谁决策的（date, approver）
  - 为什么选这个（trade-off分析）
  - 后续review点（什么情况下要推翻这个决策）

---

### 日结 (17:30-18:00):

**全员Sync** (10分钟):
- [ ] 环境都OK吗
- [ ] 明天的工作分配清楚吗
- [ ] 有没有blocker

**Slack/Message汇总**:
```
✅ 会议确认: 7大决策通过
✅ 环境检查: run_cases.py通过
✅ 任务分配: 见下方Day 2-5的具体分工
⚠️ Blockers: [如果有]
```

---

## 📋 Day 2 (2月27日，周四)

### Morning (9:00-12:00): 数据库设计和实现第1阶段

**Backend Lead** (9:00-12:00): 
**任务**: 在models.py中实现6个新表

**表的优先级和复杂度**:
```
第一批 (简单，9:00-10:30):
  1. User (id, username, email, created_at)
     - 最简单，就几个字段
  2. AuditLog (id, user_id, action, timestamp, details)
     - 日志表，也比较简单

第二批 (中等，10:30-12:00):
  3. Member (id, owner_id, name, birth_date, gender, created_at)
     - 关键表，关键字段"birth_date"
  4. Event (id, owner_id, name, bazi_json, L_level, created_at)
     - 事件表，包含四柱JSON

第三批 (稍复杂，12:00后):
  5. Scenario (id, owner_id, name, base_event_id, variations, created_at)
     - 假设表，包含variations的结构化数据
  6. Delegation (id, from_member_id, to_member_id, permission, created_at)
     - 权限委托表，多对多关系
```

**Code Structure**:
```python
# models.py 新增内容示例：

# 🔵 当前已有:
# - Case (1)
# - Snapshot (2)

# 🟢 需要新增:
# 1. User
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True)
    password_hash: str  # bcrypt hash
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    members: List["Member"] = Relationship(back_populates="owner")
    events: List["Event"] = Relationship(back_populates="owner")

# 2. Member
class Member(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id")
    name: str
    birth_date: date  # 关键字段
    gender: str  # "M" or "F"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    owner: User = Relationship(back_populates="members")
    events: List["Event"] = Relationship(back_populates="member")

# 3. Event
class Event(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    owner_id: int = Field(foreign_key="user.id")
    member_id: int = Field(foreign_key="member.id")
    name: str
    bazi_json: str  # JSON string of complete result
    L_level: int  # 0, 1, 2, 3
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    owner: User = Relationship(back_populates="events")
    member: Member = Relationship(back_populates="events")

# ... 等等
```

**Checkpoint** (12:00):
- [ ] 6个表全部定义完毕
- [ ] 没有syntax error（用`python -m py_compile models.py`检查）
- [ ] 有comment说明每个表的用途

---

### Afternoon (14:00-18:00): 数据库迁移和初始化

**Backend Lead** (14:00-15:00):
- [ ] 运行`init_db()`确保所有表都被create
- [ ] 验证SQLite文件中真的有这6个新表
  ```bash
  sqlite3 db.sqlite3
  .tables  # 应该显示: user member event scenario delegation auditlog cases snapshot
  ```

**QA Lead** (14:00-16:00):
- [ ] 设计table-level test cases
  ```python
  # tests/test_models.py 的大纲
  
  def test_user_creation():
      """验证User表能创建记录"""
      pass
  
  def test_member_creation():
      """验证Member表能创建记录，关键是birth_date"""
      pass
  
  def test_event_creation():
      """验证Event表能存储完整的四柱JSON"""
      pass
  
  def test_foreign_key_constraints():
      """验证外键约束（删除owner时cascade delete）"""
      pass
  
  # ... 共10个tests
  ```

**Frontend Lead** (14:00-15:00):
- [ ] 在HTML footer中，更新隐私声明
  ```html
  <!-- 旧声明（删除）：
  本站不主动存储任何输入数据
  -->
  
  <!-- 新声明（添加）：-->
  <p>
    <strong>⚠️ 隐私声明</strong>: 
    此工具将您的生日通过URL参数传输。
    分享链接会在浏览器历史、ISP日志等多个位置保存生日信息。
    <strong>强烈建议仅与您完全信任的人分享</strong>。
    我们不对链接分享导致的信息泄露负责。
  </p>
  ```
- [ ] 提交PR到main分支

**DevOps** (14:00-15:30):
- [ ] 确保requirements.txt中的所有包都pinned到具体版本
  ```txt
  sxtwl==1.x.x  # 检查当前版本
  cnlunar==0.x.x  # 检查当前版本
  fastapi==0.x.x
  pydantic==2.x.x
  sqlalchemy==2.x.x
  pytest==7.x.x
  ```
- [ ] 创建`requirements-lock.txt`（完整的dependency tree）

---

### 日结 (17:30-18:00):

**Checkpoint**:
```
✅ models.py: 6个新表定义完毕
✅ 数据库: 所有表都创建成功
✅ 隐私声明: 已更新
✅ requirements: 已lockdown
⏳ Tests: 明天写
```

**Slack汇总**:
```
Day 2完成:
- models.py: 6个表 ✅
- 数据库初始化 ✅  
- 隐私声明更新 ✅
- 版本锁定 ✅

明天计划:
- Unit tests for models
- Auth middleware skeleton
```

---

## 📋 Day 3 (2月28日，周五)

### Morning (9:00-12:00): Auth Middleware & Permission System框架

**Backend Lead** (9:00-12:00):
**任务**: 在run.py中添加auth middleware和@require_permission decorator

**Code Structure**:
```python
# run.py 新增内容：

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthenticationCredentials
import jwt
from datetime import datetime, timedelta

# ========== 1. JWT配置 ==========
SECRET_KEY = "your-secret-key"  # 应该从env读取
ALGORITHM = "HS256"

# ========== 2. Middleware ==========
class AuthMiddleware:
    async def __call__(self, request: Request, call_next):
        authorization = request.headers.get("Authorization", "")
        
        if authorization.startswith("Bearer "):
            token = authorization[7:]
            try:
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                request.state.user_id = payload.get("user_id")
                request.state.username = payload.get("username")
            except jwt.InvalidTokenError:
                request.state.user_id = None
        else:
            request.state.user_id = None
        
        response = await call_next(request)
        return response

app.add_middleware(AuthMiddleware)

# ========== 3. Dependency ==========
async def get_current_user(request: Request) -> int:
    if request.state.user_id is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return request.state.user_id

# ========== 4. Permission Decorator ==========
def require_permission(permission: str):
    """Decorator to check user has permission"""
    async def verify_permission(user_id: int = Depends(get_current_user)):
        # 从数据库查询user是否有这个permission
        # 暂时: 所有登录用户都有所有权限（Week 2改进）
        return user_id
    
    return Depends(verify_permission)

# ========== 5. 修改现有endpoint ==========
@app.post("/api/v1/verify")
async def verify(
    req: VerifyRequest,
    user_id: int = require_permission("verify")  # 新增
):
    # ... 现有逻辑
    pass
```

**Checkpoint** (12:00):
- [ ] run.py能正常启动（`python -m uvicorn run:app`）
- [ ] /api/v1/verify 没有middleware报错
- [ ] test_payload.json的请求仍然能通过（auth暂时宽松）

---

### Afternoon (14:00-18:00): Unit Tests & Validation

**QA Lead** (14:00-17:00):
**任务**: 编写10个table-level unit tests

```python
# tests/test_models.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import SQLModel, User, Member, Event, AuditLog

# Fixture: 创建内存数据库用于测试
@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

# Test 1: User创建
def test_user_creation(test_db):
    user = User(username="alice", email="alice@example.com", password_hash="...")
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    
    assert user.id is not None
    assert user.username == "alice"

# Test 2: Member创建（关键：birth_date）
def test_member_creation(test_db):
    user = User(username="alice", email="alice@example.com", password_hash="...")
    test_db.add(user)
    test_db.commit()
    
    member = Member(
        owner_id=user.id,
        name="小王",
        birth_date="2000-01-01",
        gender="M"
    )
    test_db.add(member)
    test_db.commit()
    test_db.refresh(member)
    
    assert member.name == "小王"
    assert member.birth_date.year == 2000

# Test 3: Event创建（包含完整JSON）
def test_event_creation_with_bazi(test_db):
    # ... 创建user和member
    # ... 计算一个四柱结果
    bazi_json = json.dumps({
        "pillars_primary": {...},
        "L_level": 0,
        ...
    })
    
    event = Event(owner_id=user.id, member_id=member.id, bazi_json=bazi_json, L_level=0)
    test_db.add(event)
    test_db.commit()
    
    assert event.L_level == 0

# Test 4-10: ... 其他约束和关系测试
```

**运行tests**:
```bash
pytest tests/test_models.py -v
# 期望: 10个test都PASS ✅
```

---

### 日结 (17:30-18:00):

**Friday Wrap-up Meeting** (17:30, 15分钟全员):

```
✅ auth middleware: 框架完成
✅ @require_permission: decorator就绪  
✅ unit tests: 10/10 pass
✅ models: 6个表全部工作正常

Week 1成果:
- 数据库: 从2个表 → 8个表 (300%)
- 认证: 从0% → 50%框架完成
- 测试: 从4个文件 → 14个文件 (+ tables & auth)
- 隐私: 声明更诚实了

Week 2任务 (Preview):
- 完成auth_service.py (JWT签发、验证)
- 完成权限数据库模型 (UserRole, Permission)
- 实现member CRUD endpoints
- 实现event推荐逻辑 (待设计)
```

---

## 📋 Day 4-5 (周末): 可选Catch-up

**如果Day 1-3进展顺利** ✅:
- [ ] 可以提前开始Week 2的一些工作
- [ ] 或者补充missing测试用例

**如果Day 1-3有delay** ⚠️:
- [ ] 周末不加班
- [ ] 下周一继续，按原计划Week 2进行

---

## 🎯 Week 1必须完成的Deliverable清单

| 交付物 | Done? | 负责人 |
|-------|-------|-------|
| models.py: 6个新表 | ☐ | Backend Lead |
| 数据库初始化脚本 | ☐ | Backend Lead |
| run.py: auth middleware | ☐ | Backend Lead |
| @require_permission decorator | ☐ | Backend Lead |
| 隐私声明更新 | ☐ | Frontend Lead |
| 10个table-level tests | ☐ | QA Lead |
| run_cases.py全部通过 | ☐ | QA Lead |
| 决策记录文档 | ☐ | PM |
| Jira Issues创建 (40+) | ☐ | PM |
| requirements版本锁定 | ☐ | DevOps |

---

## 🚨 Week 1 Blocker清单

**如果发现以下任何一个问题，立即escalate到PM**:

1. **sxtwl导入失败**
   - 解决: 重装、检查版本兼容性
   - Fallback: 编写mock版本用于测试

2. **SQLite创建表失败**
   - 解决: 检查ForeignKey约束、数据类型
   - Fallback: 临时改用memory数据库测试逻辑

3. **auth middleware导致现有API失败**
   - 解决: 改middleware逻辑，确保backward compatible
   - Fallback: 第一周不加middleware，Week 2再加

4. **任何一个人的开发环境出问题**
   - 立即让DevOps支持（不能1个人卡住全队）

---

## 📞 Daily Standup Template

**每天10:00, 15分钟，可以是Slack/Zoom**

```
【参加人】Backend Lead, QA Lead, Frontend Lead, PM

【格式】每人简述:
  1️⃣ Yesterday: 昨天完成了什么
  2️⃣ Today: 今天计划做什么  
  3️⃣ Blocker: 有没有卡住的

【最后】
  PM更新"Day X进度表" (共5天)
```

**Example (Day 2 morning)**:
```
Backend Lead: 
  ✅ Yesterday: models.py - User & Member表完成
  📋 Today: Event & Scenario表，11点checkpoint
  🚨 Blocker: 需要确认ForeignKey的cascade规则

QA Lead:
  ✅ Yesterday: 设计了10个test cases
  📋 Today: 写test_models.py，下午提交PR
  (无blocker)

Frontend Lead:
  ✅ Yesterday: 审查了HTML，找到隐私声明位置
  📋 Today: 更新声明文本，提交PR
  ⚠️ Blocker: 需要legal review这份隐私声明措辞

PM:
  📊 更新进度: 40% Day 2 on track
  📌 记录: ForeignKey cascade是Backend Lead的Q，需要resolve
```

---

## 📊 Week 1进度追踪

**用这个表格追踪每天的情况**:

```
Day | models | auth | tests | other | Overall
----|--------|------|-------|-------|--------
  1 | 文档   | 计划 | 计划  | kickoff | 10%
  2 | 80%    | -    | -     | DB init | 35%
  3 | 100%   | 70%  | 70%   | -       | 65%
  4 | 100%   | 100% | 100%  | polish  | 95%
  5 | 100%   | 100% | 100%  | review  | 100%
```

PM在每天下午3点before standup更新这个表，并共享到Slack。

---

## ✅ Week 1成功标志

**如果达到以下目标，Week 1就是成功的**:

- ✅ 6个新表全部建成，没有schema error
- ✅ run_cases.py 20个样例全部通过
- ✅ 10个table-level tests全部PASS
- ✅ /api/v1/verify 仍然能工作（backward compatible）
- ✅ 隐私声明已更新为诚实版本
- ✅ 40+个issues已分好P0/P1/P2
- ✅ 团队对Week 2计划达成共识
- ✅ 没有人过度疲劳或burnout迹象

**如果有任何一个没达到** ❌:
- → 周末延续到下周一
- → PM调整Week 2计划，不加新任务

---

## 团队签字确认

```
我们同意上述Week 1计划，并承诺：
- 每天10:00 standup
- 遵守分配的任务
- Blocker立即escalate
- 质量不低于Code Review标准

后期签字确认：

[ ] Backend Lead: ________________  Date: _______
[ ] QA Lead:     ________________  Date: _______
[ ] Frontend Lead: ______________  Date: _______
[ ] DevOps:      ________________  Date: _______
[ ] PM:          ________________  Date: _______
```

---

**Let's go! 🚀**  
Week 1 Kick-off: 2026-02-26 09:00

