"""Write brand SVG assets with correct UTF-8."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "frontend/src/assets/brand"

MARK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" fill="none" role="img" aria-label="浮生">
  <path d="M 22 76 A 50 50 0 1 1 98 76" stroke="#b8894d" stroke-width="1.35" stroke-linecap="round"/>
  <line x1="60" y1="108" x2="60" y2="97" stroke="#8b3a2a" stroke-width="1.6" stroke-linecap="round"/>
  <text x="60" y="71" text-anchor="middle" font-family="'LXGW Neo ZhiSong', 'Noto Serif SC', 'STSong', 'SimSun', serif" font-size="36" font-weight="600" fill="#1a1410" letter-spacing="0.08em">浮生</text>
</svg>
"""

LOGO = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 72" fill="none" role="img" aria-label="浮生">
  <path d="M 12 50 A 28 28 0 1 1 60 50" stroke="#b8894d" stroke-width="1.1" stroke-linecap="round"/>
  <line x1="36" y1="66" x2="36" y2="60" stroke="#8b3a2a" stroke-width="1.3" stroke-linecap="round"/>
  <text x="36" y="44" text-anchor="middle" font-family="'LXGW Neo ZhiSong', 'Noto Serif SC', 'STSong', 'SimSun', serif" font-size="20" font-weight="600" fill="#1a1410" letter-spacing="0.06em">浮生</text>
  <text x="84" y="46" font-family="'LXGW Neo ZhiSong', 'Noto Serif SC', 'STSong', 'SimSun', serif" font-size="28" font-weight="600" fill="#1a1410" letter-spacing="0.14em">浮生</text>
  <text x="84" y="62" font-family="'LXGW Neo ZhiSong', 'Noto Serif SC', 'STSong', 'SimSun', serif" font-size="11" fill="#6b5d4f" letter-spacing="0.22em">人生六卷辑录</text>
</svg>
"""

if __name__ == "__main__":
    (BASE / "fusheng-mark.svg").write_text(MARK, encoding="utf-8")
    (BASE / "fusheng-logo.svg").write_text(LOGO, encoding="utf-8")
    print("OK")
