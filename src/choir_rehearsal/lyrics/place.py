"""Sett stavelser inn som ``<lyric>`` på syngbare noter i MusicXML (Fase 3).

Gitt en ordnet liste med stavelser og en stemme (``<part>``), tildeles stavelsene
til de syngbare notene i leserekkefølge. En «syngbar» note er en note som:

- ikke er en pause (``<rest>``),
- ikke er et akkord-medlem (``<chord>`` – akkorden er én sunget hendelse, teksten
  hører til den første noten), og
- ikke er en videreført bindebue (``<tie type="stop">`` – samme sungne tone holdes,
  ingen ny stavelse).

Dette er den sekvensielle koblingen: stavelse *k* → syngbar note *k*. Den trenger
ikke x-koordinater for notene, og passer derfor homr sin utdata (som ikke har
noteposisjoner). Melisme (én stavelse over flere noter) er en kjent grense i v1.
"""

from __future__ import annotations

import copy

from lxml import etree

from choir_rehearsal.lyrics.syllables import Syllable

# Rekkefølge på barn i <note> (forenklet MusicXML-DTD): <lyric> kommer sent,
# etter <notations>. Vi setter den inn før disse hvis de finnes, ellers sist.
_AFTER_LYRIC_TAGS = {"play", "listen"}


def is_singable(note: etree._Element) -> bool:
    """Sant hvis noten skal ha en egen stavelse (ikke pause/akkord-medlem/tie-stop)."""
    if note.find("rest") is not None:
        return False
    if note.find("chord") is not None:
        return False
    for tie in note.findall("tie"):
        if tie.get("type") == "stop":
            return False
    return True


def _make_lyric(syl: Syllable, number: int) -> etree._Element:
    lyric = etree.Element("lyric", number=str(number))
    syllabic = etree.SubElement(lyric, "syllabic")
    syllabic.text = syl.syllabic
    text = etree.SubElement(lyric, "text")
    text.text = syl.text
    return lyric


def _insert_lyric(note: etree._Element, lyric: etree._Element) -> None:
    # Fjern ev. eksisterende lyric med samme nummer (idempotent ny-kjøring).
    for existing in note.findall("lyric"):
        if existing.get("number") == lyric.get("number"):
            note.remove(existing)
    # Sett inn før <play>/<listen> hvis de finnes, ellers til slutt.
    insert_at = len(note)
    for i, child in enumerate(note):
        if child.tag in _AFTER_LYRIC_TAGS:
            insert_at = i
            break
    note.insert(insert_at, lyric)


def singable_notes(part: etree._Element) -> list[etree._Element]:
    """Alle syngbare noter i en stemme, i dokumentrekkefølge."""
    return [n for n in part.findall(".//note") if is_singable(n)]


def apply_lyrics_to_part(
    part: etree._Element,
    syllables: list[Syllable],
    *,
    number: int = 1,
) -> int:
    """Tildel stavelser til syngbare noter i en stemme. Returnerer antall satt inn.

    Endrer ``part`` på stedet. Hvis det er flere syngbare noter enn stavelser,
    får de overskytende notene ingen tekst. Hvis det er flere stavelser enn noter,
    blir de overskytende stavelsene ikke brukt (returverdien viser hvor mange som
    faktisk ble satt inn).
    """
    notes = singable_notes(part)
    count = 0
    for note, syl in zip(notes, syllables, strict=False):
        _insert_lyric(note, _make_lyric(syl, number))
        count += 1
    return count


def apply_lyrics_to_score(
    root: etree._Element,
    part_id: str,
    syllables: list[Syllable],
    *,
    number: int = 1,
) -> int:
    """Som :func:`apply_lyrics_to_part`, men finn stemmen via ``part_id`` i et partitur."""
    part = root.find(f".//part[@id='{part_id}']")
    if part is None:
        raise KeyError(f"Fant ikke stemme med id {part_id!r}")
    return apply_lyrics_to_part(part, syllables, number=number)


def clone_with_lyrics(
    part: etree._Element,
    syllables: list[Syllable],
    *,
    number: int = 1,
) -> etree._Element:
    """Ikke-muterende variant: returner en kopi av stemmen med tekst påført."""
    part_copy = copy.deepcopy(part)
    apply_lyrics_to_part(part_copy, syllables, number=number)
    return part_copy
