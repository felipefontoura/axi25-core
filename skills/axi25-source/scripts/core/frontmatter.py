"""One YAML frontmatter serializer (was string-concat json.dumps across many files).

Uses PyYAML (a real serializer) instead of hand-built `f"key: {json.dumps(v)}"` lines.
Correct quoting/escaping/unicode for free.
"""
from __future__ import annotations

from typing import Any

import yaml


def dump(meta: dict[str, Any]) -> str:
    """Serialize a dict into a `---`-fenced YAML frontmatter block (order preserved)."""
    body = yaml.safe_dump(
        {k: v for k, v in meta.items() if v is not None},
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=4096,
    ).rstrip("\n")
    return f"---\n{body}\n---\n"


def document(meta: dict[str, Any], body: str, header: list[str] | None = None) -> str:
    """Assemble a full source note: frontmatter + optional header lines + body.

    `header` is raw markdown lines placed between frontmatter and the `---` separator
    (e.g. `# Title`, a cover embed, a source URL line).
    """
    parts = [dump(meta).rstrip("\n")]
    if header:
        parts += ["", *header]
    parts += ["", "---", "", body.rstrip() + "\n"]
    return "\n".join(parts)
