#!/bin/bash
set -euo pipefail

# Kun i Claude Code på web (remote). Lokalt gjør utvikleren oppsettet selv.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "$CLAUDE_PROJECT_DIR"

# Installer prosjektet med dev-verktøy (pytest, ruff). Idempotent og cache-vennlig.
# Tunge OMR-avhengigheter (homr/torch) holdes utenfor og installeres i Fase 1.
# pip-oppgradering er best-effort (systemets pip kan være distro-styrt).
python3 -m pip install --quiet --upgrade pip >/dev/null 2>&1 || true
python3 -m pip install --quiet -e ".[dev]"

echo "choir-rehearsal: dev-miljø klart (pytest + ruff installert)."
