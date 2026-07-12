from __future__ import annotations

from pathlib import Path

_static_dir = Path(__file__).resolve().parent.parent / "static"
_spa_index = _static_dir / "app" / "index.html"
_spa_main_entry = "/static/app/cases"


def spa_index_exists() -> bool:
    return _spa_index.exists()


def spa_entry_url() -> str:
    return _spa_main_entry


def legacy_page_path(name: str) -> Path:
    return _static_dir / f"{name}.html"


def legacy_page_url(name: str) -> str:
    return f"/static/{name}.html"


def resolve_page_url(name: str) -> str:
    if spa_index_exists():
        return f"/static/app/{name}"
    return legacy_page_url(name)
