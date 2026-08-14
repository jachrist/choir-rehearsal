"""Subprosess-wrapper rundt homr-CLI-et (Fase 1).

homr kjøres som ``homr <bilde>`` og skriver MusicXML med ``.musicxml``-endelse i
samme mappe som inndatabildet. homr har ikke et stabilt Python-API, så vi kaller
CLI-et. Dette isolerer resten av pipelinen fra interne endringer i homr.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

# Rimelig tak: homr på CPU kan bruke lang tid per side. Kan overstyres per kall.
DEFAULT_TIMEOUT_S = 900


class HomrError(RuntimeError):
    """homr feilet under kjøring, eller produserte ikke forventet MusicXML."""


class HomrNotInstalledError(HomrError):
    """homr-CLI-et finnes ikke på PATH. Installer med: pip install -e '.[omr]'"""


def homr_available() -> bool:
    """Returner ``True`` hvis homr-CLI-et finnes på PATH."""
    return shutil.which("homr") is not None


def _expected_output(image_path: Path) -> Path:
    return image_path.with_suffix(".musicxml")


def run_homr(
    image_path: str | Path,
    *,
    timeout: int = DEFAULT_TIMEOUT_S,
    extra_args: list[str] | None = None,
) -> Path:
    """Kjør homr på ett bilde og returner stien til produsert MusicXML-fil.

    Args:
        image_path: Sti til sidebildet (PNG/JPG).
        timeout: Maks kjøretid i sekunder.
        extra_args: Ekstra CLI-flagg til homr (f.eks. ``["--output-tempo", "80"]``).

    Returns:
        Sti til ``<bilde>.musicxml``.

    Raises:
        HomrNotInstalledError: homr finnes ikke på PATH.
        FileNotFoundError: Bildet finnes ikke.
        HomrError: homr returnerte feil, tidsavbrudd, eller ingen utdatafil.
    """
    image_path = Path(image_path)
    if not homr_available():
        raise HomrNotInstalledError(
            "homr-CLI-et finnes ikke på PATH. Installer med: pip install -e '.[omr]'"
        )
    if not image_path.exists():
        raise FileNotFoundError(f"Bildet finnes ikke: {image_path}")

    cmd = ["homr", *(extra_args or []), str(image_path)]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise HomrError(f"homr tidsavbrudd etter {timeout}s på {image_path.name}") from exc

    if proc.returncode != 0:
        raise HomrError(
            f"homr feilet (kode {proc.returncode}) på {image_path.name}:\n"
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        )

    out = _expected_output(image_path)
    if not out.exists():
        # Fallback: homr kan i prinsippet navngi utdata litt annerledes.
        candidates = sorted(image_path.parent.glob(f"{image_path.stem}*.musicxml"))
        if not candidates:
            raise HomrError(
                f"homr fullførte, men fant ingen MusicXML-fil for {image_path.name}"
            )
        out = candidates[0]
    return out


def image_to_musicxml(
    image_path: str | Path,
    *,
    timeout: int = DEFAULT_TIMEOUT_S,
    extra_args: list[str] | None = None,
) -> str:
    """Kjør homr på ett bilde og returner MusicXML-innholdet som tekst."""
    out = run_homr(image_path, timeout=timeout, extra_args=extra_args)
    return out.read_text(encoding="utf-8")
