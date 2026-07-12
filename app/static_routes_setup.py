from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.static_entrypoints import (
    _spa_index,
    _static_dir,
    legacy_page_path,
    legacy_page_url,
    resolve_page_url,
    spa_entry_url,
    spa_index_exists,
)


class SafeStaticFiles(StaticFiles):
    """html=True 时缺失文件默认抛 RuntimeError；统一转为 404。"""

    async def get_response(self, path: str, scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except (RuntimeError, FileNotFoundError) as exc:
            if isinstance(exc, RuntimeError) and "does not exist" not in str(exc):
                raise
            raise StarletteHTTPException(status_code=404, detail="Not Found") from exc


def configure_static_routes(app: FastAPI) -> None:
    @app.get("/app", include_in_schema=False)
    @app.get("/app/{path:path}", include_in_schema=False)
    def spa_fallback(path: str = ""):
        if spa_index_exists():
            return FileResponse(str(_spa_index), media_type="text/html")
        raise HTTPException(status_code=404, detail="SPA not built. Run: cd frontend && npm run build")

    @app.get("/static/app", include_in_schema=False)
    @app.get("/static/app/", include_in_schema=False)
    @app.get("/static/app/{path:path}", include_in_schema=False)
    def static_app_spa_fallback(path: str = ""):
        app_root = _static_dir / "app"
        candidate = (app_root / Path(path)) if path else None
        if candidate and candidate.exists() and candidate.is_file():
            return FileResponse(candidate)
        if candidate and candidate.suffix:
            raise HTTPException(status_code=404, detail=f"Static asset not found: {path}")
        if spa_index_exists():
            return FileResponse(str(_spa_index), media_type="text/html")
        raise HTTPException(status_code=404, detail="SPA not built. Run: cd frontend && npm run build")

    if _static_dir.exists():
        app.mount("/static", SafeStaticFiles(directory=str(_static_dir), html=True), name="static")

    @app.get("/favicon.ico")
    def favicon():
        icon = _static_dir / "favicon.ico"
        if icon.exists():
            return FileResponse(icon, media_type="image/x-icon")
        raise HTTPException(status_code=404, detail="favicon not found")

    @app.get("/")
    @app.get("/dashboard")
    def serve_dashboard():
        if spa_index_exists():
            return RedirectResponse(url=spa_entry_url(), status_code=302)
        ziwei_page = legacy_page_path("ziwei")
        if ziwei_page.exists():
            return FileResponse(ziwei_page, media_type="text/html")
        raise HTTPException(status_code=404, detail="SPA not found. Run: cd frontend && npm run build")

    @app.get("/verify")
    def serve_verify():
        if spa_index_exists():
            return RedirectResponse(url=resolve_page_url("ziwei"), status_code=301)
        return RedirectResponse(url=legacy_page_url("ziwei"), status_code=301)

    @app.get("/new")
    @app.get("/new/{path:path}")
    def serve_new(path: str = ""):
        if spa_index_exists():
            target = f"/static/app/new{f'/{path}' if path else ''}"
            return RedirectResponse(url=target, status_code=302)
        return RedirectResponse(url=legacy_page_url("ziwei"), status_code=301)

    @app.get("/bazi")
    def serve_bazi():
        if spa_index_exists():
            return RedirectResponse(url=resolve_page_url("bazi"), status_code=301)
        return RedirectResponse(url=legacy_page_url("bazi"), status_code=301)

    @app.get("/ziwei")
    def serve_ziwei():
        if spa_index_exists():
            return RedirectResponse(url=resolve_page_url("ziwei"), status_code=301)
        return RedirectResponse(url=legacy_page_url("ziwei"), status_code=301)

    @app.get("/admin")
    def serve_admin():
        if spa_index_exists():
            return RedirectResponse(url=resolve_page_url("admin"), status_code=301)
        return RedirectResponse(url=legacy_page_url("admin"), status_code=301)
