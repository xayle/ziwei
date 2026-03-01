# 快速启动指南 - Week 2+ 开发者

## 环境激活

```bash
# Windows PowerShell
& d:\Users\Administrator\Desktop\c1\.venv\Scripts\Activate.ps1

# 或者直接使用python路径
d:\Users\Administrator\Desktop\c1\.venv\Scripts\python.exe
```

## 启动API服务器

```bash
cd d:\Users\Administrator\Desktop\c1

# 方式1: 基础启动
d:/Users/Administrator/Desktop/c1/.venv/Scripts/python.exe -m uvicorn run:app --host 127.0.0.1 --port 8000

# 方式2: 带自动重载 (开发时)
d:/Users/Administrator/Desktop/c1/.venv/Scripts/python.exe -m uvicorn run:app --host 127.0.0.1 --port 8000 --reload

# 方式3: 访问Swagger文档
http://127.0.0.1:8000/docs
```

## 数据库操作

```bash
# 重新初始化数据库 (会删除所有数据)
python -c "from db import init_db; init_db()"

# 检查表结构
python -c "from sqlmodel import SQLModel; print([t.__tablename__ for t in SQLModel.registry.mappers[0].class_])"

# 查询用户
python -c "from sqlmodel import Session, select; from models import User; from db import get_engine; engine = get_engine(); with Session(engine) as s: print(s.exec(select(User)).all())"
```

## 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_models.py -v

# 运行特定测试
pytest tests/test_models.py::TestUserTable::test_user_creation -v

# 显示输出 (用于调试)
pytest tests/ -v -s

# 快速模式
pytest tests/ -q
```

## 常见任务

### 新增用户并获取Token

```bash
# 使用curl
curl -X POST "http://127.0.0.1:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"testpass123"}'

# 响应示例:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 用Token获取用户信息

```bash
# 替换YOUR_TOKEN为上面得到的token
curl -X GET "http://127.0.0.1:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 创建成员记录

```python
from sqlmodel import Session
from models import Member, User
from db import get_engine
from datetime import date

engine = get_engine()
with Session(engine) as session:
    # 先找到用户
    user = session.query(User).first()
    if user:
        # 创建成员
        member = Member(
            owner_id=user.id,
            name="John Doe",
            birth_date=date(1990, 5, 15),
            gender="M",
            birth_time_hour=9,
            birth_time_minute=30,
            birth_city="Beijing"
        )
        session.add(member)
        session.commit()
        print(f"Member created: {member.id}")
```

## 项目结构参考

```
d:\Users\Administrator\Desktop\c1\
├── models.py              # SQLModel表定义
├── db.py                  # 数据库连接和初始化
├── run.py                 # FastAPI应用入口
├── services/
│   ├── auth_service.py    # JWT和密码处理
│   ├── bazi_full_service.py
│   └── normalize_input.py
├── routers/
│   ├── auth.py            # 认证端点 (NEW in Week 1)
│   ├── bazi.py
│   ├── cases.py
│   ├── compute.py
│   └── snapshots.py
├── static/
│   └── verify.html        # 前端界面 (隐私声明已更新)
├── tests/
│   ├── test_models.py     # 数据库单元测试 (NEW in Week 1)
│   └── ... others
├── docs/
│   └── ... API文档等
├── .venv/                 # Python虚拟环境
├── requirements.txt
└── database.db            # SQLite数据库文件
```

## 关键环境变量

```bash
# 在run.py或环境中设置这些变量:

SECRET_KEY=dev-secret-key-change-in-production  # JWT密钥，生产版必须改
DATABASE_URL=sqlite:///./database.db             # 数据库URL (自动创建)
BASE_URL=http://127.0.0.1:8000                   # API基础URL
```

## Week 2+待办事项

根据WEEK1-SUMMARY-2026-02-26.md，Week 2的主要任务:

1. **权限管理系统** (RBAC)
   - [ ] 创建permission_service.py
   - [ ] 实现@require_permission装饰器
   - [ ] 成员间访问控制

2. **多用户集成测试**
   - [ ] 用户隔离测试
   - [ ] 权限委托测试
   - [ ] 成员访问模式测试

3. **安全改进**
   - [ ] 替换SHA256为argon2
   - [ ] 添加refresh token机制
   - [ ] 实现rate limiting

4. **文档完善**
   - [ ] API端点文档
   - [ ] 数据库模式文档
   - [ ] 部署检查清单

## 已知问题与注意事项

⚠️ **当前限制** (Week 1):
- 密码哈希使用SHA256 (计划Week 2升级到argon2)
- 没有refresh token (需要在Week 2添加)
- SQLModel ORM relationships未完全定义 (使用外键FK替代)
- FastAPI lifespan handlers使用已弃用语法

## 调试技巧

### 查看API错误日志
```bash
# 以详细输出运行API
python -m uvicorn run:app --host 127.0.0.1 --port 8000 --log-level debug
```

### 检查数据库连接
```python
from db import get_engine
engine = get_engine()
with engine.connect() as conn:
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    print([row[0] for row in result])
```

### 清空数据库日志
```bash
# 删除SQLite数据库文件强制重新初始化
remove-item database.db

# 然后运行
python -c "from db import init_db; init_db()"
```

## 性能监控 (Week 2+)

推荐逐步添加:
- [ ] 请求日志记录 (JSON formatted)
- [ ] 数据库查询计时
- [ ] API响应时间统计
- [ ] 错误率监控

## 联系方式

如有技术问题，参考:
1. WEEK1-SUMMARY-2026-02-26.md - Week 1完整总结
2. CODE-REVIEW-2026-02-25.md - 原始代码审查
3. DECISION-RECORD-2026-02-25.md - 技术决议历史

---

Generated: Week 1 End (2026-02-26)
Last Updated: Start of Week 2
Status: ✅ Ready for development
