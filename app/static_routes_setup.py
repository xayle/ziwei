from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles


def configure_static_routes(app: FastAPI) -> None:
    _static_dir = Path(__file__).resolve().parent.parent / "static"
    _spa_index = _static_dir / "app" / "index.html"
    _spa_main_entry = "/static/app/cases"

    @app.get("/app", include_in_schema=False)
    @app.get("/app/{path:path}", include_in_schema=False)
    def spa_fallback(path: str = ""):
        if _spa_index.exists():
            return FileResponse(str(_spa_index), media_type="text/html")
        raise HTTPException(status_code=404, detail="SPA not built. Run: cd frontend && npm run build")

    @app.get("/static/app", include_in_schema=False)
    @app.get("/static/app/", include_in_schema=False)
    @app.get("/static/app/{path:path}", include_in_schema=False)
    def static_app_spa_fallback(path: str = ""):
        if _spa_index.exists():
            return FileResponse(str(_spa_index), media_type="text/html")
        raise HTTPException(status_code=404, detail="SPA not built. Run: cd frontend && npm run build")

    if _static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(_static_dir), html=True), name="static")

    @app.get("/favicon.ico")
    def favicon():
        icon = _static_dir / "favicon.ico"
        if icon.exists():
            return FileResponse(icon, media_type="image/x-icon")
        raise HTTPException(status_code=404, detail="favicon not found")

    @app.get("/")
    @app.get("/dashboard")
    def serve_dashboard():
        if _spa_index.exists():
            return RedirectResponse(url=_spa_main_entry, status_code=302)
        ziwei_page = _static_dir / "ziwei.html"
        if ziwei_page.exists():
            return FileResponse(ziwei_page, media_type="text/html")
        raise HTTPException(status_code=404, detail="SPA not found. Run: cd frontend && npm run build")

    @app.get("/verify")
    def serve_verify():
        if _spa_index.exists():
            return RedirectResponse(url=_spa_main_entry, status_code=301)

        ziwei_html = _static_dir / "ziwei.html"
        if ziwei_html.exists():
            return RedirectResponse(url="/static/ziwei.html", status_code=301)

        raise HTTPException(status_code=404, detail="verify ui not found")

    @app.get("/bazi")
    def serve_bazi():
        if _spa_index.exists():
            return RedirectResponse(url="/static/app/bazi", status_code=301)

        bazi_html = _static_dir / "bazi.html"
        if bazi_html.exists():
            return RedirectResponse(url="/static/bazi.html", status_code=301)

        raise HTTPException(status_code=404, detail="bazi ui not found")

    @app.get("/admin")
    def serve_admin():
        if _spa_index.exists():
            return RedirectResponse(url="/static/app/admin", status_code=301)

        admin_html = _static_dir / "admin.html"
        if admin_html.exists():
            return RedirectResponse(url="/static/admin.html", status_code=301)

        raise HTTPException(status_code=404, detail="admin ui not found")
