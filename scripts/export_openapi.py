#!/usr/bin/env python3
"""Export runtime OpenAPI schema to docs/openapi.json."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs" / "openapi.json"


def main() -> int:
    os.environ.setdefault("SECRET_KEY", "export-openapi-dev-key")
    sys.path.insert(0, str(ROOT))

    from run import app  # noqa: WPS433

    schema = app.openapi()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    path_count = len(schema.get("paths", {}))
    print(f"Wrote {OUTPUT} ({path_count} paths)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
