"""Delte fixtures: genererer små PDF-er og MusicXML i minnet, så testene ikke
krever innsjekkede binærfiler for grunnoppsettet."""

from __future__ import annotations

from pathlib import Path

import pymupdf as fitz  # PyMuPDF (fitz er det gamle modulnavnet)
import pytest


@pytest.fixture
def text_pdf(tmp_path: Path) -> Path:
    """En «innkjøpt» PDF med ekte tekstlag, inkl. norske tegn og en sangtekst-lignende linje."""
    path = tmp_path / "med-tekstlag.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Kjære vakre måne", fontsize=14)
    page.insert_text((72, 100), "syng en sang for oss", fontsize=14)
    doc.save(path)
    doc.close()
    return path


@pytest.fixture
def two_page_text_pdf(tmp_path: Path) -> Path:
    """To-siders PDF med tekstlag – for sidebasert rendring/uttrekk."""
    path = tmp_path / "to-sider.pdf"
    doc = fitz.open()
    for n in (1, 2):
        page = doc.new_page()
        page.insert_text((72, 72), f"Side {n} av partituret", fontsize=14)
        page.insert_text((72, 100), "med sangtekst på hver side", fontsize=14)
    doc.save(path)
    doc.close()
    return path


@pytest.fixture
def image_pdf(tmp_path: Path) -> Path:
    """En «skannet» PDF uten tekstlag – bare en tegnet figur, null tekst-tegn."""
    path = tmp_path / "uten-tekstlag.pdf"
    doc = fitz.open()
    page = doc.new_page()
    # Tegn et fylt rektangel; ingen tekst legges inn.
    page.draw_rect(fitz.Rect(72, 72, 300, 300), fill=(0, 0, 0))
    doc.save(path)
    doc.close()
    return path


VALID_MUSICXML = """<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="4.0">
  <part-list>
    <score-part id="P1"><part-name>Sopran</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <note><pitch><step>C</step><octave>5</octave></pitch><duration>4</duration></note>
    </measure>
    <measure number="2">
      <note><pitch><step>D</step><octave>5</octave></pitch><duration>4</duration></note>
    </measure>
  </part>
</score-partwise>
"""


@pytest.fixture
def valid_musicxml() -> str:
    return VALID_MUSICXML
