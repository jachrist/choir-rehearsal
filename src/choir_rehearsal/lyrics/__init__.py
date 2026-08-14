"""Sangtekst-gjenkjenning og -plassering (Fase 3) – prosjektets vanskeligste steg.

Forgrening (avklart forutsetning): innkjøpte PDF-er med tekstlag gir eksakt tekst
med posisjon via ``choir_rehearsal.pdf.textlayer`` (ingen OCR nødvendig). Skannede
sider må gå via OCR/vision.

Anbefalt tilnærming: hybrid. Bounding-box per stavelse (fra tekstlag eller OCR) gir
deterministisk posisjon; en vision-modell gjør den vanskelige koblingen
stavelse→note og håndterer bindestrek-deling og elisjon. Divisi (to stemmer på én
stav) kompliserer koblingen og trenger egne testtilfeller.
"""

from __future__ import annotations


def place_lyrics():  # pragma: no cover - Fase 3
    """Koble stavelser til noter og sette dem inn i <lyric>-elementer.

    Ikke implementert ennå – legges til i Fase 3.
    """
    raise NotImplementedError("Sangtekst-plassering implementeres i Fase 3.")
