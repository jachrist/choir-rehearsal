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
    """Sant hvis noten skal ha en egen stavelse (ikke pause/akkord-medlem/tie-stop).

    Merk: dette fanger *bindebuer* (tie, samme tonehøyde holdes). *Legatobuer*
    (slur/melisme, én stavelse over flere ulike toner) håndteres separat i
    tildelingen, siden det krever tilstand over flere noter – se ``_assign``.
    """
    if note.find("rest") is not None:
        return False
    if note.find("chord") is not None:
        return False
    for tie in note.findall("tie"):
        if tie.get("type") == "stop":
            return False
    return True


def _slur_types(note: etree._Element) -> set[str]:
    """Hvilke slur-typer (start/stop) noten bærer, fra <notations><slur ...>."""
    return {s.get("type") for s in note.findall(".//slur") if s.get("type")}


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


def _assign(
    notes: list[etree._Element],
    syllables: list[Syllable],
    number: int,
    respect_slurs: bool,
) -> int:
    """Tildel stavelser til en ordnet liste syngbare noter. Returnerer antall satt inn.

    Når ``respect_slurs`` er sann, regnes en legatobue (slur) som melisme: bare den
    *første* noten under buen får en stavelse; de øvrige notene under buen hoppes
    over til buen slutter. Det hindrer at teksten forskyves én note per melisme.
    """
    syl_iter = iter(syllables)
    count = 0
    in_melisma = False
    for note in notes:
        if respect_slurs and in_melisma:
            # Note under en pågående legatobue: ingen ny stavelse.
            if "stop" in _slur_types(note):
                in_melisma = False
            continue
        syl = next(syl_iter, None)
        if syl is None:
            break
        _insert_lyric(note, _make_lyric(syl, number))
        count += 1
        if respect_slurs:
            types = _slur_types(note)
            if "start" in types and "stop" not in types:
                in_melisma = True
    return count


def apply_lyrics_to_part(
    part: etree._Element,
    syllables: list[Syllable],
    *,
    number: int = 1,
    respect_slurs: bool = True,
) -> int:
    """Tildel stavelser til syngbare noter i en stemme. Returnerer antall satt inn.

    Endrer ``part`` på stedet. Legatobuer (melisme) håndteres når
    ``respect_slurs`` er sann (standard). Flere noter enn stavelser → de
    overskytende notene får ingen tekst; flere stavelser enn noter → de
    overskytende stavelsene brukes ikke.

    Advarsel om feilinnkapsling: her tildeles hele stemmen i én sekvens, så en
    feil (f.eks. en melisme homr ikke merket) forskyver *alle* etterfølgende
    stavelser. Bruk :func:`apply_lyrics_by_measure` for å begrense slike feil til
    én takt om gangen.
    """
    return _assign(singable_notes(part), syllables, number, respect_slurs)


def apply_lyrics_by_measure(
    part: etree._Element,
    syllables_per_measure: list[list[Syllable]],
    *,
    number: int = 1,
    respect_slurs: bool = True,
) -> int:
    """Tildel stavelser takt for takt, med re-synkronisering ved hver taktstrek.

    ``syllables_per_measure[i]`` er stavelsene som hører til takt *i*. Fordi hver
    takt tildeles uavhengig, holder en feilkobling (f.eks. en melisme homr ikke
    merket, eller en ekstra/manglende note) seg *innenfor den ene takten* og
    forskyver ikke resten av stykket – lett å rette i MuseScore.

    Takter uten en tilhørende bolk i ``syllables_per_measure`` får ingen tekst.
    Returnerer totalt antall stavelser satt inn.
    """
    measures = part.findall("measure")
    total = 0
    for i, measure in enumerate(measures):
        if i >= len(syllables_per_measure):
            break
        notes = [n for n in measure.findall(".//note") if is_singable(n)]
        total += _assign(notes, syllables_per_measure[i], number, respect_slurs)
    return total


def apply_lyrics_to_score(
    root: etree._Element,
    part_id: str,
    syllables: list[Syllable],
    *,
    number: int = 1,
    respect_slurs: bool = True,
) -> int:
    """Som :func:`apply_lyrics_to_part`, men finn stemmen via ``part_id`` i et partitur."""
    part = root.find(f".//part[@id='{part_id}']")
    if part is None:
        raise KeyError(f"Fant ikke stemme med id {part_id!r}")
    return apply_lyrics_to_part(part, syllables, number=number, respect_slurs=respect_slurs)


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
