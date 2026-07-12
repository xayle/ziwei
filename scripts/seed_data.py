#!/usr/bin/env python3
"""Seed local database: admin user + sample cases (BE-P3-08)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlmodel import Session, select

from app.config import settings
from app.models import Case, User
from db import get_engine, init_db
from services.auth_service import hash_password


def _ensure_admin(session: Session) -> User:
    existing = session.exec(select(User).where(User.username == "admin")).first()
    if existing:
        return existing
    user = User(
        username="admin",
        email="admin@local.dev",
        password_hash=hash_password("admin123!"),
        role="owner",
        is_admin=True,
        is_active=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _ensure_sample_cases(session: Session, owner_id: int) -> list[Case]:
    samples = [
        {
            "name": "样例·甲子日",
            "gender": "male",
            "birth_dt_local": "1984-02-15T08:30:00",
            "tz": "Asia/Shanghai",
            "lon": 121.47,
            "city": "上海",
        },
        {
            "name": "样例·紫微对照",
            "gender": "female",
            "birth_dt_local": "1990-06-21T14:00:00",
            "tz": "Asia/Shanghai",
            "lon": 116.41,
            "city": "北京",
        },
    ]
    created: list[Case] = []
    for spec in samples:
        hit = session.exec(select(Case).where(Case.name == spec["name"], Case.owner_id == owner_id)).first()
        if hit:
            created.append(hit)
            continue
        case = Case(owner_id=owner_id, **spec)
        session.add(case)
        session.commit()
        session.refresh(case)
        created.append(case)
    return created


def main() -> int:
    print(f"Seeding database: {settings.db_path}")
    init_db()
    engine = get_engine()
    with Session(engine) as session:
        admin = _ensure_admin(session)
        assert admin.id is not None
        cases = _ensure_sample_cases(session, admin.id)
        admin_name = admin.username
        admin_id = admin.id
        case_lines = [f"  - {c.id} {c.name}" for c in cases]
    print(f"admin: {admin_name} (id={admin_id})")
    print(f"sample_cases: {len(case_lines)}")
    for line in case_lines:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
