"""PDF-inngang: rendring til bilde og tekstlag-deteksjon."""

from choir_rehearsal.pdf.render import render_page_to_png, render_pdf_to_pngs
from choir_rehearsal.pdf.textlayer import (
    TextSpan,
    extract_text_spans,
    has_text_layer,
)

__all__ = [
    "render_page_to_png",
    "render_pdf_to_pngs",
    "TextSpan",
    "extract_text_spans",
    "has_text_layer",
]
