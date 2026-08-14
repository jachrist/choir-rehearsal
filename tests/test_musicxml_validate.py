"""Tester for MusicXML-validering – pipelinens gjennomgående kontrakt."""

from __future__ import annotations

import pytest

from choir_rehearsal.musicxml import (
    MusicXMLValidationError,
    count_measures,
    count_notes,
    count_parts,
    distinct_voices,
    is_well_formed,
    parse,
)


def test_valid_musicxml_is_well_formed(valid_musicxml: str):
    assert is_well_formed(valid_musicxml) is True


def test_parse_returns_root(valid_musicxml: str):
    root = parse(valid_musicxml)
    assert root.tag == "score-partwise"


def test_count_measures(valid_musicxml: str):
    assert count_measures(valid_musicxml) == 2


def test_count_parts_and_notes(valid_musicxml: str):
    assert count_parts(valid_musicxml) == 1
    assert count_notes(valid_musicxml) == 2


def test_distinct_voices():
    xml = (
        "<score-partwise><part id='P1'><measure number='1'>"
        "<note><voice>1</voice></note><note><voice>2</voice></note>"
        "<note><voice>1</voice></note></measure></part></score-partwise>"
    )
    assert distinct_voices(xml) == 2


def test_distinct_voices_none_when_absent(valid_musicxml: str):
    assert distinct_voices(valid_musicxml) == 0


def test_malformed_xml_is_not_well_formed():
    assert is_well_formed("<score-partwise><measure></score-partwise>") is False


def test_wrong_root_rejected():
    assert is_well_formed("<html><body>ikke noter</body></html>") is False


def test_parse_raises_on_wrong_root():
    with pytest.raises(MusicXMLValidationError):
        parse("<foo/>")


def test_parse_accepts_bytes(valid_musicxml: str):
    root = parse(valid_musicxml.encode("utf-8"))
    assert root.tag == "score-partwise"


def test_parse_accepts_file_path(tmp_path, valid_musicxml: str):
    p = tmp_path / "score.musicxml"
    p.write_text(valid_musicxml, encoding="utf-8")
    assert count_measures(p) == 2
