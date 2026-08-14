"""Tester for Fase 2-orkestreringen (merge_folder + rapport)."""

from __future__ import annotations

from pathlib import Path

from choir_rehearsal import musicxml
from choir_rehearsal.pipeline import merge_folder
from choir_rehearsal.pipeline.phase2 import format_report
from tests.test_merge import page


def _write_pages(directory: Path, pages: list[str]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for i, xml in enumerate(pages):
        (directory / f"side-{i:03d}.musicxml").write_text(xml, encoding="utf-8")


def test_merge_folder_picks_largest_group(tmp_path: Path):
    # side 0 = 1 stemme (tittel), sidene 1-3 = 4 stemmer (SATB) -> største gruppe
    _write_pages(tmp_path, [page(1, 5), page(4, 2), page(4, 3), page(4, 2)])
    out = tmp_path / "merged.musicxml"
    result = merge_folder(tmp_path, out)

    assert result.merged_path == out
    assert out.exists()
    assert result.part_count == 4
    assert result.merged_pages == [1, 2, 3]
    assert result.total_measures == 7
    assert 1 in result.excluded and result.excluded[1] == [0]
    assert musicxml.is_well_formed(out)


def test_merge_folder_report_mentions_excluded(tmp_path: Path):
    _write_pages(tmp_path, [page(1, 5), page(4, 2), page(4, 2)])
    result = merge_folder(tmp_path, tmp_path / "m.musicxml")
    report = format_report(result)
    assert "Sammenslått" in report
    assert "Utelatt" in report


def test_merge_folder_explicit_pages(tmp_path: Path):
    _write_pages(tmp_path, [page(4, 2), page(4, 3), page(1, 9)])
    result = merge_folder(tmp_path, tmp_path / "m.musicxml", pages=[0, 1])
    assert result.merged_pages == [0, 1]
    assert result.total_measures == 5


def test_merge_folder_empty_dir(tmp_path: Path):
    result = merge_folder(tmp_path, tmp_path / "m.musicxml")
    assert result.merged_path is None
    assert "Ingen MusicXML" in format_report(result)


def test_single_group_no_exclusions(tmp_path: Path):
    _write_pages(tmp_path, [page(4, 2), page(4, 2)])
    result = merge_folder(tmp_path, tmp_path / "m.musicxml")
    assert result.excluded == {}
    assert result.merged_pages == [0, 1]
