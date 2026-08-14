"""Mål nøyaktigheten til sangtekst-koblingen mot en fasit (Fase 3).

En manuelt rettet MusicXML-fil (fasit) gir en kjent, korrekt stavelsesrekke per
stemme. Denne modulen sammenligner en uttrukket/plassert stavelsesrekke mot
fasiten og gir et likhetstall (0–1). Brukes både i en golden-file-test og til å
følge med på om forbedringer i renseren faktisk hjelper.
"""

from __future__ import annotations

import difflib
from pathlib import Path

from choir_rehearsal import musicxml


def ground_truth_syllables(source: str | bytes | Path, part_id: str) -> list[str]:
    """Hent stavelsestekstene (i rekkefølge) fra ``<lyric>`` i en stemme."""
    root = musicxml.parse(source)
    part = root.find(f".//part[@id='{part_id}']")
    if part is None:
        return []
    return [(lyr.findtext("text") or "").strip() for lyr in part.findall(".//note/lyric")]


def sequence_similarity(a: list[str], b: list[str]) -> float:
    """Likhet mellom to stavelsesrekker (0–1), ufølsom for store/små bokstaver."""
    matcher = difflib.SequenceMatcher(
        None, [x.lower() for x in a], [x.lower() for x in b]
    )
    return matcher.ratio()


def diff_syllables(a: list[str], b: list[str]) -> list[tuple[str, str, str]]:
    """Radvis diff mellom fasit ``a`` og uttrekk ``b``.

    Returnerer tripler ``(tag, fasit, min)`` der tag er "equal", "replace",
    "delete" (mangler i uttrekket) eller "insert" (ekstra i uttrekket) – nyttig
    for å se *hvor* det driver.
    """
    out: list[tuple[str, str, str]] = []
    sm = difflib.SequenceMatcher(None, [x.lower() for x in a], [x.lower() for x in b])
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        span = max(i2 - i1, j2 - j1)
        for k in range(span):
            fa = a[i1 + k] if i1 + k < i2 else ""
            mb = b[j1 + k] if j1 + k < j2 else ""
            out.append((tag, fa, mb))
    return out
