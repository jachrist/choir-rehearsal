"""Rendrer PDF-sider til rasterbilder (PNG) for OMR-steget (Fase 1).

Bygger på PyMuPDF (fitz). Ren, veletablert teknologi; jf. brief.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF

from choir_rehearsal.config import DEFAULT_DPI


def render_page_to_png(
    pdf_path: str | Path,
    page_index: int,
    out_path: str | Path,
    dpi: int = DEFAULT_DPI,
) -> Path:
    """Rendre én side i en PDF til en PNG-fil.

    Args:
        pdf_path: Sti til PDF-en.
        page_index: 0-indeksert sidenummer.
        out_path: Sti til PNG-filen som skrives.
        dpi: Oppløsning i punkter per tomme.

    Returns:
        Stien til den skrevne PNG-filen.

    Raises:
        IndexError: Hvis ``page_index`` er utenfor dokumentet.
    """
    out_path = Path(out_path)
    with fitz.open(pdf_path) as doc:
        if not 0 <= page_index < doc.page_count:
            raise IndexError(
                f"Side {page_index} finnes ikke (dokumentet har {doc.page_count} sider)"
            )
        page = doc.load_page(page_index)
        pix = page.get_pixmap(dpi=dpi)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pix.save(out_path)
    return out_path


def render_pdf_to_pngs(
    pdf_path: str | Path,
    out_dir: str | Path,
    dpi: int = DEFAULT_DPI,
) -> list[Path]:
    """Rendre alle sider i en PDF til PNG-filer i ``out_dir``.

    Filnavn: ``side-000.png``, ``side-001.png``, ...

    Returns:
        Liste med stier til de skrevne PNG-filene, i siderekkefølge.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with fitz.open(pdf_path) as doc:
        for i in range(doc.page_count):
            page = doc.load_page(i)
            pix = page.get_pixmap(dpi=dpi)
            target = out_dir / f"side-{i:03d}.png"
            pix.save(target)
            written.append(target)
    return written
