"""Sidesammenslåing: flere MusicXML-sider → ett sammenhengende partitur (Fase 2).

Slår sammen sider som deler samme stemmestruktur (takt-for-takt, løpende
taktnummerering). Sider med avvikende struktur grupperes og rapporteres i stedet
for å slås sammen blindt – se ``pipeline.phase2``.
"""

from choir_rehearsal.merge.musicxml_merge import (
    MergeError,
    group_by_part_count,
    merge_scores,
    part_count,
)

__all__ = [
    "MergeError",
    "group_by_part_count",
    "merge_scores",
    "part_count",
]
