"""Redigeringsmotor for sangtekst (Fase 4) – rene operasjoner på MusicXML.

Verktøyet er hybrid: noter og struktur rettes i MuseScore, mens *sangtekst-
plasseringen* rettes her. Derfor rører disse operasjonene **kun** ``<lyric>``-
elementer; alt annet (noter, struktur, piano, dynamikk) bevares uendret, så
MuseScore-arbeidet ikke forstyrres.

Alle operasjoner jobber på et parset MusicXML-tre (``lxml``-element) og gjenbruker
plasseringslogikken fra :mod:`choir_rehearsal.lyrics.place` (inkl. melisme/slur-
håndtering). De er rene og enhetstestbare uten server.
"""

from __future__ import annotations

from dataclasses import dataclass

from lxml import etree

from choir_rehearsal.lyrics.place import (
    _make_lyric,
    is_singable,
    singable_notes,
)
from choir_rehearsal.lyrics.syllables import Syllable, tokenize_line


@dataclass
class VoiceInfo:
    """Oppsummering av en stemme for redigerings-UI-et."""

    part_id: str
    name: str
    singable_notes: int
    lyric_count: int


def list_voices(root: etree._Element) -> list[VoiceInfo]:
    """List stemmene i partituret med antall syngbare noter og satte stavelser."""
    out: list[VoiceInfo] = []
    for sp in root.findall(".//part-list/score-part"):
        pid = sp.get("id")
        name = (sp.findtext("part-name") or pid or "").strip()
        part = root.find(f".//part[@id='{pid}']")
        if part is None:
            continue
        notes = singable_notes(part)
        nlyr = sum(1 for n in notes if n.find("lyric") is not None)
        out.append(VoiceInfo(pid, name, len(notes), nlyr))
    return out


def _require_part(root: etree._Element, part_id: str) -> etree._Element:
    part = root.find(f".//part[@id='{part_id}']")
    if part is None:
        raise KeyError(f"Fant ikke stemme med id {part_id!r}")
    return part


def get_syllables(root: etree._Element, part_id: str, *, number: int = 1) -> list[str]:
    """Nåværende stavelsestekster (i rekkefølge) for de syngbare notene i en stemme.

    Noter uten tekst gir tom streng, slik at listen flukter med de syngbare notene.
    """
    part = _require_part(root, part_id)
    out: list[str] = []
    for note in singable_notes(part):
        text = ""
        for lyr in note.findall("lyric"):
            if lyr.get("number") == str(number):
                text = lyr.findtext("text") or ""
                break
        out.append(text)
    return out


def clear_lyrics(root: etree._Element, part_id: str, *, number: int = 1) -> int:
    """Fjern alle ``<lyric>`` med gitt vers-nummer i en stemme. Returnerer antall fjernet."""
    part = _require_part(root, part_id)
    removed = 0
    for note in part.findall(".//note"):
        for lyr in note.findall("lyric"):
            if lyr.get("number") == str(number):
                note.remove(lyr)
                removed += 1
    return removed


def _current_syllable_objs(root: etree._Element, part_id: str, number: int) -> list[Syllable]:
    """Hent nåværende stavelser som Syllable-objekter (bevarer syllabic)."""
    part = _require_part(root, part_id)
    out: list[Syllable] = []
    for note in singable_notes(part):
        for lyr in note.findall("lyric"):
            if lyr.get("number") == str(number):
                text = lyr.findtext("text") or ""
                syl = lyr.findtext("syllabic") or "single"
                if text:
                    out.append(Syllable(text, syl))
                break
    return out


def _place(
    root: etree._Element,
    part_id: str,
    syllables: list[Syllable],
    *,
    number: int,
    respect_slurs: bool,
    skip: int = 0,
) -> int:
    """Intern: tøm og legg stavelsene på de syngbare notene, ev. med ``skip`` blanke
    noter foran (brukes til forskyvning)."""
    from choir_rehearsal.lyrics.place import _assign

    clear_lyrics(root, part_id, number=number)
    part = _require_part(root, part_id)
    notes = singable_notes(part)
    if skip > 0:
        notes = notes[skip:]
    return _assign(notes, syllables, number, respect_slurs)


def set_text(
    root: etree._Element,
    part_id: str,
    text: str,
    *,
    number: int = 1,
    respect_slurs: bool = True,
) -> int:
    """Erstatt en stemmes sangtekst: tokeniser ``text`` og legg den på notene på nytt."""
    return _place(
        root, part_id, tokenize_line(text), number=number, respect_slurs=respect_slurs
    )


def shift_lyrics(
    root: etree._Element,
    part_id: str,
    offset: int,
    *,
    number: int = 1,
    respect_slurs: bool = True,
) -> int:
    """Forskyv stemmens stavelser ``offset`` syngbare noter (positivt = mot høyre).

    Retter den vanligste feilen: hele teksten ligger én note for tidlig/sent.
    Positiv offset skyver teksten senere (blanke noter foran); negativ dropper de
    første stavelsene.
    """
    syls = _current_syllable_objs(root, part_id, number)
    if offset < 0:
        syls = syls[-offset:]
        skip = 0
    else:
        skip = offset
    return _place(root, part_id, syls, number=number, respect_slurs=respect_slurs, skip=skip)


def set_syllable_on_note(
    root: etree._Element,
    part_id: str,
    singable_index: int,
    text: str,
    syllabic: str = "single",
    *,
    number: int = 1,
) -> None:
    """Sett/endre teksten på én bestemt syngbar note (0-indeksert). Tom tekst fjerner."""
    part = _require_part(root, part_id)
    notes = singable_notes(part)
    if not 0 <= singable_index < len(notes):
        raise IndexError(f"Note-indeks {singable_index} utenfor stemmen")
    note = notes[singable_index]
    for lyr in note.findall("lyric"):
        if lyr.get("number") == str(number):
            note.remove(lyr)
    if text:
        from choir_rehearsal.lyrics.place import _insert_lyric

        _insert_lyric(note, _make_lyric(Syllable(text, syllabic), number))


def note_is_singable(note: etree._Element) -> bool:
    """Re-eksport for bekvemmelighet."""
    return is_singable(note)
