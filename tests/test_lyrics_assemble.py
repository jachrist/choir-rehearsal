"""Tester for seksjonsfilter, dedup og stemme-vis sammensetting."""

from __future__ import annotations

from choir_rehearsal.lyrics import (
    assemble_voice_lyrics,
    dedup_doubled_tokens,
    group_lines,
    sequence_similarity,
    strip_section_labels,
)
from choir_rehearsal.lyrics.evaluate import diff_syllables, ground_truth_syllables
from choir_rehearsal.pdf.textlayer import TextSpan


def span(text, x0, y0, w=10.0, h=10.0) -> TextSpan:
    return TextSpan(text=text, x0=x0, y0=y0, x1=x0 + w, y1=y0 + h, page_index=0)


def test_strip_section_labels_glued():
    assert strip_section_labels("Vers 2 KorVers 2 KorEn om") == "En om"
    assert strip_section_labels("Bridge3 syng her") == "syng her"


def test_strip_section_labels_leaves_normal_text():
    assert strip_section_labels("Enn om det al-dri") == "Enn om det al-dri"


def test_dedup_doubled_tokens():
    assert dedup_doubled_tokens(["a", "b", "a", "b"]) == ["a", "b"]
    assert dedup_doubled_tokens(["a", "b", "c"]) == ["a", "b", "c"]
    assert dedup_doubled_tokens(["a", "b", "a", "c"]) == ["a", "b", "a", "c"]


def test_assemble_voice_lyrics_basic():
    spans = [
        span("S.", 10, 100), span("Enn", 30, 100), span("om", 60, 100),
        span("A.", 10, 200), span("Enn", 30, 200), span("om", 60, 200),
    ]
    voices = assemble_voice_lyrics(group_lines(spans))
    assert voices["S"] == "Enn om"
    assert voices["A"] == "Enn om"


def test_assemble_shared_label_fills_both_voices():
    spans = [span("A.T.", 10, 100), span("syng", 45, 100), span("nå", 80, 100)]
    voices = assemble_voice_lyrics(group_lines(spans))
    assert voices["A"] == "syng nå"
    assert voices["T"] == "syng nå"


def test_assemble_filters_section_and_dedup():
    # linje med seksjonsord foran og doblet tekst
    spans = [
        span("S.", 10, 100), span("Kor", 30, 100),
        span("syng", 60, 100), span("nå", 90, 100),
        span("syng", 120, 100), span("nå", 150, 100),
    ]
    voices = assemble_voice_lyrics(group_lines(spans))
    assert voices["S"] == "syng nå"


def test_sequence_similarity():
    assert sequence_similarity(["a", "b", "c"], ["a", "b", "c"]) == 1.0
    assert sequence_similarity(["a", "b"], ["x", "y"]) == 0.0
    assert 0 < sequence_similarity(["a", "b", "c"], ["a", "x", "c"]) < 1


def test_ground_truth_syllables():
    xml = (
        '<score-partwise><part-list>'
        '<score-part id="P1"><part-name>S</part-name></score-part></part-list>'
        '<part id="P1"><measure number="1">'
        '<note><pitch><step>C</step><octave>5</octave></pitch><duration>4</duration>'
        '<lyric number="1"><syllabic>begin</syllabic><text>glo</text></lyric></note>'
        '<note><pitch><step>D</step><octave>5</octave></pitch><duration>4</duration>'
        '<lyric number="1"><syllabic>end</syllabic><text>ria</text></lyric></note>'
        '</measure></part></score-partwise>'
    )
    assert ground_truth_syllables(xml, "P1") == ["glo", "ria"]


def test_diff_syllables_flags_replacement():
    diff = diff_syllables(["a", "b", "c"], ["a", "x", "c"])
    tags = [d[0] for d in diff]
    assert "replace" in tags
