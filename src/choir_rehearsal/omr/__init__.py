"""OMR-steget: bilde → rå MusicXML via homr (Fase 1).

Wrapper rundt homr (https://github.com/liebharc/homr). homr eksponerer ikke et
stabilt Python-API; det brukes som et CLI-verktøy (``homr <bilde>`` skriver
``<bilde>.musicxml`` ved siden av inndata). Denne wrapperen kaller CLI-et som en
subprosess, slik at integrasjonen er robust mot interne endringer i homr.

Merk (avklart forutsetning): partiturene er SATB med klaver og kan ha divisi
(opptil 8 stemmer), ofte med damestemmer og herrestemmer på hver sin notelinje.
Fase 1-valideringen skal eksplisitt sjekke at flerstavs-strukturen bevares.
"""

from choir_rehearsal.omr.homr_runner import (
    HomrError,
    HomrNotInstalledError,
    homr_available,
    image_to_musicxml,
    run_homr,
)

__all__ = [
    "HomrError",
    "HomrNotInstalledError",
    "homr_available",
    "image_to_musicxml",
    "run_homr",
]
