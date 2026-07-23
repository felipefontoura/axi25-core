#!/usr/bin/env bash
# Cloud-first setup for the axi25-source skill (macOS / Linux). Creates an isolated venv at
# scripts/.venv with the light pip deps (no ML, no host tools — ffmpeg comes from
# imageio-ffmpeg). Nothing outside this dir is touched. (Windows: use setup.ps1.)
#
#   cd .claude/skills/axi25-source/scripts && ./setup.sh
#
# Engine is `uv` (cross-platform, manages Python itself). One secret: OPENROUTER_API_KEY.
set -euo pipefail
cd "$(dirname "$0")"

if command -v uv >/dev/null 2>&1; then
  uv python install 3.13 || true
  uv sync
else
  echo "[error] uv not found — install it: https://docs.astral.sh/uv"
  exit 1
fi

[ -f .env ] || { [ -f .env.example ] && cp .env.example .env && echo "[setup] created .env — fill in OPENROUTER_API_KEY"; }

echo
echo "[ok] isolated venv ready → scripts/.venv"
echo "    run:  uv run python source.py --help"
echo "    key:  put OPENROUTER_API_KEY in scripts/.env  (https://openrouter.ai/keys)"
