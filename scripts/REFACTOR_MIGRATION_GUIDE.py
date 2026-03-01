"""
第一周重构 - 自动化迁移脚本
用来帮助自动更新导入语句和代码重复清理
"""
import os
import re
from pathlib import Path

# 需要更新导入的文件映射
FILES_TO_UPDATE = {
    # 主文件
    "run.py": {
        "old_imports": [
            ("from schemas import", "from app.schemas import"),
            ("from models import", "from app.models import"),
            ("from config import settings", "from app.config import settings"),
        ],
        "description": "主 FastAPI 应用启动文件"
    },
    "db.py": {
        "old_imports": [
            ("from config import settings", "from app.config import settings"),
            ("import models as _models", "from app import models as _models"),
        ],
        "description": "数据库连接配置"
    },
    "routers/cases.py": {
        "old_imports": [
            ("from models import", "from app.models import"),
            ("from schemas import", "from app.schemas import"),
            # 移除冗余的 get_current_user，改用共享的
            ("def get_current_user", "# REMOVE THIS FUNCTION - use shared from app.dependencies"),
        ],
        "requires_cleanup": True,
        "description": "Cases 路由"
    },
    "routers/members.py": {
        "old_imports": [
            ("from models import", "from app.models import"),
            # 移除冗余的 get_current_user
            ("def get_current_user", "# REMOVE THIS FUNCTION - use shared from app.dependencies"),
        ],
        "requires_cleanup": True,
        "description": "Members 路由"
    },
    "routers/events.py": {
        "old_imports": [
            ("from models import", "from app.models import"),
            # 移除冗余的 get_current_user
            ("def get_current_user", "# REMOVE THIS FUNCTION - use shared from app.dependencies"),
        ],
        "requires_cleanup": True,
        "description": "Events 路由"
    },
    "routers/auth.py": {
        "old_imports": [
            ("from models import", "from app.models import"),
            ("from schemas import", "from app.schemas import"),
        ],
        "description": "Auth 路由"
    },
    "routers/bazi.py": {
        "old_imports": [
            ("from models import", "from app.models import"),
            ("from schemas import", "from app.schemas import"),
        ],
        "description": "BaZi 路由"
    },
    "routers/delegation.py": {
        "old_imports": [
            ("from models import", "from app.models import"),
            ("from schemas import", "from app.schemas import"),
        ],
        "description": "Delegation 路由"
    },
    "routers/scenarios.py": {
        "old_imports": [
            ("from models import", "from app.models import"),
            ("from schemas import", "from app.schemas import"),
        ],
        "description": "Scenarios 路由"
    },
    "routers/snapshots.py": {
        "old_imports": [
            ("from models import", "from app.models import"),
            ("from schemas import", "from app.schemas import"),
        ],
        "description": "Snapshots 路由"
    },
    "routers/compute.py": {
        "old_imports": [
            ("from models import", "from app.models import"),
            ("from schemas import", "from app.schemas import"),
        ],
        "description": "Compute 路由"
    },
    "routers/audit.py": {
        "old_imports": [
            ("from models import", "from app.models import"),
            ("from schemas import", "from app.schemas import"),
        ],
        "description": "Audit 路由"
    },
}

SHARED_DEPENDENCY_PATTERN = """
# ===== 统一使用共享的认证依赖 =====
from app.dependencies import require_user, RequiredUser
from fastapi import Depends
from app.models import User

# 而不是定义本地的 get_current_user
"""

def print_migration_instructions():
    """打印迁移说明"""
    print("=" * 80)
    print("第一周代码重构 - 迁移完成检查清单")
    print("=" * 80)
    print()
    print("✅ 已完成的工作：")
    print("  1. 创建 app/models/ 包，分离所有数据模型到各自文件")
    print("     - app/models/base.py (User, RefreshToken)")
    print("     - app/models/case.py (Case, Snapshot)")
    print("     - app/models/member.py (Member)")
    print("     - app/models/event.py (Event)")
    print("     - app/models/other.py (Scenario, Delegation, AuditLog)")
    print("     - app/models/__init__.py (集中导出)")
    print()
    print("  2. 创建 app/schemas/ 包，分离所有API schemas")
    print("     - app/schemas/common.py (WarningModel, RangeModel, BackendInfo)")
    print("     - app/schemas/bazi.py (所有八字相关 schema)")
    print("     - app/schemas/case.py (Case 相关 schema)")
    print("     - app/schemas/compute.py (计算相关 schema)")
    print("     - app/schemas/__init__.py (集中导出)")
    print()
    print("  3. 创建 app/dependencies/ 包（共享依赖注入）")
    print("     - app/dependencies/auth.py (get_current_user, require_user)")
    print("     - app/dependencies/__init__.py")
    print()
    print("  4. 创建增强的 app/config.py")
    print("     - 支持环境变量")
    print("     - 支持 .env 文件")
    print("     - 支持多环境配置（development, staging, production）")
    print()
    print("⏳ 需要手动完成的工作：")
    print()
    for file_path, config in FILES_TO_UPDATE.items():
        print(f"  📝 {file_path}")
        print(f"     {config['description']}")
        print(f"     需要更新导入：")
        for old, new in config['old_imports']:
            print(f"       - {old} → {new}")
        if config.get('requires_cleanup'):
            print(f"     ⚠️  需要移除冗余的 get_current_user() 函数")
        print()
    print()
    print("📋 迁移步骤：")
    print()
    print("第1步：更新所有导入语句")
    print("  • 使用编辑器全局查找替换:")
    print("    - 'from models import' → 'from app.models import'")
    print("    - 'from schemas import' → 'from app.schemas import'")
    print("    - 'from config import' → 'from app.config import'")
    print()
    print("第2步：在路由文件中移除冗余的认证函数")
    print("  • 替换为：")
    print(SHARED_DEPENDENCY_PATTERN)
    print()
    print("第3步：更新 run.py 的 CORS 配置")
    print("  • 使用 app.config.settings 中的 allowed_origins")
    print("  • 移除硬编码的本地 localhost 列表")
    print()
    print("第4步：创建 .env 文件")
    print("  • 复制 .env.example 为 .env")
    print("  • 根据你的环境修改配置")
    print()
    print("第5步：验证所有导入")
    print("  python -c \"from app.models import *; from app.schemas import *; print('✓ 所有导入成功')\"")
    print()
    print("=" * 80)

if __name__ == "__main__":
    print_migration_instructions()
