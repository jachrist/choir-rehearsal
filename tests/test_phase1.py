"""Tester for Fase 1-orkestreringen. Mocker homr-grensen slik at hele kjeden
(PDF → bilde → «homr» → validering → rapport) testes uten torch/homr."""

from __future__ import annotations

from pathlib import Path

from choir_rehearsal.pipeline import format_report, phase1, process_pdf

NORMAL = """<score-partwise version="4.0">
  <part-list><score-part id="P1"><part-name>Sopran</part-name></score-part></part-list>
  <part id="P1"><measure number="1">
    <note><pitch><step>C</step><octave>5</octave></pitch><duration>4</duration></note>
  </measure></part>
</score-partwise>"""

DIVISI = """<score-partwise version="4.0">
  <part-list><score-part id="P1"><part-name>Damer</part-name></score-part></part-list>
  <part id="P1"><measure number="1">
    <note><pitch><step>C</step><octave>5</octave></pitch><duration>4</duration><voice>1</voice></note>
    <note><pitch><step>A</step><octave>4</octave></pitch><duration>4</duration><voice>2</voice></note>
  </measure></part>
</score-partwise>"""

EMPTY = """<score-partwise version="4.0">
  <part-list><score-part id="P1"><part-name>Sopran</part-name></score-part></part-list>
  <part id="P1"><measure number="1"></measure></part>
</score-partwise>"""

INVALID = "<html><body>ikke noter</body></html>"


def _patch_homr(monkeypatch, xml_by_page: dict[int, str], default: str = NORMAL):
    """Erstatt run_homr med en variant som skriver crafted MusicXML per side."""

    def _fake(image_path, *, timeout=900, extra_args=None):
        image_path = Path(image_path)
        idx = int(image_path.stem.split("-")[1])
        out = image_path.with_suffix(".musicxml")
        out.write_text(xml_by_page.get(idx, default), encoding="utf-8")
        return out

    monkeypatch.setattr(phase1, "run_homr", _fake)


def test_process_pdf_happy_path(monkeypatch, two_page_text_pdf: Path, tmp_path: Path):
    _patch_homr(monkeypatch, {})
    result = process_pdf(two_page_text_pdf, tmp_path / "out", dpi=100)
    assert len(result.pages) == 2
    assert result.ok_pages == 2
    p0 = result.pages[0]
    assert p0.ok and p0.well_formed
    assert p0.parts == 1
    assert p0.notes == 1
    assert p0.error is None
    assert p0.musicxml_path is not None and p0.musicxml_path.exists()


def test_divisi_detection(monkeypatch, two_page_text_pdf: Path, tmp_path: Path):
    _patch_homr(monkeypatch, {0: DIVISI})
    result = process_pdf(two_page_text_pdf, tmp_path / "out", dpi=100)
    assert result.pages[0].voices == 2
    assert result.pages[0].has_divisi is True
    assert result.pages[1].has_divisi is False


def test_empty_page_flagged(monkeypatch, two_page_text_pdf: Path, tmp_path: Path):
    _patch_homr(monkeypatch, {0: EMPTY})
    result = process_pdf(two_page_text_pdf, tmp_path / "out", dpi=100)
    p0 = result.pages[0]
    assert p0.well_formed is True
    assert p0.notes == 0
    assert p0.looks_empty is True
    assert p0.ok is False


def test_invalid_musicxml_recorded_not_raised(monkeypatch, two_page_text_pdf: Path, tmp_path: Path):
    _patch_homr(monkeypatch, {0: INVALID})
    result = process_pdf(two_page_text_pdf, tmp_path / "out", dpi=100)
    p0 = result.pages[0]
    assert p0.well_formed is False
    assert p0.ok is False
    assert p0.error is not None


def test_homr_failure_on_one_page_does_not_stop_others(
    monkeypatch, two_page_text_pdf: Path, tmp_path: Path
):
    def _fake(image_path, *, timeout=900, extra_args=None):
        image_path = Path(image_path)
        idx = int(image_path.stem.split("-")[1])
        if idx == 0:
            raise RuntimeError("homr krasjet")
        out = image_path.with_suffix(".musicxml")
        out.write_text(NORMAL, encoding="utf-8")
        return out

    monkeypatch.setattr(phase1, "run_homr", _fake)
    result = process_pdf(two_page_text_pdf, tmp_path / "out", dpi=100)
    assert result.pages[0].error is not None
    assert "homr krasjet" in result.pages[0].error
    assert result.pages[1].ok is True
    assert result.ok_pages == 1


def test_pages_selection(monkeypatch, two_page_text_pdf: Path, tmp_path: Path):
    _patch_homr(monkeypatch, {})
    result = process_pdf(two_page_text_pdf, tmp_path / "out", dpi=100, pages=[1])
    assert len(result.pages) == 1
    assert result.pages[0].page_index == 1


def test_format_report_contains_key_fields(monkeypatch, two_page_text_pdf: Path, tmp_path: Path):
    _patch_homr(monkeypatch, {0: DIVISI, 1: EMPTY})
    result = process_pdf(two_page_text_pdf, tmp_path / "out", dpi=100)
    report = format_report(result)
    assert "Fase 1-rapport" in report
    assert "divisi" in report
    assert "tom" in report
