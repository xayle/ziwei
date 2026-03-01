"""
scripts/seed_data.py — BaZi API v7.0 数据种子脚本 (M0 任务 0.35)

功能:
  1. 创建默认管理员账号（admin / BaZi@2025!）
  2. 导入 8 个 Golden Test 命理案例
  3. 幂等操作（重复运行无副作用）

用法:
  python scripts/seed_data.py
  python scripts/seed_data.py --dry-run   （只显示计划，不写入）
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# 保证项目根目录在 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session, select

from db import get_engine
from app.models import User, Case
from services.auth_service import hash_password


# ── 管理员账号 ─────────────────────────────────────────────────────────────────
ADMIN_CONFIG = {
    "username": "admin",
    "email": "admin@bazi.local",
    "password": "BaZi@2025!",
    "role": "admin",
    "is_admin": True,
    "is_active": True,
}

# ── 8 个 Golden Test 命理案例 ────────────────────────────────────────────────
# 案例来自项目第七章 Golden Test 规格
GOLDEN_CASES = [
    {
        "title": "Golden Test #1 — 甲子年立春前男命",
        "description": "四柱验证标准案例：阳年男顺大运，日主甲木",
        "birth_datetime": "1984-02-04T08:30:00",
        "timezone": "Asia/Shanghai",
        "longitude": 116.41,
        "gender": "male",
        "mode": "dual",
        "solar_time_enabled": False,
        "tags": ["golden_test", "dayun_forward"],
    },
    {
        "title": "Golden Test #2 — 乙丑年男命逆大运",
        "description": "阴年男逆大运验证案例",
        "birth_datetime": "1985-03-15T14:20:00",
        "timezone": "Asia/Shanghai",
        "longitude": 116.41,
        "gender": "male",
        "mode": "dual",
        "solar_time_enabled": False,
        "tags": ["golden_test", "dayun_reverse"],
    },
    {
        "title": "Golden Test #3 — 甲子年女命逆大运",
        "description": "阳年女逆大运验证案例",
        "birth_datetime": "1984-06-20T10:15:00",
        "timezone": "Asia/Shanghai",
        "longitude": 116.41,
        "gender": "female",
        "mode": "dual",
        "solar_time_enabled": False,
        "tags": ["golden_test", "female_dayun_reverse"],
    },
    {
        "title": "Golden Test #4 — 乙丑年女命顺大运",
        "description": "阴年女顺大运验证案例",
        "birth_datetime": "1985-09-10T18:45:00",
        "timezone": "Asia/Shanghai",
        "longitude": 116.41,
        "gender": "female",
        "mode": "dual",
        "solar_time_enabled": False,
        "tags": ["golden_test", "female_dayun_forward"],
    },
    {
        "title": "Golden Test #5 — 早子时 23:00",
        "description": "子时早段（23:00）时柱判断验证",
        "birth_datetime": "1990-05-15T23:00:00",
        "timezone": "Asia/Shanghai",
        "longitude": 116.41,
        "gender": "male",
        "mode": "dual",
        "solar_time_enabled": False,
        "tags": ["golden_test", "zishi_early", "23:00"],
    },
    {
        "title": "Golden Test #6 — 早子时 23:30",
        "description": "子时早段（23:30）时柱判断验证",
        "birth_datetime": "1990-05-15T23:30:00",
        "timezone": "Asia/Shanghai",
        "longitude": 116.41,
        "gender": "male",
        "mode": "dual",
        "solar_time_enabled": False,
        "tags": ["golden_test", "zishi_early", "23:30"],
    },
    {
        "title": "Golden Test #7 — 真太阳时修正 +8 验证",
        "description": "经度差对真太阳时影响验证（東经130°）",
        "birth_datetime": "1992-08-08T12:00:00",
        "timezone": "Asia/Shanghai",
        "longitude": 130.0,
        "gender": "male",
        "mode": "dual",
        "solar_time_enabled": True,
        "tags": ["golden_test", "solar_time"],
    },
    {
        "title": "Golden Test #8 — 节气边界验证",
        "description": "出生时间近节气交接时刻，L 级别判定验证",
        "birth_datetime": "2000-02-04T20:29:00",
        "timezone": "Asia/Shanghai",
        "longitude": 116.41,
        "gender": "female",
        "mode": "dual",
        "solar_time_enabled": False,
        "tags": ["golden_test", "jieqi_boundary"],
    },
]


def seed_admin(session: Session, dry_run: bool = False) -> None:
    """创建/确保管理员账号（幂等）"""
    existing = session.exec(
        select(User).where(User.username == ADMIN_CONFIG["username"])
    ).first()
    if existing:
        print(f"  [SKIP] Admin user '{ADMIN_CONFIG['username']}' already exists")
        return
    if dry_run:
        print(f"  [DRY-RUN] Would create admin user '{ADMIN_CONFIG['username']}'")
        return
    admin = User(
        username=ADMIN_CONFIG["username"],
        email=ADMIN_CONFIG["email"],
        password_hash=hash_password(ADMIN_CONFIG["password"]),
        role=ADMIN_CONFIG["role"],
        is_admin=ADMIN_CONFIG["is_admin"],
        is_active=ADMIN_CONFIG["is_active"],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    session.add(admin)
    session.flush()
    print(f"  [CREATE] Admin user '{ADMIN_CONFIG['username']}' created (id={admin.id})")


def seed_golden_cases(session: Session, dry_run: bool = False) -> None:
    """导入 8 个 Golden Test 案例（幂等，按名称去重）"""
    for i, case_data in enumerate(GOLDEN_CASES, 1):
        name = case_data["title"]
        existing = session.exec(
            select(Case).where(Case.name == name)  # type: ignore[attr-defined]
        ).first()
        if existing:
            print(f"  [SKIP] Case #{i}: '{name}' already exists")
            continue
        if dry_run:
            print(f"  [DRY-RUN] Would create case #{i}: '{name}'")
            continue
        case = Case(
            name=name,
            notes=case_data.get("description", ""),
            birth_dt_local=case_data["birth_datetime"],
            tz=case_data["timezone"],
            lon=case_data["longitude"],
            gender=case_data["gender"],
            solar_time_enabled=case_data["solar_time_enabled"],
            tags=",".join(case_data.get("tags", [])),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(case)
        print(f"  [CREATE] Case #{i}: '{name}'")


def main(dry_run: bool = False) -> None:
    print(f"=== BaZi API v7.0 — 数据种子 {'(DRY-RUN)' if dry_run else ''} ===")
    with Session(get_engine()) as session:
        print("\n[1] 管理员账号:")
        seed_admin(session, dry_run)

        print("\n[2] Golden Test 案例:")
        try:
            seed_golden_cases(session, dry_run)
        except Exception as exc:
            print(f"  [WARN] Golden cases skipped: {exc}")

        if not dry_run:
            session.commit()
            print("\n✅ 种子数据写入完成")
        else:
            print("\n✅ Dry-run 完成（未写入任何数据）")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BaZi API 数据种子脚本")
    parser.add_argument("--dry-run", action="store_true", help="只显示计划，不写入")
    args = parser.parse_args()
    main(dry_run=args.dry_run)
