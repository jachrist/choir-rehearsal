"""Grupper tekst-spans fra PDF-tekstlaget til ordnede tekstlinjer (Fase 3).

``choir_rehearsal.pdf.extract_text_spans`` gir posisjonert tekst (én ``TextSpan``
per stykke) fra innkjøpte PDF-er med tekstlag. Her klynges disse til vannrette
linjer (etter y), sorteres venstre→høyre (etter x), og settes sammen til en
lesbar linjestreng der mellomrom gjenskapes ut fra horisontale mellomrom.

Resultatet er råmaterialet for stavelse-tokenisering: en sangtekstlinje som
``"Glo-ri-a in ex-cel-sis"``.

Merk: terskelverdiene her (linjehøyde-toleranse, mellomrom-faktor) bør finjusteres
mot ekte kornoter. Å *skille* sangtekstlinjer fra annen tekst (tittel, komponist,
tempo, sidetall) er en egen heuristikk som trenger reelle data og kommer i neste
steg – denne modulen gjør den geometriske grupperingen som uansett trengs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from statistics import median

from choir_rehearsal.lyrics.clean import clean_lyric_text, strip_section_labels
from choir_rehearsal.pdf.textlayer import TextSpan

# Stemme-etikett i starten av en sangtekstlinje, f.eks. "S.", "A.T.", "2S.11".
# Valgfrie ledende/etterfoelgende tall er takt-/systemnummer og forkastes.
_VOICE_LABEL = re.compile(r"^\s*\d*\s*((?:[SATB]\.)+)\s*\d*\s*")


@dataclass
class TextLine:
    """En vannrett linje med tekst, satt sammen av flere spans."""

    spans: list[TextSpan] = field(default_factory=list)

    @property
    def y_center(self) -> float:
        return sum((s.y0 + s.y1) / 2 for s in self.spans) / len(self.spans)

    @property
    def x0(self) -> float:
        return min(s.x0 for s in self.spans)

    @property
    def text(self) -> str:
        return reconstruct_text(self.spans)


def parse_voice_label(text: str) -> tuple[list[str], str]:
    """Skill ut stemme-etikett i starten av en linje.

    ``"2S.11Enn om det"`` → (``["S"]``, ``"Enn om det"``);
    ``"A.T. E-vig"`` → (``["A", "T"]``, ``"E-vig"``) – delt linje for alt og tenor.
    Uten gjenkjent etikett: (``[]``, uendret tekst).
    """
    m = _VOICE_LABEL.match(text)
    if not m:
        return [], text.strip()
    letters = [c for c in m.group(1) if c in "SATB"]
    return letters, text[m.end():].strip()


def dedup_doubled_tokens(tokens: list[str]) -> list[str]:
    """Hvis en linje er nøyaktig doblet (A A), behold bare den ene halvdelen.

    Enkelte delte staver/tekstlag gir samme sangtekstlinje to ganger etter
    hverandre. Dette fjerner den åpenbare doblingen uten å røre reell gjentakelse
    med varierende tekst.
    """
    n = len(tokens)
    if n >= 4 and n % 2 == 0 and tokens[: n // 2] == tokens[n // 2 :]:
        return tokens[: n // 2]
    return tokens


def assemble_voice_lyrics(
    lines: list[TextLine],
    *,
    section_filter: bool = True,
    dedup: bool = True,
) -> dict[str, str]:
    """Sett sammen sangtekst per stemme fra grupperte tekstlinjer.

    For hver linje: rens teksten, fjern seksjonsord, skill ut stemme-etikett, og
    føy resten til hver stemme etiketten peker på (``A.T.`` → både A og T).
    Returnerer f.eks. ``{"S": "Enn om det al-dri ...", "A": "..."}``.
    """
    collected: dict[str, list[str]] = {}
    for line in lines:
        text = clean_lyric_text(line.text)
        if section_filter:
            text = strip_section_labels(text)
        voices, rest = parse_voice_label(text)
        rest = rest.strip()
        if not voices or not rest:
            continue
        tokens = rest.split()
        if dedup:
            tokens = dedup_doubled_tokens(tokens)
        joined = " ".join(tokens)
        for v in voices:
            collected.setdefault(v, []).append(joined)
    return {v: " ".join(parts) for v, parts in collected.items()}


def _height(span: TextSpan) -> float:
    return span.y1 - span.y0


def group_lines(spans: list[TextSpan], *, y_tol: float | None = None) -> list[TextLine]:
    """Klyng spans til linjer etter vertikal posisjon (y-senter).

    ``y_tol`` er hvor nær to spans må være i y for å regnes som samme linje.
    Default: halvparten av median tegnhøyde.
    """
    if not spans:
        return []
    if y_tol is None:
        y_tol = median(_height(s) for s in spans) * 0.5

    ordered = sorted(spans, key=lambda s: (s.y0 + s.y1) / 2)
    lines: list[TextLine] = []
    current: list[TextSpan] = [ordered[0]]
    current_y = (ordered[0].y0 + ordered[0].y1) / 2

    for span in ordered[1:]:
        yc = (span.y0 + span.y1) / 2
        if abs(yc - current_y) <= y_tol:
            current.append(span)
            # løpende gjennomsnitt for stabilitet
            current_y = sum((s.y0 + s.y1) / 2 for s in current) / len(current)
        else:
            lines.append(TextLine(sorted(current, key=lambda s: s.x0)))
            current = [span]
            current_y = yc
    lines.append(TextLine(sorted(current, key=lambda s: s.x0)))
    return lines


def reconstruct_text(row_spans: list[TextSpan], *, space_ratio: float = 0.35) -> str:
    """Sett sammen spans (venstre→høyre) til én streng.

    Setter inn mellomrom mellom to spans når det horisontale gapet er større enn
    ``space_ratio`` × median tegnhøyde (en grov tilnærming til ordmellomrom).
    Nære spans limes sammen (typisk stavelser i samme ord / rundt bindestrek).
    """
    if not row_spans:
        return ""
    ordered = sorted(row_spans, key=lambda s: s.x0)
    heights = [_height(s) for s in ordered] or [1.0]
    gap_threshold = median(heights) * space_ratio

    out = ordered[0].text
    for prev, cur in zip(ordered, ordered[1:], strict=False):
        gap = cur.x0 - prev.x1
        if gap > gap_threshold:
            out += " "
        out += cur.text
    return out
