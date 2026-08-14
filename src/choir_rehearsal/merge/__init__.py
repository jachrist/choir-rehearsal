"""Sidesammenslåing: flere MusicXML-sider → ett sammenhengende partitur (Fase 2).

Utgangspunkt: relieur (https://github.com/papoteur-mga/relieur). Høy risiko –
trolig ikke bygget for korpartitur med repetisjoner og 1./2. voltaer. Regn med
patching eller en egen sammenslåingsrutine på MusicXML-nivå. Testes eksplisitt
med repetisjoner, voltaer og opptakt over sidebytter.
"""

from __future__ import annotations

from pathlib import Path


def merge_pages(page_paths: list[str | Path]) -> str:  # pragma: no cover - Fase 2
    """Slå sammen MusicXML-sider (én per side) til ett partitur.

    Ikke implementert ennå – legges til i Fase 2.
    """
    raise NotImplementedError("Sammenslåing implementeres i Fase 2.")
