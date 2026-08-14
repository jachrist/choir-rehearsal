"""Tester for innsetting av <lyric> på syngbare noter."""

from __future__ import annotations

from lxml import etree

from choir_rehearsal.lyrics import (
    apply_lyrics_by_measure,
    apply_lyrics_to_part,
    is_singable,
    singable_notes,
    tokenize_line,
)
from choir_rehearsal.lyrics.place import apply_lyrics_to_score


def _note(pitch="C", *, rest=False, chord=False, tie_stop=False, slur=None) -> str:
    if rest:
        return "<note><rest/><duration>4</duration></note>"
    inner = ""
    if chord:
        inner += "<chord/>"
    inner += f"<pitch><step>{pitch}</step><octave>4</octave></pitch><duration>4</duration>"
    if tie_stop:
        inner += '<tie type="stop"/>'
    if slur:  # "start" | "stop" | "start-stop"
        notations = "".join(f'<slur type="{t}"/>' for t in slur.split("-"))
        inner += f"<notations>{notations}</notations>"
    return f"<note>{inner}</note>"


def _part(notes_xml: str, part_id="P1") -> etree._Element:
    xml = f'<part id="{part_id}"><measure number="1">{notes_xml}</measure></part>'
    return etree.fromstring(xml)


def _multi_measure_part(*measures: str, part_id="P1") -> etree._Element:
    body = "".join(
        f'<measure number="{i + 1}">{m}</measure>' for i, m in enumerate(measures)
    )
    return etree.fromstring(f'<part id="{part_id}">{body}</part>')


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


def test_slur_melisma_skips_continuation_notes():
    # C starter legatobue, D fortsetter, E stopper -> hele buen = én stavelse (på C).
    # F er utenfor buen -> neste stavelse.
    part = _part(
        _note("C", slur="start") + _note("D") + _note("E", slur="stop") + _note("F")
    )
    n = apply_lyrics_to_part(part, tokenize_line("glo-ri"))
    assert n == 2
    lyric_texts = {
        note.find("pitch/step").text: note.findtext("lyric/text")
        for note in part.findall(".//note")
    }
    assert lyric_texts["C"] == "glo"  # første note under buen
    assert lyric_texts["D"] is None  # melisme-fortsettelse, ingen tekst
    assert lyric_texts["E"] is None
    assert lyric_texts["F"] == "ri"  # neste stavelse etter buen


def test_respect_slurs_false_assigns_every_note():
    part = _part(_note("C", slur="start") + _note("D") + _note("E", slur="stop"))
    n = apply_lyrics_to_part(part, tokenize_line("a b c"), respect_slurs=False)
    assert n == 3


def test_by_measure_contains_error_within_measure():
    # Takt 1 har en melisme homr IKKE merket (ingen slur), så én ekstra note.
    # Med takt-vis tildeling forskyves likevel ikke takt 2.
    m1 = _note("C") + _note("D") + _note("E")  # 3 noter, men bare 2 stavelser gis
    m2 = _note("F") + _note("G")
    part = _multi_measure_part(m1, m2)
    total = apply_lyrics_by_measure(
        part,
        [tokenize_line("en to"), tokenize_line("tre fi-re")],
        respect_slurs=False,
    )
    assert total == 4
    # Takt 2 starter rent på "tre", uavhengig av at takt 1 hadde en note til overs.
    m2_notes = part.findall("measure")[1].findall("note")
    assert m2_notes[0].findtext("lyric/text") == "tre"
    assert m2_notes[1].findtext("lyric/text") == "fi"


def test_by_measure_skips_measures_without_syllables():
    part = _multi_measure_part(_note("C"), _note("D"))
    total = apply_lyrics_by_measure(part, [tokenize_line("bare")])
    assert total == 1
    assert part.findall("measure")[1].find("note/lyric") is None


def test_second_verse_number():
    part = _part(_note("C") + _note("D"))
    apply_lyrics_to_part(part, tokenize_line("vers en"), number=1)
    apply_lyrics_to_part(part, tokenize_line("vers to"), number=2)
    first = part.find(".//note")
    nums = sorted(lyr.get("number") for lyr in first.findall("lyric"))
    assert nums == ["1", "2"]
