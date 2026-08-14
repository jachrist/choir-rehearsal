"""Slå sammen per-side MusicXML til ett sammenhengende partitur (Fase 2).

homr produserer én MusicXML-fil per side. For å få ett spillbart partitur per
stykke må sidene slås sammen: takter skjøtes sammen per stemme, med løpende
taktnummerering.

Kjerneutfordringen (bekreftet på ekte kornoter): homr tolker ofte antall stemmer
*ulikt fra side til side* (f.eks. 1 stemme på tittelsiden, 4 på SATB-sidene, eller
vekslende 1–3 i lukket partitur). Denne modulen skjuler *ikke* slike forskjeller.
Den slår sammen sider som deler samme stemmestruktur, og lar den som orkestrerer
(``pipeline.phase2``) gruppere sidene og velge den største konsistente gruppen.
Sider med avvikende struktur er en OMR-feil som må rettes (Fase 4), ikke noe
mergeren skal gjette seg til.

Grenser i denne versjonen (dokumentert, testet der det er relevant):
- Repetisjoner/voltaer *inne i* en takt bevares som de er.
- En repetisjon som er åpnet på én side og lukkes på neste håndteres ikke spesielt.
- ``<divisions>`` kan variere mellom sider; verdiene beholdes per takt slik homr
  ga dem (MuseScore tolker attributt-endringer midt i partituret).
"""

from __future__ import annotations

import copy
from pathlib import Path

from lxml import etree

from choir_rehearsal import musicxml


class MergeError(ValueError):
    """Sidene kan ikke slås sammen (f.eks. ulikt antall stemmer)."""


def part_count(source: str | bytes | Path) -> int:
    """Antall stemmer (``<score-part>``) i en side."""
    return musicxml.count_parts(source)


def _roots(sources: list[str | bytes | Path]) -> list[etree._Element]:
    return [musicxml.parse(s) for s in sources]


def group_by_part_count(sources: list[str | bytes | Path]) -> dict[int, list[int]]:
    """Grupper sideindekser etter antall stemmer.

    Returnerer f.eks. ``{1: [0], 4: [1, 2, 3, 4, 5]}`` – nyttig for å finne den
    største konsistente gruppen å slå sammen.
    """
    groups: dict[int, list[int]] = {}
    for i, root in enumerate(_roots(sources)):
        n = len(root.findall(".//part-list/score-part"))
        groups.setdefault(n, []).append(i)
    return groups


def _part_elements(root: etree._Element) -> list[etree._Element]:
    return root.findall("part")


def merge_scores(sources: list[str | bytes | Path]) -> str:
    """Slå sammen sider med *lik* stemmestruktur til ett partitur (MusicXML-tekst).

    Takter skjøtes per stemme i siderekkefølge og nummereres løpende fra 1.

    Raises:
        MergeError: Hvis listen er tom, eller sidene har ulikt antall stemmer.
    """
    if not sources:
        raise MergeError("Ingen sider å slå sammen")

    roots = _roots(sources)
    counts = [len(r.findall(".//part-list/score-part")) for r in roots]
    if len(set(counts)) != 1:
        raise MergeError(
            "Sidene har ulikt antall stemmer og kan ikke slås sammen direkte: "
            f"{counts}. Grupper sidene (se group_by_part_count) og slå sammen "
            "én konsistent gruppe om gangen."
        )
    n_parts = counts[0]
    if n_parts == 0:
        raise MergeError("Sidene har ingen stemmer (tomt part-list)")

    # Bygg skjelett fra første side: behold header (work, identification, defaults,
    # part-list), men bytt ut selve stemmene med sammenslåtte takter.
    template = copy.deepcopy(roots[0])
    for part in _part_elements(template):
        template.remove(part)

    # Normaliser part-id-er til P1..PN både i part-list og i kroppen.
    score_parts = template.findall(".//part-list/score-part")
    part_ids = [f"P{i + 1}" for i in range(n_parts)]
    for sp, pid in zip(score_parts, part_ids, strict=True):
        sp.set("id", pid)

    # For hver stemme: samle takter fra alle sider, renummerer løpende.
    for p_idx, pid in enumerate(part_ids):
        merged_part = etree.SubElement(template, "part")
        merged_part.set("id", pid)
        measure_no = 1
        for root in roots:
            parts = _part_elements(root)
            src_part = parts[p_idx]
            for measure in src_part.findall("measure"):
                m = copy.deepcopy(measure)
                m.set("number", str(measure_no))
                merged_part.append(m)
                measure_no += 1

    xml_bytes = etree.tostring(
        template, xml_declaration=True, encoding="UTF-8", pretty_print=True
    )
    return xml_bytes.decode("utf-8")
