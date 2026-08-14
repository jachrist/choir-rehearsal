"""Tester for PDF → bilde-rendring (Fase 1-grunnlag)."""

from __future__ import annotations

from pathlib import Path

import pytest

from choir_rehearsal.pdf import render_page_to_png, render_pdf_to_pngs


def test_render_page_writes_png(text_pdf: Path, tmp_path: Path):
    out = tmp_path / "side.png"
    result = render_page_to_png(text_pdf, 0, out, dpi=150)
    assert result == out
    assert out.exists()
    assert out.stat().st_size > 0
    # PNG-magisk signatur
    assert out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_higher_dpi_gives_larger_image(text_pdf: Path, tmp_path: Path):
    low = render_page_to_png(text_pdf, 0, tmp_path / "low.png", dpi=72)
    high = render_page_to_png(text_pdf, 0, tmp_path / "high.png", dpi=300)
    assert high.stat().st_size > low.stat().st_size


def test_render_all_pages(two_page_text_pdf: Path, tmp_path: Path):
    out_dir = tmp_path / "sider"
    pages = render_pdf_to_pngs(two_page_text_pdf, out_dir, dpi=100)
    assert len(pages) == 2
    assert [p.name for p in pages] == ["side-000.png", "side-001.png"]
    assert all(p.exists() for p in pages)


def test_out_of_range_page_raises(text_pdf: Path, tmp_path: Path):
    with pytest.raises(IndexError):
        render_page_to_png(text_pdf, 5, tmp_path / "x.png")
