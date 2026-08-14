"""Tekstlag-deteksjon og -uttrekk (Fase 3-forgrening).

Innkjøpte PDF-er har ofte et ekte tekstlag. Da kan sangteksten hentes ut med
eksakt posisjon rett fra PDF-en – helt uten OCR og uten gjenkjenningsfeil.
Skannede papirkopier er rene bilder uten tekstlag og må gå via OCR/vision.

Denne modulen skiller de to tilfellene og gir posisjonert tekst når den finnes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pymupdf as fitz  # PyMuPDF (fitz er det gamle modulnavnet)

from choir_rehearsal.config import TEXT_LAYER_MIN_CHARS


@dataclass(frozen=True)
class TextSpan:
    """Et sammenhengende tekststykke med posisjon på siden.

    Koordinatene er i PDF-punkter (origo øverst til venstre), slik PyMuPDF gir dem.
    ``x0, y0`` er øvre venstre hjørne; ``x1, y1`` er nedre høyre.
    """

    text: str
    x0: float
    y0: float
    x1: float
    y1: float
    page_index: int


def _page_text_char_count(page: fitz.Page) -> int:
    return len(page.get_text("text").strip())


def has_text_layer(
    pdf_path: str | Path,
    *,
    min_chars: int = TEXT_LAYER_MIN_CHARS,
) -> bool:
    """Returner ``True`` hvis minst én side har et brukbart tekstlag.

    Brukes tidlig i pipelinen til å velge mellom direkte tekstuttrekk (innkjøpt PDF)
    og OCR/vision (skannet PDF).
    """
    with fitz.open(pdf_path) as doc:
        for page in doc:
            if _page_text_char_count(page) >= min_chars:
                return True
    return False


def page_has_text_layer(
    pdf_path: str | Path,
    page_index: int,
    *,
    min_chars: int = TEXT_LAYER_MIN_CHARS,
) -> bool:
    """Som :func:`has_text_layer`, men for én bestemt side."""
    with fitz.open(pdf_path) as doc:
        if not 0 <= page_index < doc.page_count:
            raise IndexError(
                f"Side {page_index} finnes ikke (dokumentet har {doc.page_count} sider)"
            )
        return _page_text_char_count(doc.load_page(page_index)) >= min_chars


def extract_text_spans(pdf_path: str | Path, page_index: int) -> list[TextSpan]:
    """Trekk ut posisjonert tekst fra én side.

    Returnerer en tom liste for sider uten tekstlag (skannede bilder).
    Resultatet er råmateriale for sangtekst-koblingen i Fase 3: hver span kan
    knyttes til nærmeste note ut fra x-posisjon per stavesystem.
    """
    spans: list[TextSpan] = []
    with fitz.open(pdf_path) as doc:
        if not 0 <= page_index < doc.page_count:
            raise IndexError(
                f"Side {page_index} finnes ikke (dokumentet har {doc.page_count} sider)"
            )
        page = doc.load_page(page_index)
        data = page.get_text("dict")
        for block in data.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "")
                    if not text.strip():
                        continue
                    x0, y0, x1, y1 = span["bbox"]
                    spans.append(
                        TextSpan(
                            text=text,
                            x0=x0,
                            y0=y0,
                            x1=x1,
                            y1=y1,
                            page_index=page_index,
                        )
                    )
    return spans
