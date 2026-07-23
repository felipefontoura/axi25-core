"""Vault path + slug + hash helpers. Stdlib only.

Single source of truth for slug/path/hash logic shared by the four handlers.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date
from pathlib import Path


def today() -> str:
    """ISO date (YYYY-MM-DD) for `acquired`/`created`/`updated` frontmatter."""
    return date.today().isoformat()


def slugify(text: str, maxlen: int = 80) -> str:
    """kebab-case ASCII slug. English filenames rule (see AGENTS.md / references/naming.md)."""
    text = (text or "").lower()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:maxlen]


def vault_root(start: Path | str | None = None) -> Path:
    """Walk up from `start` (or this file) until the vault root is found.

    Root = the dir containing `.obsidian/` or `20-wiki/`.
    """
    p = Path(start or __file__).resolve()
    for parent in [p, *p.parents]:
        if (parent / ".obsidian").exists() or (parent / "20-wiki").exists():
            return parent
    raise RuntimeError("Could not find vault root (no .obsidian or 20-wiki/ found)")


def sha256_of(path: Path | str) -> str:
    """SHA-256 of a file, streamed in 1 MiB chunks."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
