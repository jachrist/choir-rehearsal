"""Lettvekts MusicXML-validering.

MusicXML er kontrakten mellom alle stegene i pipelinen. Billige velformethet- og
strukturkontroller på hver faseovergang fanger stille korrupsjon tidlig. Full
XSD-validering mot den offisielle MusicXML-skjemaen legges til når skjemafilene
tas inn (Fase 2+); denne modulen dekker det som trengs uten eksterne skjemafiler.
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree

_MUSICXML_ROOTS = {"score-partwise", "score-timewise"}


class MusicXMLValidationError(ValueError):
    """Reises når innhold ikke er gyldig/velformet MusicXML."""


def _to_bytes(source: str | bytes | Path) -> bytes:
    if isinstance(source, bytes):
        return source
    if isinstance(source, Path):
        return source.read_bytes()
    # str: kan være en sti eller selve XML-innholdet
    stripped = source.lstrip()
    if stripped.startswith("<"):
        return source.encode("utf-8")
    return Path(source).read_bytes()


def parse(source: str | bytes | Path) -> etree._Element:
    """Parse MusicXML og returner rot-elementet.

    Godtar rå XML (str/bytes) eller en filsti.

    Raises:
        MusicXMLValidationError: Ved ugyldig XML eller feil rot-element.
    """
    raw = _to_bytes(source)
    try:
        root = etree.fromstring(raw)
    except etree.XMLSyntaxError as exc:  # pragma: no cover - meldingstekst varierer
        raise MusicXMLValidationError(f"Ugyldig XML: {exc}") from exc

    tag = etree.QName(root).localname
    if tag not in _MUSICXML_ROOTS:
        raise MusicXMLValidationError(
            f"Rot-element er <{tag}>, forventet et av {sorted(_MUSICXML_ROOTS)}"
        )
    return root


def is_well_formed(source: str | bytes | Path) -> bool:
    """Returner ``True`` hvis kilden er velformet MusicXML med riktig rot-element."""
    try:
        parse(source)
    except MusicXMLValidationError:
        return False
    return True


def count_measures(source: str | bytes | Path) -> int:
    """Tell antall ``<measure>``-elementer i partituret.

    Nyttig i sammenslåingstester (Fase 2): antall takter etter sammenslåing skal
    stemme med summen av takter i sidene.
    """
    root = parse(source)
    return len(root.findall(".//measure"))
