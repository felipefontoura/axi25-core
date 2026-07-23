#!/usr/bin/env python3
"""
Acquire a web article / paper / thread as raw source Markdown into the vault.

Local-first pipeline (pure Python, no key, no host tool):
  URL → trafilatura (fetch + readability extraction + metadata) → Markdown →
  contract frontmatter → 10-sources/{articles,papers,posts}/<slug>.md

trafilatura strips boilerplate (nav/ads/cookie-banners/related) and outputs clean
Markdown with title/author/date metadata.

JS-gated pages: trafilatura's plain fetch can't run JavaScript. When a page comes back
empty, render it (browser Save-As full HTML, or a browser-automation tool) and pass the
file via --html; extraction runs on that.

Source acquisition only — never writes to 20-wiki/ (that is axi25-ingest).

Usage:
    source.py article https://example.com/post
    source.py article https://arxiv.org/abs/1234.5678 --kind paper
    source.py article https://example.com/post --slug my-slug --author jane-doe
    source.py article https://example.com/post --html rendered.html   # rendered-HTML fallback
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

# allow running this handler standalone (put scripts/ on sys.path for `core`)
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from core import frontmatter, slugify, today, vault_root

# destination dir (under 10-sources/) per source_kind
_KIND_DIR = {
    "article": "articles",
    "paper": "papers",
    "thread": "posts",
    "talk": "articles",
}


def slug_from_url(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    tail = path.rsplit("/", 1)[-1] if path else ""
    tail = re.sub(r"\.(html?|php|aspx?)$", "", tail, flags=re.I)
    return slugify(tail) or slugify(urlparse(url).netloc)


def get_content(url: str, html_file: Path | None) -> str | None:
    if html_file is not None:
        return html_file.read_text(encoding="utf-8", errors="replace")
    from trafilatura import fetch_url

    return fetch_url(url)


def extract(downloaded: str) -> dict:
    """Return {title, author, date, sitename, lang, text(markdown)}.

    Uses the high-level trafilatura API: extract() for the Markdown body + extract_metadata()
    for title/author/date (trafilatura 2.x — bare_extraction's markdown path returns empty).
    """
    from trafilatura import extract as _extract, extract_metadata

    text = _extract(
        downloaded,
        output_format="markdown",
        include_comments=False,
        include_tables=True,
        favor_precision=True,
    ) or ""

    meta = extract_metadata(downloaded)

    def g(attr: str) -> str:
        v = getattr(meta, attr, None) if meta else None
        return v.strip() if isinstance(v, str) else (v or "")

    return {
        "title": g("title"),
        "author": g("author"),
        "date": g("date"),
        "sitename": g("sitename"),
        "lang": g("language"),
        "text": text.strip(),
    }


def write_md(md_path: Path, url: str, kind: str, meta: dict, author_slug: str, body: str) -> None:
    title = meta.get("title") or md_path.stem.replace("-", " ").title()
    author = meta.get("author") or ""

    note = (
        "primary source — local extraction via trafilatura (readability + markdown). "
        "Boilerplate removed (nav/ads/related); verbatim text. Ingest via axi25-ingest."
    )

    fm_meta = {
        "type": "source",
        "source_kind": kind,
        "title": title,
        "author": author or None,
        "author_slug": author_slug or None,
        "lang": meta.get("lang") or None,
        "site": meta.get("sitename") or None,
        "published": meta.get("date") or None,
        "acquired": today(),
        "original_path": url,
        "note": note,
    }
    header = [f"# {title}", "", f"> Source: <{url}>"]
    md_path.write_text(frontmatter.document(fm_meta, body, header=header), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="source.py article",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("url", help="Article URL")
    p.add_argument("--kind", choices=list(_KIND_DIR), default="article",
                   help="source_kind: article (default) | paper | thread | talk")
    p.add_argument("--slug", help="Output slug (default: from title, else from URL)")
    p.add_argument("--author", help="Author slug override")
    p.add_argument("--html", type=Path, help="Pre-rendered HTML file (fallback for JS-gated pages)")
    p.add_argument("--force", action="store_true", help="Overwrite existing output")
    args = p.parse_args(argv)

    html_file = args.html.expanduser().resolve() if args.html else None
    if html_file is not None and not html_file.is_file():
        print(f"[error] --html file not found: {html_file}")
        return 1

    print(f"[fetch] {args.url}" + (f" (from {html_file.name})" if html_file else ""))
    downloaded = get_content(args.url, html_file)
    if not downloaded:
        print("[error] fetch returned nothing. The page may be JS-gated or blocking bots.")
        print("        Fallback: render it (browser Save-As Webpage Complete), then re-run with --html.")
        return 2

    print("[extract] trafilatura (readability + markdown)...")
    meta = extract(downloaded)
    if not meta or not meta.get("text"):
        print("[error] extraction found no article body.")
        print("        Check the raw HTML for a paywall / lead-gate / display:none content.")
        return 3

    slug = args.slug or slugify(meta.get("title", "")) or slug_from_url(args.url)
    author_slug = args.author or slugify(meta.get("author", ""))

    target_dir = vault_root() / "10-sources" / _KIND_DIR[args.kind]
    md_path = target_dir / f"{slug}.md"
    print(f"[target] {md_path}")

    if md_path.exists() and not args.force:
        print("[skip] output already exists (use --force to overwrite)")
        return 0

    target_dir.mkdir(parents=True, exist_ok=True)
    write_md(md_path, args.url, args.kind, meta, author_slug, meta["text"])

    words = len(meta["text"].split())
    print(f"[done] {md_path}  (~{words} words)")
    print("       lint-check the .md before ingesting — confirm no paywall stub / truncation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
