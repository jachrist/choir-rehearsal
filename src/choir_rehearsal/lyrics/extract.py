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

from dataclasses import dataclass, field
from statistics import median

from choir_rehearsal.pdf.textlayer import TextSpan


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
