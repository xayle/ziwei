#!/usr/bin/env python3
"""Rasterize fusheng-mark.svg to PNG for favicon and legacy img tags."""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARK_SVG = ROOT / "frontend/src/assets/brand/fusheng-mark.svg"
OUT_BRAND = ROOT / "frontend/src/assets/brand/fusheng-logo.png"
OUT_PUBLIC = ROOT / "frontend/public/fusheng-logo.png"
STATIC_APP = ROOT / "static/app/fusheng-logo.png"


def _build_html(svg_text: str) -> str:
    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8"/>
<style>
  @font-face {{
    font-family: "LXGW Neo ZhiSong";
    src: url("file:///{ROOT.as_posix()}/frontend/public/fonts/LXGWNeoZhiSong-subset.woff2") format("woff2");
    font-display: swap;
  }}
  body {{ margin: 0; background: #f5f0e6; }}
  .wrap {{ width: 512px; height: 512px; display: flex; align-items: center; justify-content: center; }}
  svg {{ width: 480px; height: 480px; }}
</style>
</head><body><div class="wrap">{svg_text}</div></body></html>"""


def main() -> None:
    if not MARK_SVG.is_file():
        raise SystemExit(f"Missing {MARK_SVG}")

    svg_text = MARK_SVG.read_text(encoding="utf-8")
    html = _build_html(svg_text)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 512, "height": 512}, device_scale_factor=2)
        page.set_content(html, wait_until="networkidle")
        page.wait_for_timeout(400)
        png = page.locator("svg").screenshot(type="png", omit_background=False)
        browser.close()

    OUT_BRAND.write_bytes(png)
    shutil.copy2(OUT_BRAND, OUT_PUBLIC)
    if STATIC_APP.parent.is_dir():
        shutil.copy2(OUT_BRAND, STATIC_APP)
    print(f"Wrote {OUT_BRAND} ({len(png)} bytes)")
    print(f"Synced {OUT_PUBLIC}")


if __name__ == "__main__":
    main()
