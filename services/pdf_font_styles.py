"""Shared PDF HTML font-face (R086 P1 · optional LXGW Neo ZhiSong)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_FONT_CANDIDATES = (
    ROOT / "frontend" / "public" / "fonts" / "LXGWNeoZhiSong-subset.woff2",
    ROOT / "static" / "app" / "fonts" / "LXGWNeoZhiSong-subset.woff2",
    ROOT / "data" / "fonts" / "LXGWNeoZhiSong-subset.woff2",
)

FONT_STACK = '"FushengSong", "LXGW Neo ZhiSong", "Noto Serif SC", "Source Han Serif SC", STSong, serif'


@lru_cache(maxsize=1)
def resolve_song_font_path() -> Path | None:
    for path in _FONT_CANDIDATES:
        if path.is_file():
            return path
    return None


def pdf_song_font_face_css() -> str:
    """Inject @font-face when local woff2 exists; otherwise rely on system serif stack."""
    font_path = resolve_song_font_path()
    if font_path is None:
        return ""
    uri = font_path.resolve().as_uri()
    return f"""
    @font-face {{
      font-family: "FushengSong";
      src: url("{uri}") format("woff2");
      font-weight: 400;
      font-style: normal;
      font-display: swap;
    }}
    """


def pdf_body_font_family() -> str:
    if resolve_song_font_path() is not None:
        return FONT_STACK
    return '"Noto Serif SC", "Source Han Serif SC", STSong, serif'
