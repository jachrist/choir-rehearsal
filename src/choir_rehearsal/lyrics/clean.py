"""Rens rå tekst fra PDF-tekstlaget til lesbar sangtekst (Fase 3).

Tekstlaget i engraverte noter blander ofte inn musikkfont-glyffer (notehoder,
noekler osv.) fra Unicodes private omraade (U+E000-U+F8FF), sammen med den
faktiske sangteksten. I tillegg brukes typografiske konvensjoner:

- bindestrek med mellomrom ("al - dri") for stavelsesdeling,
- understrek ("gaa____") som melisme-/forlengelseslinje,
- ligaturer (fi-ligatur for "fi").

Denne modulen fjerner glyffene, normaliserer ligaturer, fjerner
melisme-understrek og gjoer " - " om til ekte stavelses-bindestrek, slik at
resultatet kan tokeniseres av :mod:`choir_rehearsal.lyrics.syllables`.
"""

from __future__ import annotations

import re
import unicodedata

# Unicode privat bruksomraade (U+E000-U+F8FF) - der musikkfonter legger glyffene.
_PUA = re.compile("[\ue000-\uf8ff]")
_UNDERSCORES = re.compile("_+")
# Vanlig bindestrek + typografiske varianter (U+2010, U+2011, U+2212).
_SPACED_HYPHEN = re.compile("\\s*[-\u2010\u2011\u2212]\\s*")
_LOOSE_HYPHEN = re.compile("(^|\\s)[-\u2010\u2011\u2212](\\s|$)")
_MULTISPACE = re.compile("\\s+")

# Seksjons-/strukturord som opptrer i partituret, men ikke er sangtekst. De kan
# vaere limt sammen med teksten (f.eks. "KorVers2KorEn"), saa vi krever ikke
# ordgrense etter ordet. Store forbokstaver holder det unna vanlige tekstord.
DEFAULT_SECTION_LABELS = (
    "Vers", "Kor", "Bridge", "Refreng", "Refr", "Coda", "Intro", "Outro", "Verse", "Chorus",
)
_SECTION_RE = re.compile("(" + "|".join(DEFAULT_SECTION_LABELS) + r")\s*\d*")


def strip_music_glyphs(text: str) -> str:
    """Fjern glyffer fra Unicodes private bruksomraade (musikkfont-tegn)."""
    return _PUA.sub("", text)


def normalize_ligatures(text: str) -> str:
    """Loes opp typografiske ligaturer (fi->fi, fl->fl osv.) via NFKC-normalisering."""
    return unicodedata.normalize("NFKC", text)


def strip_melisma_extenders(text: str) -> str:
    """Fjern understrek-forlengelser (melisme markeres via legatobuer, ikke tekst)."""
    return _UNDERSCORES.sub(" ", text)


def join_syllable_hyphens(text: str) -> str:
    """Gjoer "al - dri" om til "al-dri" saa stavelsesdeling bevares."""
    return _SPACED_HYPHEN.sub("-", text)


def strip_section_labels(text: str) -> str:
    """Fjern seksjons-/strukturord (Vers, Kor, Bridge, Refreng ...) inkl. tall.

    Fjerner ordene selv naar de er limt sammen med teksten ("KorVers2KorEn"
    → " En"). Store forbokstaver gjoer at vanlige tekstord ikke rammes.
    """
    return _MULTISPACE.sub(" ", _SECTION_RE.sub(" ", text)).strip()


def clean_lyric_text(raw: str) -> str:
    """Full rensing: fjern glyffer, normaliser ligaturer, fjern melisme-understrek,
    slaa sammen stavelses-bindestrek og komprimer mellomrom."""
    text = strip_music_glyphs(raw)
    text = normalize_ligatures(text)
    text = strip_melisma_extenders(text)
    text = join_syllable_hyphens(text)
    text = _MULTISPACE.sub(" ", text).strip()
    # Rydd opp loese bindestreker som ble til overs (f.eks. "-" alene mellom ord).
    text = _LOOSE_HYPHEN.sub(" ", text)
    return _MULTISPACE.sub(" ", text).strip()
