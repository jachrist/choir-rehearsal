"""Tester for MusicXML-validering – pipelinens gjennomgående kontrakt."""

from __future__ import annotations

import pytest

from choir_rehearsal.musicxml import (
    MusicXMLValidationError,
    count_measures,
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
