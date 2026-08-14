"""Sangtekst-gjenkjenning og -plassering (Fase 3) – prosjektets vanskeligste steg.

Forgrening (avklart forutsetning): innkjøpte PDF-er med tekstlag gir eksakt tekst
med posisjon via ``choir_rehearsal.pdf.textlayer`` (ingen OCR nødvendig). Skannede
sider må gå via OCR/vision.

homr sin MusicXML har ikke x-koordinater per note, så koblingen stavelse→note gjøres
sekvensielt (stavelse k → k-te syngbare note) innenfor hver stemme, ikke ved
x-matching. Modulene:

- ``syllables`` – del tekst i stavelser (syllabic begin/middle/end/single)
- ``extract``   – grupper tekst-spans til ordnede linjer
- ``place``     – sett stavelser inn som <lyric> på syngbare noter
"""

from choir_rehearsal.lyrics.extract import TextLine, group_lines, reconstruct_text
from choir_rehearsal.lyrics.place import (
    apply_lyrics_to_part,
    apply_lyrics_to_score,
    is_singable,
    singable_notes,
)
from choir_rehearsal.lyrics.syllables import Syllable, syllabify_word, tokenize_line

__all__ = [
    "Syllable",
    "syllabify_word",
    "tokenize_line",
    "TextLine",
    "group_lines",
    "reconstruct_text",
    "apply_lyrics_to_part",
    "apply_lyrics_to_score",
    "is_singable",
    "singable_notes",
]
