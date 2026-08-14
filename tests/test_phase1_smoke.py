"""Ekte ende-til-ende-røyktest for Fase 1 (treg, opt-in).

Denne kjører den *virkelige* homr-motoren og hoppes over med mindre:
  * homr faktisk er installert, og
  * det finnes minst én ekte PDF i ``testdata/pdf/``.

Slik kjører den aldri i vanlig, rask CI, men er tilgjengelig så snart dirigenten
legger inn ekte kornoter i testdata/. Kjør eksplisitt med:

    pytest -m slow

Dette er selve Fase 1-målingen: sammenlign den genererte MusicXML-en (og
kvalitetsrapporten) med kildesiden for å vurdere om homr er «godt nok til å rette».
"""

from __future__ import annotations

from pathlib import Path

import pytest

from choir_rehearsal.omr import homr_available
from choir_rehearsal.pipeline import format_report, process_pdf

TESTDATA_PDF_DIR = Path(__file__).parent.parent / "testdata" / "pdf"


def _real_pdfs() -> list[Path]:
    if not TESTDATA_PDF_DIR.is_dir():
        return []
    return sorted(TESTDATA_PDF_DIR.glob("*.pdf"))


pytestmark = pytest.mark.slow


@pytest.mark.skipif(not homr_available(), reason="homr er ikke installert")
def test_real_homr_on_testdata(tmp_path: Path):
    pdfs = _real_pdfs()
    if not pdfs:
        pytest.skip("Ingen ekte PDF i testdata/pdf/ – legg inn kornoter for Fase 1-måling")

    pdf = pdfs[0]
    result = process_pdf(pdf, tmp_path / "out", dpi=300, pages=[0])
    print("\n" + format_report(result))  # noqa: T201 - nyttig ved -s

    page = result.pages[0]
    # Vi dømmer ikke musikalsk korrekthet her (det gjør mennesket), men
    # integrasjonen skal produsere en fil uten å krasje.
    assert page.error is None, f"homr feilet: {page.error}"
    assert page.musicxml_path is not None and page.musicxml_path.exists()
