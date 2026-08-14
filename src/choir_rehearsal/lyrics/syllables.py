"""Del sangtekst i stavelser (Fase 3).

En sangtekstlinje deles i stavelser slik MusicXML forventer dem: hvert
``<lyric>`` har en ``<syllabic>``-verdi som sier om stavelsen står alene eller er
del av et ord delt over flere noter:

- ``single`` – ett-stavelses ord ("og", "jul")
- ``begin``  – første stavelse i et delt ord ("glo" i "glo-ri-a")
- ``middle`` – midtstavelse ("ri")
- ``end``    – siste stavelse ("a")

Konvensjon i noter/MusicXML: stavelser i et delt ord skilles med bindestrek.
Denne modulen tar en linje der ord er delt med bindestrek (slik de står under
notene, f.eks. "Glo-ri-a in ex-cel-sis") og gir en liste med stavelser.

Grenser i v1 (dokumentert): melisme (én stavelse over flere noter, ofte markert
med understrek/forlengelse) og elisjon (to stavelser på én note) håndteres ikke
spesielt ennå – de hører til en senere iterasjon.
"""

from __future__ import annotations

from dataclasses import dataclass

# Ulike bindestrek-tegn som kan opptre i tekstlag (vanlig, non-breaking, minus).
_HYPHENS = "-‐‑−"


@dataclass(frozen=True)
class Syllable:
    """En stavelse klar til å settes inn som ``<lyric>``."""

    text: str
    syllabic: str  # single | begin | middle | end


def _split_word_into_syllables(word: str) -> list[str]:
    """Del ett ord på bindestrek til stavelsestekster, uten tomme biter."""
    normalized = word
    for h in _HYPHENS[1:]:
        normalized = normalized.replace(h, "-")
    parts = [p for p in normalized.split("-") if p != ""]
    return parts


def syllabify_word(word: str) -> list[Syllable]:
    """Gjør ett (muligens bindestrek-delt) ord om til stavelser med syllabic-type."""
    parts = _split_word_into_syllables(word)
    if not parts:
        return []
    if len(parts) == 1:
        return [Syllable(parts[0], "single")]
    out: list[Syllable] = []
    for i, p in enumerate(parts):
        if i == 0:
            syl = "begin"
        elif i == len(parts) - 1:
            syl = "end"
        else:
            syl = "middle"
        out.append(Syllable(p, syl))
    return out


def tokenize_line(line: str) -> list[Syllable]:
    """Del en hel sangtekstlinje i stavelser.

    Ord skilles med mellomrom; stavelser i et ord skilles med bindestrek.
    Eksempel: ``"Glo-ri-a in ex-cel-sis"`` →
    begin/middle/end for "Glo/ri/a", single for "in", begin/middle/end for
    "ex/cel/sis".
    """
    syllables: list[Syllable] = []
    for word in line.split():
        syllables.extend(syllabify_word(word))
    return syllables
