#!/usr/bin/env python3
"""
Deterministic OCR/markdown cleanup — dehyphenate, reflow paragraphs, strip noise.

Turns raw converter output (OCR flat text: per-line breaks, hyphenated wraps, standalone
page numbers, running-head debris) into clean flowing Markdown, one paragraph per line
(the vault convention — 10-sources disables MD013). Preserves YAML frontmatter, headings,
lists, and diagram/exhibit fragment blocks verbatim.

This is the mechanical half of the acquisition fix-pass. It is DETERMINISTIC (no LLM, no
content-filter risk on copyrighted text) and idempotent.

Usage:
    reflow_ocr.py <file.md>            # rewrite in place
    reflow_ocr.py <file.md> --out <p>  # write elsewhere
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_LIST_RE = re.compile(r'^\s*([-*+]|\d+[.)])\s+')


def _split_frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter_including_fences, rest). Empty frontmatter if none."""
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            nl = text.find("\n", end + 1)
            cut = nl + 1 if nl != -1 else len(text)
            return text[:cut], text[cut:]
    return "", text


def _blocks(body: str) -> list[list[str]]:
    out, cur = [], []
    for ln in body.split("\n"):
        if ln.strip() == "":
            if cur:
                out.append(cur)
                cur = []
        else:
            cur.append(ln)
    if cur:
        out.append(cur)
    return out


def _is_heading(b): return b[0].lstrip().startswith("#")
def _is_list(b): return all(_LIST_RE.match(x) for x in b)
def _is_pagenum(b): return len(b) == 1 and re.fullmatch(r'[\divxlcIVXLC|.\-—~ ]{1,6}', b[0].strip() or "x") is not None


def _fragmented(b: list[str]) -> bool:
    """Diagram/exhibit debris: several very short lines, little sentence punctuation.

    Prose is hard-wrapped at ~70-80 chars, so real paragraphs have long lines; debris has
    short ones. A hyphenation wrap (a line ending in '-') is a clear prose signal.
    """
    if len(b) < 4 or any(x.rstrip().endswith("-") for x in b):
        return False
    lens = sorted(len(x.strip()) for x in b)
    med = lens[len(lens) // 2]
    joined = " ".join(x.strip() for x in b)
    punct = joined.count(".") + joined.count("?") + joined.count(":")
    return med < 22 and punct <= max(1, len(b) // 5)


def _reflow(b: list[str]) -> str:
    out = ""
    for x in b:
        s = x.strip()
        if not s:
            continue
        if out.endswith("-") and s[:1].islower():
            out = out[:-1] + s          # dehyphenate line-wrap
        elif out:
            out = out + " " + s
        else:
            out = s
    return out


def reflow_markdown(text: str) -> str:
    fm, body = _split_frontmatter(text)
    res = []
    for b in _blocks(body):
        if _is_pagenum(b):
            continue                    # drop standalone page numbers / rule debris
        if _is_heading(b) or _is_list(b) or _fragmented(b):
            res.append("\n".join(b))    # keep verbatim
        else:
            res.append(_reflow(b))      # reflow prose into one paragraph
    joined = "\n\n".join(res).strip() + "\n"
    return (fm.rstrip() + "\n\n" + joined) if fm else joined


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)

    text = args.file.read_text(encoding="utf-8")
    out = reflow_markdown(text)
    (args.out or args.file).write_text(out, encoding="utf-8")

    wi, wo = len(text.split()), len(out.split())
    print(f"[reflow] words {wi} -> {wo} ({100 * wo // max(1, wi)}% kept), "
          f"lines {text.count(chr(10)) + 1} -> {out.count(chr(10)) + 1}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
