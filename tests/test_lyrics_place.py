"""Tester for innsetting av <lyric> på syngbare noter."""

from __future__ import annotations

from lxml import etree

from choir_rehearsal.lyrics import (
    apply_lyrics_to_part,
    is_singable,
    singable_notes,
    tokenize_line,
)
from choir_rehearsal.lyrics.place import apply_lyrics_to_score


def _note(pitch="C", *, rest=False, chord=False, tie_stop=False) -> str:
    if rest:
        return "<note><rest/><duration>4</duration></note>"
    inner = ""
    if chord:
        inner += "<chord/>"
    inner += f"<pitch><step>{pitch}</step><octave>4</octave></pitch><duration>4</duration>"
    if tie_stop:
        inner += '<tie type="stop"/>'
    return f"<note>{inner}</note>"


def _part(notes_xml: str, part_id="P1") -> etree._Element:
    xml = f'<part id="{part_id}"><measure number="1">{notes_xml}</measure></part>'
    return etree.fromstring(xml)


def test_is_singable_rules():
    assert is_singable(etree.fromstring(_note("C"))) is True
    assert is_singable(etree.fromstring(_note(rest=True))) is False
    assert is_singable(etree.fromstring(_note("E", chord=True))) is False
    assert is_singable(etree.fromstring(_note("C", tie_stop=True))) is False


def test_singable_notes_skips_rest_and_chord():
    part = _part(_note("C") + _note(rest=True) + _note("E") + _note("G", chord=True))
    assert len(singable_notes(part)) == 2  # C og E; pause og akkord-medlem hoppes over


def test_apply_lyrics_sequential():
    part = _part(_note("C") + _note("D") + _note("E"))
    n = apply_lyrics_to_part(part, tokenize_line("glo-ri-a"))
    assert n == 3
    texts = [t.text for t in part.findall(".//note/lyric/text")]
    syls = [s.text for s in part.findall(".//note/lyric/syllabic")]
    assert texts == ["glo", "ri", "a"]
    assert syls == ["begin", "middle", "end"]


def test_lyrics_skip_rests_in_assignment():
    part = _part(_note("C") + _note(rest=True) + _note("E"))
    apply_lyrics_to_part(part, tokenize_line("ja vel"))
    # Bare de to syngbare notene får tekst, pausen ikke
    lyric_notes = part.findall(".//note[lyric]")
    assert len(lyric_notes) == 2


def test_more_notes_than_syllables_leaves_rest_empty():
    part = _part(_note("C") + _note("D") + _note("E"))
    n = apply_lyrics_to_part(part, tokenize_line("en"))
    assert n == 1
    assert len(part.findall(".//note/lyric")) == 1


def test_more_syllables_than_notes():
    part = _part(_note("C"))
    n = apply_lyrics_to_part(part, tokenize_line("glo-ri-a in ex-cel-sis"))
    assert n == 1


def test_idempotent_reapply_same_number():
    part = _part(_note("C") + _note("D"))
    apply_lyrics_to_part(part, tokenize_line("hei du"))
    apply_lyrics_to_part(part, tokenize_line("god dag"))
    # Ikke doble lyrics på samme note/nummer
    first_note = part.find(".//note")
    assert len(first_note.findall("lyric")) == 1
    assert first_note.find("lyric/text").text == "god"


def test_apply_to_score_by_part_id():
    root = etree.fromstring(
        '<score-partwise><part-list>'
        '<score-part id="P1"><part-name>S</part-name></score-part></part-list>'
        f'<part id="P1"><measure number="1">{_note("C") + _note("D")}</measure></part>'
        "</score-partwise>"
    )
    n = apply_lyrics_to_score(root, "P1", tokenize_line("hal-lo"))
    assert n == 2
    assert [t.text for t in root.findall(".//lyric/text")] == ["hal", "lo"]


def test_second_verse_number():
    part = _part(_note("C") + _note("D"))
    apply_lyrics_to_part(part, tokenize_line("vers en"), number=1)
    apply_lyrics_to_part(part, tokenize_line("vers to"), number=2)
    first = part.find(".//note")
    nums = sorted(lyr.get("number") for lyr in first.findall("lyric"))
    assert nums == ["1", "2"]
