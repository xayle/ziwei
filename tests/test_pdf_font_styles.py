"""PDF font resolution for server-side HTML export."""

from __future__ import annotations

from services.pdf_font_styles import pdf_body_font_family, pdf_song_font_face_css, resolve_song_font_path


def test_pdf_font_helpers_do_not_crash():
    css = pdf_song_font_face_css()
    family = pdf_body_font_family()
    assert isinstance(css, str)
    assert "serif" in family


def test_pdf_font_face_when_file_present():
    path = resolve_song_font_path()
    if path is None:
        assert pdf_song_font_face_css() == ""
    else:
        assert "@font-face" in pdf_song_font_face_css()
        assert "FushengSong" in pdf_body_font_family()
