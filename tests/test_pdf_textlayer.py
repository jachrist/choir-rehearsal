"""Tester for tekstlag-forgreningen: innkjøpt (tekst) vs. skannet (bilde)."""

from __future__ import annotations

from pathlib import Path

import pytest

from choir_rehearsal.pdf import extract_text_spans, has_text_layer
from choir_rehearsal.pdf.textlayer import page_has_text_layer


def test_purchased_pdf_has_text_layer(text_pdf: Path):
    assert has_text_layer(text_pdf) is True


def test_scanned_pdf_has_no_text_layer(image_pdf: Path):
    assert has_text_layer(image_pdf) is False


def test_extract_spans_preserves_norwegian_chars(text_pdf: Path):
    spans = extract_text_spans(text_pdf, 0)
    joined = " ".join(s.text for s in spans)
    assert "Kjære" in joined
    assert "måne" in joined


def test_extracted_spans_have_positions(text_pdf: Path):
    spans = extract_text_spans(text_pdf, 0)
    assert spans, "forventet minst én span"
    first = spans[0]
    # Bounding-box skal være ikke-degenerert (bredde/høyde > 0)
    assert first.x1 > first.x0
    assert first.y1 > first.y0


def test_extract_spans_empty_for_scanned(image_pdf: Path):
    assert extract_text_spans(image_pdf, 0) == []


def test_page_level_detection(two_page_text_pdf: Path):
    assert page_has_text_layer(two_page_text_pdf, 0) is True
    assert page_has_text_layer(two_page_text_pdf, 1) is True


def test_page_out_of_range_raises(text_pdf: Path):
    with pytest.raises(IndexError):
        page_has_text_layer(text_pdf, 9)
