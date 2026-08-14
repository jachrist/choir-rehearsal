"""Tester for stavelse-tokenisering."""

from __future__ import annotations

from choir_rehearsal.lyrics import syllabify_word, tokenize_line


def test_single_syllable_word():
    syls = syllabify_word("jul")
    assert len(syls) == 1
    assert syls[0].text == "jul"
    assert syls[0].syllabic == "single"


def test_multi_syllable_word():
    syls = syllabify_word("glo-ri-a")
    assert [s.text for s in syls] == ["glo", "ri", "a"]
    assert [s.syllabic for s in syls] == ["begin", "middle", "end"]


def test_two_syllable_word():
    syls = syllabify_word("san-gen")
    assert [s.syllabic for s in syls] == ["begin", "end"]


def test_tokenize_line_mixed():
    syls = tokenize_line("Glo-ri-a in ex-cel-sis")
    assert [s.text for s in syls] == ["Glo", "ri", "a", "in", "ex", "cel", "sis"]
    assert [s.syllabic for s in syls] == [
        "begin", "middle", "end", "single", "begin", "middle", "end",
    ]


def test_norwegian_characters_preserved():
    syls = tokenize_line("kjæ-re væ-ne må-ne")
    assert [s.text for s in syls] == ["kjæ", "re", "væ", "ne", "må", "ne"]


def test_empty_and_whitespace():
    assert tokenize_line("") == []
    assert tokenize_line("   ") == []


def test_extra_hyphens_do_not_make_empty_syllables():
    syls = syllabify_word("glo--ri-")
    assert [s.text for s in syls] == ["glo", "ri"]
    assert [s.syllabic for s in syls] == ["begin", "end"]


def test_unicode_hyphen_variants():
    # non-breaking hyphen (U+2011) skal behandles som vanlig bindestrek
    syls = syllabify_word("glo‑ri‑a")
    assert [s.text for s in syls] == ["glo", "ri", "a"]
