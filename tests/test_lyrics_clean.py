"""Tester for rensing av raa tekstlag-tekst til sangtekst."""

from __future__ import annotations

from choir_rehearsal.lyrics import clean_lyric_text, tokenize_line
from choir_rehearsal.lyrics.clean import (
    join_syllable_hyphens,
    normalize_ligatures,
    strip_melisma_extenders,
    strip_music_glyphs,
)

# Noen tegn fra Unicodes private bruksomraade (musikkfont-glyffer).
PUA = ""


def test_strip_music_glyphs():
    raw = f"S.{PUA}Enn{PUA} om"
    assert strip_music_glyphs(raw) == "S.Enn om"


def test_normalize_ligatures():
    assert normalize_ligatures("oppﬁn-ner") == "oppfin-ner"  # U+FB01 = fi-ligatur


def test_strip_melisma_extenders():
    assert strip_melisma_extenders("gaa____").strip() == "gaa"


def test_join_syllable_hyphens():
    assert join_syllable_hyphens("al - dri") == "al-dri"
    assert join_syllable_hyphens("ven  -  ta") == "ven-ta"


def test_clean_full_pipeline_on_realistic_line():
    raw = f"S.{PUA}Enn om det al  -  dri er ment aa gaa____________"
    assert clean_lyric_text(raw) == "S.Enn om det al-dri er ment aa gaa"


def test_clean_preserves_hyphenation_and_ligature():
    raw = f" E  - vig  opp - ﬁn - ner  naa________{PUA}"
    cleaned = clean_lyric_text(raw)
    assert cleaned == "E-vig opp-fin-ner naa"
    syls = tokenize_line(cleaned)
    assert [s.text for s in syls] == ["E", "vig", "opp", "fin", "ner", "naa"]
    assert [s.syllabic for s in syls][:2] == ["begin", "end"]


def test_clean_empty():
    assert clean_lyric_text("") == ""
    assert clean_lyric_text(PUA) == ""
