#!/usr/bin/env python3
"""
LLM cleanup of OCR/converter Markdown via OpenRouter (open-weights → no copyright filter).

FIX-ONLY, language-preserving rewrite: dehyphenate, reflow paragraphs, strip page-number/
running-head noise, fix obvious OCR typos, keep/repair heading + list structure. Preserves
EVERY sentence and the ORIGINAL language (never translates or summarizes).

Runs on OPEN-WEIGHTS models (default from core.openrouter) which, unlike proprietary APIs,
don't block verbatim reproduction — so full-text cleanup of your own material works. Best
run AFTER reflow_ocr.py (deterministic), but works standalone.

A per-chunk fidelity guard compares word counts: a chunk that loses too much (the model
summarized) is retried, then falls back to a deterministic reflow rather than accepting a
lossy rewrite.

Usage:
    llm_clean.py <file.md> [--model <slug>] [--chunk-lines 1500] [--min-keep 0.90] [--out PATH]
Needs OPENROUTER_API_KEY (env or scripts/.env).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# allow running standalone (put scripts/ on sys.path for `core`)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import openrouter
from postprocess import reflow_ocr

SYSTEM = (
    "You turn raw OCR / document-conversion Markdown into an IMPECCABLE Markdown source. "
    "This is FIX-ONLY — repair and structure, never rewrite the author.\n"
    "\n"
    "DO:\n"
    "- Dehyphenate line-wrapped words (e.g. 'capa-\\nble' -> 'capable').\n"
    "- Reflow the per-line OCR fragments into proper flowing paragraphs (one blank line "
    "between paragraphs; never hard-wrap mid-sentence).\n"
    "- Remove OCR noise: standalone page numbers, running headers/footers, stray single "
    "glyphs/marks from diagrams or drop-caps.\n"
    "- Fix obvious OCR typos and spacing.\n"
    "- Add headings ONLY where the text itself marks them (recover, never invent). Use '## ' "
    "for major section/chapter/part titles and '### ' for subsections. Do NOT use '# ' (the "
    "document title lives in the frontmatter). Do NOT turn figure/table captions into "
    "headings. When a line's role is ambiguous, leave it as body text.\n"
    "- Restore lists (use '- ' bullets), tables, and emphasis.\n"
    "- Keep EVERY image reference exactly (lines like '![](./slug/images/page-012-img-1.png)') "
    "and place it inline near the text it belongs to. Do not invent images.\n"
    "\n"
    "HARD RULES: preserve EVERY sentence and idea, in the SAME order. Keep the ORIGINAL "
    "LANGUAGE exactly — NEVER translate, summarize, paraphrase to 'improve' style, reorder, "
    "drop, or add content. Keep the author's exact wording; only repair OCR damage and "
    "structure.\n"
    "Output ONLY the cleaned Markdown — no preface, no reasoning, no explanation, no code fences."
)

_THINK_RE = re.compile(r"<think>.*?</think>", re.S | re.I)


def _clean_output(s: str) -> str:
    """Strip reasoning-model <think> blocks and stray code fences from the response."""
    s = _THINK_RE.sub("", s)
    if "</think>" in s:  # reasoning leaked without an opening tag
        s = s.rsplit("</think>", 1)[1]
    s = s.strip()
    if s.startswith("```"):
        s = s.split("\n", 1)[1] if "\n" in s else ""
        if s.rstrip().endswith("```"):
            s = s.rstrip()[:-3]
    return s.strip()


def _split_frontmatter(text: str) -> tuple[str, str]:
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            nl = text.find("\n", end + 1)
            cut = nl + 1 if nl != -1 else len(text)
            return text[:cut], text[cut:]
    return "", text


def _chunks(body: str, chunk_lines: int) -> list[str]:
    """Blank-line-aligned chunks of ~chunk_lines (never split a paragraph)."""
    lines = body.split("\n")
    out, start = [], 0
    n = len(lines)
    while start < n:
        end = min(start + chunk_lines, n)
        while end < n and lines[end].strip() != "":
            end += 1
        out.append("\n".join(lines[start:end]).strip("\n"))
        start = end
        while start < n and lines[start].strip() == "":
            start += 1
    return [c for c in out if c.strip()]


def clean_chunk(chunk: str, model: str, min_keep: float, max_grow: float) -> str:
    """Clean one chunk, faithfully. The word count must stay within [min_keep, max_grow]×
    input — a drop means it summarized, a spike means it invented content. On failure after
    a retry, fall back to a deterministic reflow (verbatim) rather than trust the model.
    """
    in_words = len(chunk.split())
    msgs = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": chunk}]
    for _ in range(2):
        out = _clean_output(openrouter.chat(msgs, model=model))
        wo = len(out.split())
        if in_words == 0 or (min_keep * in_words <= wo <= max_grow * in_words):
            return out
        drift = "dropped" if wo < min_keep * in_words else "added"
        msgs.append({"role": "assistant", "content": out})
        msgs.append({"role": "user", "content":
            f"You {drift} content ({in_words} words in, {wo} out). Redo — output the FULL text, "
            "every sentence in order; ONLY fix OCR/formatting, never add or remove anything."})
    print(f"  [warn] chunk fell back to deterministic reflow ({in_words}w in — model not faithful)", file=sys.stderr)
    return reflow_ocr.reflow_markdown(chunk).rstrip("\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path)
    ap.add_argument("--model", default=openrouter.DEFAULT_MODEL)
    ap.add_argument("--chunk-lines", type=int, default=1500)
    ap.add_argument("--min-keep", type=float, default=0.90, help="min output/input word ratio to accept a chunk (else reflow)")
    ap.add_argument("--max-grow", type=float, default=1.08, help="max output/input word ratio to accept a chunk (else reflow)")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args(argv)

    text = args.file.read_text(encoding="utf-8")
    fm, body = _split_frontmatter(text)
    chunks = _chunks(body, args.chunk_lines)
    print(f"[llm-clean] {args.file.name}: {len(chunks)} chunk(s) via {args.model}")

    cleaned = []
    for i, ch in enumerate(chunks, 1):
        try:
            cleaned.append(clean_chunk(ch, args.model, args.min_keep, args.max_grow))
        except openrouter.OpenRouterError as e:
            print(f"[error] chunk {i}: {e}", file=sys.stderr)
            return 1
        print(f"  chunk {i}/{len(chunks)} done")

    joined = "\n\n".join(cleaned).strip() + "\n"
    out_text = (fm.rstrip() + "\n\n" + joined) if fm else joined
    (args.out or args.file).write_text(out_text, encoding="utf-8")

    wi, wo = len(text.split()), len(out_text.split())
    print(f"[done] words {wi} -> {wo} ({100 * wo // max(1, wi)}% kept) -> {args.out or args.file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
