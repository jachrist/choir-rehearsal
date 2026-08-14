"""Fase 1: PDF → bilde → homr → rå MusicXML, med en enkel kvalitetsrapport.

Formålet med Fase 1 er å *måle* homr sin gjenkjenningskvalitet på ekte kornoter
før mer tid investeres. Denne modulen kjører hele kjeden per side og samler
enkle signaler (velformethet, antall takter/stemmer/noter, divisi-indikasjon)
som gir et raskt bilde av hvor godt homr traff. Den *dømmer* ikke kvaliteten –
det gjør mennesket ved å sammenligne med kildesiden – men den fanger åpenbare
feil (tom eller ugyldig MusicXML, manglende stemmer) automatisk.

Homr-kallet er isolert bak ``omr.run_homr`` slik at denne orkestreringen kan
testes uten at homr/torch er installert.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from choir_rehearsal import musicxml
from choir_rehearsal.config import DEFAULT_DPI
from choir_rehearsal.omr import run_homr
from choir_rehearsal.pdf import render_pdf_to_pngs


@dataclass
class PageResult:
    """Resultat og kvalitetssignaler for én side gjennom Fase 1."""

    page_index: int
    image_path: Path | None = None
    musicxml_path: Path | None = None
    ok: bool = False
    well_formed: bool = False
    measures: int = 0
    parts: int = 0
    voices: int = 0
    notes: int = 0
    error: str | None = None

    @property
    def has_divisi(self) -> bool:
        """Flere stemmer enn stavesystemer tyder på divisi/delte stemmer."""
        return self.voices > self.parts

    @property
    def looks_empty(self) -> bool:
        """Velformet, men uten noter – ofte tegn på at homr ikke traff siden."""
        return self.well_formed and self.notes == 0


@dataclass
class Phase1Result:
    """Samlet resultat for en hel PDF."""

    pdf_path: Path
    pages: list[PageResult] = field(default_factory=list)

    @property
    def ok_pages(self) -> int:
        return sum(1 for p in self.pages if p.ok)


def _analyze_musicxml(result: PageResult, xml_path: Path) -> None:
    """Fyll inn kvalitetssignaler fra produsert MusicXML på ``result``."""
    result.musicxml_path = xml_path
    if not musicxml.is_well_formed(xml_path):
        result.error = "MusicXML er ikke velformet / feil rot-element"
        return
    result.well_formed = True
    result.measures = musicxml.count_measures(xml_path)
    result.parts = musicxml.count_parts(xml_path)
    result.voices = musicxml.distinct_voices(xml_path)
    result.notes = musicxml.count_notes(xml_path)
    result.ok = result.notes > 0


def process_pdf(
    pdf_path: str | Path,
    out_dir: str | Path,
    *,
    dpi: int = DEFAULT_DPI,
    pages: list[int] | None = None,
    homr_timeout: int = 900,
) -> Phase1Result:
    """Kjør Fase 1 på en PDF og returner et resultat med kvalitetssignaler per side.

    Én side som feiler (homr-feil, ugyldig utdata) stopper ikke resten – feilen
    fanges og registreres på den aktuelle ``PageResult``.

    Args:
        pdf_path: Sti til PDF-en.
        out_dir: Mappe for genererte bilder og MusicXML-filer.
        dpi: Oppløsning for PDF → bilde.
        pages: Valgfri liste med 0-indekserte sider å behandle (default: alle).
        homr_timeout: Maks kjøretid for homr per side (sekunder).
    """
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    images = render_pdf_to_pngs(pdf_path, out_dir, dpi=dpi)
    selected = pages if pages is not None else list(range(len(images)))

    result = Phase1Result(pdf_path=pdf_path)
    for idx in selected:
        page = PageResult(page_index=idx)
        try:
            image = images[idx]
            page.image_path = image
            xml_path = run_homr(image, timeout=homr_timeout)
            _analyze_musicxml(page, xml_path)
        except IndexError:
            page.error = f"Side {idx} finnes ikke i PDF-en"
        except Exception as exc:  # noqa: BLE001 - vi vil rapportere, ikke krasje hele kjøringen
            page.error = f"{type(exc).__name__}: {exc}"
        result.pages.append(page)
    return result


def format_report(result: Phase1Result) -> str:
    """Formater en kort, lesbar kvalitetsrapport for terminalen."""
    lines: list[str] = []
    lines.append(f"Fase 1-rapport for: {result.pdf_path.name}")
    lines.append(f"Sider behandlet: {len(result.pages)} | OK: {result.ok_pages}")
    lines.append("")
    header = (
        f"{'side':>4}  {'ok':>3}  {'takter':>6}  {'stemmer':>7}  "
        f"{'voices':>6}  {'noter':>5}  merknad"
    )
    lines.append(header)
    lines.append("-" * len(header))
    for p in result.pages:
        note = ""
        if p.error:
            note = p.error
        elif p.looks_empty:
            note = "tom – homr traff neppe siden"
        elif p.has_divisi:
            note = "divisi (flere voices enn stemmer)"
        lines.append(
            f"{p.page_index:>4}  {'ja' if p.ok else 'nei':>3}  "
            f"{p.measures:>6}  {p.parts:>7}  {p.voices:>6}  {p.notes:>5}  {note}"
        )
    return "\n".join(lines)
