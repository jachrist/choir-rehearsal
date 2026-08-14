"""Tester for redigeringsmotoren (Fase 4). Verifiserer at kun lyrics endres."""

from __future__ import annotations

from lxml import etree

from choir_rehearsal.ui import editor


def _score(n_notes=4, part_id="P1", name="Soprano") -> etree._Element:
    notes = "".join(
        "<note><pitch><step>C</step><octave>5</octave></pitch>"
        "<duration>4</duration></note>"
        for _ in range(n_notes)
    )
    return etree.fromstring(
        "<score-partwise><part-list>"
        f'<score-part id="{part_id}"><part-name>{name}</part-name></score-part>'
        "</part-list>"
        f'<part id="{part_id}"><measure number="1">{notes}</measure></part>'
        "</score-partwise>"
    )


def test_list_voices():
    root = _score(4)
    voices = editor.list_voices(root)
    assert len(voices) == 1
    assert voices[0].part_id == "P1"
    assert voices[0].name == "Soprano"
    assert voices[0].singable_notes == 4
    assert voices[0].lyric_count == 0


def test_set_text_and_get():
    root = _score(4)
    editor.set_text(root, "P1", "glo-ri-a nå")
    assert editor.get_syllables(root, "P1") == ["glo", "ri", "a", "nå"]
    assert editor.list_voices(root)[0].lyric_count == 4


def test_clear_lyrics():
    root = _score(3)
    editor.set_text(root, "P1", "en to tre")
    removed = editor.clear_lyrics(root, "P1")
    assert removed == 3
    assert editor.get_syllables(root, "P1") == ["", "", ""]


def test_shift_right_inserts_blanks():
    root = _score(4)
    editor.set_text(root, "P1", "a b c")
    editor.shift_lyrics(root, "P1", 1)  # skyv én note mot høyre
    assert editor.get_syllables(root, "P1") == ["", "a", "b", "c"]


def test_shift_left_drops_leading():
    root = _score(4)
    editor.set_text(root, "P1", "a b c d")
    editor.shift_lyrics(root, "P1", -1)  # dropp første stavelse
    assert editor.get_syllables(root, "P1") == ["b", "c", "d", ""]


def test_set_syllable_on_single_note():
    root = _score(3)
    editor.set_text(root, "P1", "a b c")
    editor.set_syllable_on_note(root, "P1", 1, "X")
    assert editor.get_syllables(root, "P1") == ["a", "X", "c"]


def test_set_syllable_empty_removes():
    root = _score(2)
    editor.set_text(root, "P1", "a b")
    editor.set_syllable_on_note(root, "P1", 0, "")
    assert editor.get_syllables(root, "P1") == ["", "b"]


def test_only_lyrics_change_notes_preserved():
    root = _score(3)
    before_notes = len(root.findall(".//note"))
    before_pitches = [n.findtext("pitch/step") for n in root.findall(".//note")]
    editor.set_text(root, "P1", "en to tre")
    editor.shift_lyrics(root, "P1", 1)
    editor.clear_lyrics(root, "P1")
    editor.set_text(root, "P1", "ny tekst her")
    after_notes = len(root.findall(".//note"))
    after_pitches = [n.findtext("pitch/step") for n in root.findall(".//note")]
    assert after_notes == before_notes
    assert after_pitches == before_pitches
