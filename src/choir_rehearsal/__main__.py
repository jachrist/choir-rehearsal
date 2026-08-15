"""Gjør pakken kjørbar som modul: ``python -m choir_rehearsal ...``.

Nyttig når konsoll-scriptet ``choir-omr`` ikke ligger på PATH (typisk med
Microsoft Store-Python på Windows).
"""

from choir_rehearsal.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
