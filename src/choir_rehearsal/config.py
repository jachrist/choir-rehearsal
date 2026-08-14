"""Sentrale konstanter for pipelinen."""

# Standard oppløsning for PDF → bilde. Kildene er ofte rene digitale PDF-er,
# så 300 dpi er et godt utgangspunkt (jf. brief). Kan økes for skannet materiale.
DEFAULT_DPI = 300

# En side regnes å ha et brukbart tekstlag hvis den inneholder minst så mange
# tekst-tegn ved direkte uttrekk. Terskelen skiller innkjøpte PDF-er (ekte tekst)
# fra skannede bilder (0 tegn). Se pdf/textlayer.py.
TEXT_LAYER_MIN_CHARS = 8
