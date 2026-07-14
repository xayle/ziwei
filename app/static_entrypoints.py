from __future__ import annotations

from pathlib import Path

_static_dir = Path(__file__).resolve().parent.parent / "static"
_spa_index = _static_dir / "app" / "index.html"
_spa_main_entry = "/static/app/"


def spa_index_exists() -> bool:
    return _spa_index.exists()


def spa_entry_url() -> str:
    return _spa_main_entry


def legacy_page_path(name: str) -> Path:
    return _static_dir / f"{name}.html"


def legacy_page_url(name: str) -> str:
    return f"/static/{name}.html"


_SPA_PAGE_ALIASES = {
    "cases": "/static/app/",
    "bazi": "/static/app/new/bazi",
    "ziwei": "/static/app/new/ziwei",
    "admin": "/static/app/extensions",
}


def resolve_page_url(name: str) -> str:
    if spa_index_exists():
        return _SPA_PAGE_ALIASES.get(name, f"/static/app/{name}")
    return legacy_page_url(name)
