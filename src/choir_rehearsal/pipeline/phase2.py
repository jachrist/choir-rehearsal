"""Fase 2: slå sammen per-side MusicXML til ett partitur, med ærlig rapport.

Strategi når homr har tolket stemmestrukturen ulikt per side: grupper sidene etter
antall stemmer, slå sammen den *største konsistente gruppen*, og rapporter hvilke
sider som ble utelatt og hvorfor. Det gir alltid ett brukbart partitur for den
dominerende strukturen, uten å skjule OMR-feilene som må rettes senere (Fase 4).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from choir_rehearsal.merge import group_by_part_count, merge_scores


@dataclass
class MergeResult:
    """Resultat av å slå sammen en mappe med per-side MusicXML."""

    source_files: list[Path]
    merged_path: Path | None = None
    merged_pages: list[int] = field(default_factory=list)
    part_count: int = 0
    total_measures: int = 0
    excluded: dict[int, list[int]] = field(default_factory=dict)  # part_count -> sider
    groups: dict[int, list[int]] = field(default_factory=dict)


def find_page_musicxml(directory: str | Path) -> list[Path]:
    """Finn per-side MusicXML i en mappe, sortert (side-000.musicxml, ...)."""
    directory = Path(directory)
    return sorted(directory.glob("*.musicxml"))


def _largest_group(groups: dict[int, list[int]]) -> int:
    """Velg part-count for gruppen med flest sider (flest takter ved likhet-brudd
    løses av kallende kode); her: flest sider, deretter høyest part-count."""
    return max(groups, key=lambda pc: (len(groups[pc]), pc))


def merge_folder(
    directory: str | Path,
    out_path: str | Path,
    *,
    pages: list[int] | None = None,
) -> MergeResult:
    """Slå sammen per-side MusicXML i en mappe til ett partitur.

    Velger den største konsistente stemmegruppen med mindre ``pages`` er oppgitt
    (da slås akkurat de sidene sammen, og de må ha lik struktur).
    """
    files = find_page_musicxml(directory)
    result = MergeResult(source_files=files)
    if not files:
        return result

    if pages is not None:
        selected = pages
    else:
        groups = group_by_part_count([str(f) for f in files])
        result.groups = groups
        chosen_pc = _largest_group(groups)
        selected = groups[chosen_pc]
        result.excluded = {pc: idx for pc, idx in groups.items() if pc != chosen_pc}

    selected_files = [files[i] for i in selected]
    merged_xml = merge_scores([str(f) for f in selected_files])

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(merged_xml, encoding="utf-8")

    from choir_rehearsal import musicxml

    result.merged_path = out_path
    result.merged_pages = selected
    result.part_count = musicxml.count_parts(out_path)
    # Takter i første stemme = antall takter i partituret.
    root = musicxml.parse(out_path)
    first_part = root.find("part")
    result.total_measures = len(first_part.findall("measure")) if first_part is not None else 0
    return result


def format_report(result: MergeResult) -> str:
    """Kort, lesbar rapport for terminalen."""
    lines: list[str] = []
    if not result.source_files:
        return "Ingen MusicXML-sider funnet."
    if result.merged_path is None:
        return "Fant sider, men klarte ikke å slå sammen."
    lines.append(f"Sammenslått: {result.merged_path.name}")
    lines.append(
        f"Sider med i partituret: {len(result.merged_pages)} "
        f"({', '.join(str(p) for p in result.merged_pages)})"
    )
    lines.append(f"Stemmer: {result.part_count} | takter totalt: {result.total_measures}")
    if result.excluded:
        for pc, idx in sorted(result.excluded.items()):
            sider = ", ".join(str(i) for i in idx)
            lines.append(
                f"Utelatt (avvikende struktur, {pc} stemmer): side {sider} "
                f"– slå ev. sammen separat, eller rett strukturen først."
            )
    return "\n".join(lines)
