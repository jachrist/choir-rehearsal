"""Golden-file-test: mål sangtekst-uttrekket mot en manuelt rettet fasit.

Kjører kun når både kilde-PDF-en og den rettede MusicXML-fila finnes i repo-roten
(begge er opphavsrettsbeskyttet og holdes lokalt). Låser inn nøyaktigheten slik at
forbedringer måles og regresjoner fanges. Kjør med: ``pytest -m slow``.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from choir_rehearsal import musicxml
from choir_rehearsal.lyrics import (
    assemble_voice_lyrics,
    ground_truth_syllables,
    group_lines,
    sequence_similarity,
    tokenize_line,
)
from choir_rehearsal.pdf.textlayer import extract_text_spans

REPO_ROOT = Path(__file__).parent.parent

pytestmark = pytest.mark.slow


def _find(pattern: str) -> Path | None:
    hits = sorted(REPO_ROOT.glob(pattern))
    return hits[0] if hits else None


def _voice_to_part(root) -> dict[str, str]:
    """Kople stemmebokstav (S/A/T/B) til part-id via part-name i fasiten."""
    mapping = {}
    for sp in root.findall(".//part-list/score-part"):
        name = (sp.findtext("part-name") or "").strip().lower()
        pid = sp.get("id")
        for letter, key in [("S", "sopran"), ("A", "alt"), ("T", "tenor"), ("B", "bass")]:
            if name.startswith(key):
                mapping[letter] = pid
    return mapping


def test_lyric_extraction_matches_corrected_file():
    pdf = _find("Stein*.pdf")
    corrected = _find("*stein*.musicxml") or _find("*Stein*.musicxml")
    if pdf is None or corrected is None:
        pytest.skip("Mangler kilde-PDF og/eller rettet MusicXML i repo-roten")

    # Uttrekk sangtekst per stemme fra alle sider i PDF-en.
    all_lines = []
    for page in range(0, 6):
        try:
            all_lines.extend(group_lines(extract_text_spans(pdf, page)))
        except IndexError:
            break
    extracted = assemble_voice_lyrics(all_lines)

    root = musicxml.parse(corrected)
    voice_to_part = _voice_to_part(root)
    assert set("SATB") <= set(voice_to_part), "fasiten mangler en SATB-stemme"

    thresholds = {"S": 0.80, "A": 0.85, "T": 0.85, "B": 0.80}
    for voice, part_id in voice_to_part.items():
        truth = ground_truth_syllables(root, part_id)
        mine = [s.text for s in tokenize_line(extracted.get(voice, ""))]
        sim = sequence_similarity(truth, mine)
        assert sim >= thresholds[voice], (
            f"{voice}: likhet {sim:.2f} under terskel {thresholds[voice]} "
            f"(fasit={len(truth)}, min={len(mine)})"
        )
