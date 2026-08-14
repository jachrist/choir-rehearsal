"""Orkestrering av pipelinen.

- Fase 1 (``phase1``): render → homr → validering.
- Fase 2 (``phase2``): slå sammen per-side MusicXML til ett partitur.
"""

from choir_rehearsal.pipeline.phase1 import (
    PageResult,
    format_report,
    process_pdf,
)
from choir_rehearsal.pipeline.phase2 import (
    MergeResult,
    merge_folder,
)

__all__ = [
    "PageResult",
    "format_report",
    "process_pdf",
    "MergeResult",
    "merge_folder",
]
