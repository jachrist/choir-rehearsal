"""Tester for gruppering av tekst-spans til linjer."""

from __future__ import annotations

from choir_rehearsal.lyrics import group_lines, parse_voice_label, reconstruct_text
from choir_rehearsal.pdf.textlayer import TextSpan


def test_parse_voice_label_single():
    voices, rest = parse_voice_label("S.Enn om det")
    assert voices == ["S"]
    assert rest == "Enn om det"


def test_parse_voice_label_with_measure_numbers():
    voices, rest = parse_voice_label("2S.11Enn om det")
    assert voices == ["S"]
    assert rest == "Enn om det"


def test_parse_voice_label_shared_alto_tenor():
    voices, rest = parse_voice_label("A.T. E-vig opp-fin-ner")
    assert voices == ["A", "T"]
    assert rest == "E-vig opp-fin-ner"


def test_parse_voice_label_none():
    voices, rest = parse_voice_label("bare vanlig tekst")
    assert voices == []
    assert rest == "bare vanlig tekst"


def span(text, x0, y0, w=10.0, h=10.0) -> TextSpan:
    return TextSpan(text=text, x0=x0, y0=y0, x1=x0 + w, y1=y0 + h, page_index=0)


def test_group_two_lines_by_y():
    spans = [
        span("Glo", 10, 100), span("ri", 30, 101), span("a", 50, 100),
        span("neste", 10, 200), span("linje", 60, 201),
    ]
    lines = group_lines(spans)
    assert len(lines) == 2
    assert [s.text for s in lines[0].spans] == ["Glo", "ri", "a"]
    assert [s.text for s in lines[1].spans] == ["neste", "linje"]


def test_lines_sorted_left_to_right():
    spans = [span("c", 90, 100), span("a", 10, 100), span("b", 50, 100)]
    lines = group_lines(spans)
    assert [s.text for s in lines[0].spans] == ["a", "b", "c"]


def test_reconstruct_text_inserts_spaces_on_gaps():
    # to ord med stort gap -> mellomrom; nær hverandre -> limt sammen
    spans = [span("in", 10, 100, w=10), span("ex", 60, 100, w=10)]
    assert reconstruct_text(spans) == "in ex"


def test_reconstruct_text_joins_close_spans():
    spans = [span("Glo", 10, 100, w=12), span("ri", 23, 100, w=8)]
    # gap = 23-22 = 1, langt under terskel -> ingen mellomrom
    assert reconstruct_text(spans) == "Glori"


def test_textline_text_property():
    spans = [span("syng", 10, 100, w=20), span("nå", 70, 100, w=10)]
    lines = group_lines(spans)
    assert lines[0].text == "syng nå"


def test_empty_input():
    assert group_lines([]) == []
    assert reconstruct_text([]) == ""


def test_y_center_and_x0_properties():
    spans = [span("a", 40, 100), span("b", 10, 102)]
    line = group_lines(spans)[0]
    assert line.x0 == 10
    assert 100 <= line.y_center <= 112
