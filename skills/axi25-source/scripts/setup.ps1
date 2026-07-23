# Cloud-first setup for the axi25-source skill (Windows / PowerShell). Creates an isolated
# venv at scripts\.venv with the light pip deps (no ML, no host tools — ffmpeg comes from
# imageio-ffmpeg). Nothing outside this dir is touched.
#
#   cd .claude\skills\axi25-source\scripts ; .\setup.ps1
#
# Engine is `uv` (manages Python itself). One secret: OPENROUTER_API_KEY.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)

if (Get-Command uv -ErrorAction SilentlyContinue) {
  uv python install 3.13
  uv sync
} else {
  Write-Host "[error] uv not found - install it: https://docs.astral.sh/uv"
  exit 1
}

if (-not (Test-Path .env)) {
  if (Test-Path .env.example) {
    Copy-Item .env.example .env
    Write-Host "[setup] created .env - fill in OPENROUTER_API_KEY"
  }
}

Write-Host ""
Write-Host "[ok] isolated venv ready -> scripts\.venv"
Write-Host "    run:  uv run python source.py --help"
Write-Host "    key:  put OPENROUTER_API_KEY in scripts\.env  (https://openrouter.ai/keys)"
