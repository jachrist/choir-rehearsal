"""Kommandolinje-inngang for pipelinen.

Fase 1:
    choir-omr fase1 noter.pdf --out-dir output/ [--dpi 300] [--pages 0,1]

Kjører PDF → bilde → homr → rå MusicXML og skriver en kvalitetsrapport til
terminalen. Krever at homr er installert (``pip install -e '.[omr]'``).

Fase 2:
    choir-omr fase2 output/noter/ --out output/noter_merged.musicxml [--pages 0,1]

Slår sammen per-side MusicXML i en mappe til ett sammenhengende partitur.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from choir_rehearsal.config import DEFAULT_DPI
from choir_rehearsal.omr import homr_available
from choir_rehearsal.pipeline import format_report, process_pdf
from choir_rehearsal.pipeline import phase2 as _phase2


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


def _cmd_fase2(args: argparse.Namespace) -> int:
    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"Finner ikke mappe: {directory}", file=sys.stderr)
        return 2
    out = Path(args.out) if args.out else directory / "merged.musicxml"
    result = _phase2.merge_folder(directory, out, pages=_parse_pages(args.pages))
    print(_phase2.format_report(result))
    return 0 if result.merged_path is not None else 1


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

    p2 = sub.add_parser("fase2", help="Slå sammen per-side MusicXML til ett partitur")
    p2.add_argument("directory", help="Mappe med per-side .musicxml (f.eks. output/noter/)")
    p2.add_argument(
        "--out",
        default=None,
        help="Sti til sammenslått fil (default: <mappe>/merged.musicxml)",
    )
    p2.add_argument(
        "--pages",
        default=None,
        help="Kommaseparerte 0-indekserte sider å slå sammen (må ha lik struktur)",
    )
    p2.set_defaults(func=_cmd_fase2)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
