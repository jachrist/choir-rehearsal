"""Tester for merge-motoren (Fase 2)."""

from __future__ import annotations

import pytest

from choir_rehearsal import musicxml
from choir_rehearsal.merge import (
    MergeError,
    group_by_part_count,
    merge_scores,
    part_count,
)


def page(n_parts: int, measures_per_part: int, start_step: str = "C") -> str:
    """Bygg en side med gitt antall stemmer og takter (én note per takt)."""
    sp = "".join(
        f'<score-part id="P{i + 1}"><part-name>Voice</part-name></score-part>'
        for i in range(n_parts)
    )
    parts = ""
    for i in range(n_parts):
        meas = "".join(
            f'<measure number="{m + 1}">'
            f"<note><pitch><step>{start_step}</step><octave>5</octave></pitch>"
            f"<duration>4</duration><voice>1</voice></note></measure>"
            for m in range(measures_per_part)
        )
        parts += f'<part id="P{i + 1}">{meas}</part>'
    return (
        '<?xml version="1.0"?><score-partwise version="4.0">'
        f"<part-list>{sp}</part-list>{parts}</score-partwise>"
    )


def test_part_count():
    assert part_count(page(4, 2)) == 4
    assert part_count(page(1, 5)) == 1


def test_group_by_part_count():
    pages = [page(1, 3), page(4, 2), page(4, 2), page(1, 1)]
    groups = group_by_part_count(pages)
    assert groups == {1: [0, 3], 4: [1, 2]}


def test_merge_same_structure_concatenates_measures():
    # tre sider, 4 stemmer, med 2/3/2 takter -> 7 takter per stemme
    merged = merge_scores([page(4, 2), page(4, 3), page(4, 2)])
    assert musicxml.count_parts(merged) == 4
    root = musicxml.parse(merged)
    for part in root.findall("part"):
        measures = part.findall("measure")
        assert len(measures) == 7
        # løpende nummerering 1..7
        assert [m.get("number") for m in measures] == [str(i) for i in range(1, 8)]


def test_merge_preserves_total_notes():
    merged = merge_scores([page(2, 2), page(2, 2)])
    assert musicxml.count_notes(merged) == 2 * 4  # 2 stemmer * 4 takter * 1 note


def test_merge_rejects_mismatched_structure():
    with pytest.raises(MergeError, match="ulikt antall stemmer"):
        merge_scores([page(4, 2), page(1, 3)])


def test_merge_empty_raises():
    with pytest.raises(MergeError):
        merge_scores([])


def test_merge_single_page_renumbers():
    merged = merge_scores([page(1, 3)])
    root = musicxml.parse(merged)
    nums = [m.get("number") for m in root.find("part").findall("measure")]
    assert nums == ["1", "2", "3"]


def test_merged_output_is_well_formed():
    merged = merge_scores([page(4, 2), page(4, 2)])
    assert musicxml.is_well_formed(merged)
