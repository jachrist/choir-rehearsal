"""Kommandolinje-inngang for pipelinen.

Fase 1:
    choir-omr fase1 noter.pdf --out-dir output/ [--dpi 300] [--pages 0,1]

Kjører PDF → bilde → homr → rå MusicXML og skriver en kvalitetsrapport til
terminalen. Krever at homr er installert (``pip install -e '.[omr]'``).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from choir_rehearsal.config import DEFAULT_DPI
from choir_rehearsal.omr import homr_available
from choir_rehearsal.pipeline import format_report, process_pdf


def _parse_pages(value: str | None) -> list[int] | None:
    if not value:
        return None
    return [int(x) for x in value.split(",") if x.strip() != ""]


def _cmd_fase1(args: argparse.Namespace) -> int:
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"Finner ikke PDF: {pdf_path}", file=sys.stderr)
        return 2
    if not homr_available():
        print(
            "homr er ikke installert. Installer med: pip install -e '.[omr]'",
            file=sys.stderr,
        )
        return 3

    result = process_pdf(
        pdf_path,
        out_dir=args.out_dir,
        dpi=args.dpi,
        pages=_parse_pages(args.pages),
    )
    print(format_report(result))
    # Exit-kode 1 hvis ingen side ga brukbar MusicXML – nyttig i skript/CI.
    return 0 if result.ok_pages > 0 else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="choir-omr",
        description="OMR-pipeline for kornoter (PDF → MusicXML).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p1 = sub.add_parser("fase1", help="PDF → bilde → homr → rå MusicXML + kvalitetsrapport")
    p1.add_argument("pdf", help="Sti til PDF-en med noter")
    p1.add_argument(
        "--out-dir",
        default="output",
        help="Mappe for bilder og MusicXML (default: output/)",
    )
    p1.add_argument(
        "--dpi",
        type=int,
        default=DEFAULT_DPI,
        help=f"Oppløsning for PDF → bilde (default: {DEFAULT_DPI})",
    )
    p1.add_argument(
        "--pages",
        default=None,
        help="Kommaseparerte 0-indekserte sider, f.eks. 0,1 (default: alle)",
    )
    p1.set_defaults(func=_cmd_fase1)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
