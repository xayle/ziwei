"""T014 · Capture design target PNGs from skin-preview.html (Python playwright)."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SKIN = ROOT / "docs" / "design" / "skin-preview.html"
TARGETS = ROOT / "docs" / "design" / "targets"
URL_BASE = SKIN.as_uri()

SHOTS = [
    ("#layout-bazi", "bazi.png", 1120, 720),
    ("#layout-ziwei", "ziwei.png", 1120, 640),
    ("#volumes", "report-toc.png", 1120, 800),
]


def main() -> None:
    TARGETS.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for hash_id, filename, width, height in SHOTS:
            page.set_viewport_size({"width": width, "height": height})
            page.goto(URL_BASE + hash_id, wait_until="load")
            page.wait_for_timeout(400)
            el = page.locator(hash_id).first
            el.screenshot(path=str(TARGETS / filename))
            print("wrote", filename)
        browser.close()


if __name__ == "__main__":
    main()
