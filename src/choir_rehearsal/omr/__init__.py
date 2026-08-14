"""OMR-steget: bilde → rå MusicXML via homr (Fase 1).

Wrapper rundt homr (https://github.com/liebharc/homr). Implementeres i Fase 1;
homr installeres via ``pip install -e ".[omr]"`` pga. tunge avhengigheter (torch).

Merk (avklart forutsetning): partiturene er SATB med klaver og kan ha divisi
(opptil 8 stemmer), ofte med damestemmer og herrestemmer på hver sin notelinje.
Wrapperen må bevare flerstavs-strukturen homr gir, og Fase 1-valideringen skal
eksplisitt sjekke divisi-tilfeller.
"""

from __future__ import annotations

from pathlib import Path


def image_to_musicxml(image_path: str | Path) -> str:  # pragma: no cover - Fase 1
    """Kjør homr på ett sidebilde og returner rå MusicXML.

    Ikke implementert ennå – legges til i Fase 1 sammen med homr-avhengigheten.
    """
    raise NotImplementedError(
        "OMR-wrapperen implementeres i Fase 1. Installer homr med: pip install -e '.[omr]'"
    )
