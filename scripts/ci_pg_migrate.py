#!/usr/bin/env python3
"""CI helper: alembic upgrade head with full traceback → GitHub ::error."""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    os.environ.setdefault("SECRET_KEY", "ci-test-secret-key-at-least-32bytes-long")
    sys.path.insert(0, str(ROOT))

    url = os.environ.get("DATABASE_URL", "")
    host = url.split("@")[-1] if "@" in url else url or "(unset)"
    print(f"DATABASE_URL host={host}")

    try:
        import psycopg2

        # quick connectivity probe (strip sqlalchemy driver prefix)
        raw = url.replace("postgresql+psycopg2://", "postgresql://")
        conn = psycopg2.connect(raw)
        conn.close()
        print("psycopg2 connect: ok")
    except Exception as exc:
        print(f"::error title=Postgres connect::{exc}")
        traceback.print_exc()
        return 1

    try:
        from alembic import command
        from alembic.config import Config

        cfg = Config(str(ROOT / "alembic.ini"))
        command.upgrade(cfg, "head")
        print("alembic upgrade head: ok")
        return 0
    except Exception as exc:
        print(f"::error title=alembic upgrade head::{exc}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
