"""Resolve an API key from the environment, then a list of .env files. Stdlib only.

The skill's own `scripts/.env` is the single home for its ONE secret
(OPENROUTER_API_KEY) and is always checked as the last-resort fallback.
"""
from __future__ import annotations

import os
from pathlib import Path


def workspace_env() -> Path | None:
    """The skill's `.env` at `scripts/.env` (nearest ancestor with `pyproject.toml`)."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists():
            return parent / ".env"
    return None


def resolve(name: str, search_paths: list[Path] | None = None) -> str | None:
    """Env var first; then the given .env files; then the skill's `scripts/.env`.

    The skill `.env` is always checked last, so callers find the shared secret
    (OPENROUTER_API_KEY) from one home without passing paths.
    """
    val = os.environ.get(name)
    if val:
        return val
    paths = [Path(p) for p in (search_paths or [])]
    ws = workspace_env()
    if ws is not None and ws not in paths:
        paths.append(ws)
    for env_path in paths:
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith(f"{name}=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None
