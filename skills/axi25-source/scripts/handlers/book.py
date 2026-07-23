#!/usr/bin/env python3
"""
Acquire a book (PDF or epub) as raw source Markdown in 10-sources/books/<author>/.

Cloud-first, pip-only pipelines (no docling / tesseract / pandoc required):

  .pdf  digital → PyMuPDF text extraction + figure references          source_kind: pdf-book
  .pdf  scanned → PyMuPDF page render → OpenRouter open-weight vision OCR
  .epub          → stdlib OPF/spine parse + markdownify (pure Python)    source_kind: epub-book

Digital-vs-scanned is auto-detected from the embedded text density (override with --scan
/ --no-ocr). The binary stays OUTSIDE the vault; only original_path + sha256 are registered.
Cover + real figures land in a sibling dir (<slug>/).

Source acquisition only — never writes to 20-wiki/ (that is axi25-ingest).

Usage:
    source.py book /path/book.pdf
    source.py book /path/book.pdf --author addy-osmani --slug beyond-vibe-coding
    source.py book /path/scanned.pdf --scan               # force vision OCR
    source.py book /path/book.epub --class-map "chap-title=1,sect-title=2"
    source.py book <file> --library ~/Documents/library --force
"""
from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import sys
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

# allow running this handler standalone (put scripts/ on sys.path for `core`)
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from core import frontmatter, sha256_of, slugify, today, vault_root
from core import vision


# --------------------------------------------------------------------------- #
# shared                                                                       #
# --------------------------------------------------------------------------- #


def _relocate_binary(src: Path, library: Path | None, author_slug: str, book_slug: str, ext: str) -> Path:
    if library is None:
        return src
    library = library.expanduser().resolve()
    target = library / author_slug / f"{book_slug}{ext}"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.resolve() == src.resolve():
        return target
    if target.exists() and sha256_of(target) == sha256_of(src):
        print(f"[library] already present: {target}")
        return target
    print(f"[library] copying to: {target}")
    shutil.copy2(src, target)
    return target


_ROMAN_OR_ARABIC_RE = re.compile(r"^\*\*[ivxlcdm\d]{1,5}\*\*\s*$", re.M | re.I)


def _looks_garbled(sample: str) -> bool:
    """A corrupt embedded text layer (glyph-substitution OCR) mixes non-Latin scripts (CJK,
    stray glyphs) into otherwise Latin prose — e.g. this PDF's 'Copyriglzt @ 2003', '儿1into'.
    If a meaningful fraction of the letters aren't Latin, the text layer is untrustworthy →
    prefer vision OCR over extracting garbage. (False-positives only on genuinely CJK books,
    which are rare here and can be forced with --no-ocr.)
    """
    letters = [c for c in sample if c.isalpha()]
    if len(letters) < 200:
        return False
    non_latin = sum(1 for c in letters if "LATIN" not in unicodedata.name(c, ""))
    # A clean Latin (en/pt) book measures ~0.0-0.05% non-Latin letters; a glyph-substitution
    # corrupt layer injects stray CJK/Greek among the wrong-latin garble (Minto ≈ 0.68%).
    # 0.3% cleanly separates them. Cost asymmetry favours sensitivity: a false positive just
    # OCRs an already-clean book; a false negative ships garbage.
    return non_latin / len(letters) > 0.003


def _looks_like_design(doc, pages: int = 6) -> bool:
    """A page whose meaning lives in its 2D LAYOUT, not in reading order — a slide, mind map,
    infographic, diagram, or poster. Signalled by SPARSE text that is either scattered into many
    short blocks or laid out on landscape pages. Prose books are the opposite: dense, portrait,
    a few long paragraph blocks. For these, linear text extraction loses the meaning → vision
    in 'design' mode reconstructs the information architecture.
    """
    n = min(pages, doc.page_count)
    if n == 0:
        return False
    landscape = scattered = total_chars = 0
    for i in range(n):
        p = doc.load_page(i)
        if p.rect.width > p.rect.height * 1.1:
            landscape += 1
        blocks = [b[4] for b in p.get_text("blocks") if len(b) > 4 and b[4].strip()]
        total_chars += sum(len(b) for b in blocks)
        if blocks:
            avg = sum(len(b) for b in blocks) / len(blocks)
            if len(blocks) >= 6 and avg < 120:  # many short runs = scattered, not paragraphs
                scattered += 1
    cpp = total_chars / n
    return cpp < 700 and (landscape >= n * 0.6 or scattered >= n * 0.6)


def _structural_clean(body: str) -> str:
    """Post-process converter output (deterministic, fidelity-preserving):
    demote spammy repeated headings to bold, merge split same-level headings, drop
    standalone bold page numbers, collapse blank runs.
    """
    heads = re.findall(r"^##\s+(.+?)$", body, re.M)
    spam = {h for h, c in Counter(heads).items() if c >= 3 and len(h) < 40}
    if spam:
        pattern = r"^##\s+(" + "|".join(map(re.escape, spam)) + r")\s*$"
        body = re.sub(pattern, r"**\1**", body, flags=re.M)
    for _ in range(3):
        new_body = re.sub(r"^(#{1,6})\s+(.+?)\n+\1\s+(.+?)$", r"\1 \2 \3", body, flags=re.M)
        if new_body == body:
            break
        body = new_body
    body = _ROMAN_OR_ARABIC_RE.sub("", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()


# --------------------------------------------------------------------------- #
# PDF pipeline (PyMuPDF + optional vision OCR)                                 #
# --------------------------------------------------------------------------- #


def _pdf_extract_meta(doc) -> dict:
    meta = doc.metadata or {}
    return {
        "title": (meta.get("title") or "").strip(),
        "author": (meta.get("author") or "").strip(),
        "subject": (meta.get("subject") or "").strip(),
        "keywords": (meta.get("keywords") or "").strip(),
        "page_count": doc.page_count,
    }


def _pdf_render_cover(doc, target: Path, dpi: int = 100) -> None:
    import fitz  # pymupdf

    if doc.page_count == 0:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    page = doc.load_page(0)
    zoom = dpi / 72.0
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    pix.save(str(target))


def _extract_page_figures(doc, page, i, images_dir, seen, slug, min_image_px, page_cover_ratio):
    """Extract real embedded figures from a page (deduped by xref). Returns list of md refs."""
    page_area = page.rect.width * page.rect.height
    refs: list[str] = []
    for img in page.get_images(full=True):
        xref = img[0]
        if xref in seen:
            continue
        seen.add(xref)
        data = doc.extract_image(xref)
        if data.get("width", 0) < min_image_px or data.get("height", 0) < min_image_px:
            continue  # decorative speck / rule / bullet
        try:  # skip full-page scans (a figure is a region, not the whole page)
            bbox = page.get_image_bbox(img)
            if bbox.is_valid and page_area and (bbox.width * bbox.height) >= page_cover_ratio * page_area:
                continue
        except Exception:
            pass
        fname = f"page-{i + 1:03d}-img-{xref}.{data['ext']}"
        (images_dir / fname).write_bytes(data["image"])
        refs.append(f"![](./{slug}/images/{fname})")
    return refs


def _pdf_text(doc, artifacts_dir: Path, slug: str, min_image_px: int, page_cover_ratio: float) -> tuple[str, int]:
    """Digital PDF: PyMuPDF text extraction per page + figure references. Deterministic."""
    images_dir = artifacts_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    seen: set[int] = set()
    image_count = 0
    blocks: list[str] = []
    for i in range(doc.page_count):
        page = doc.load_page(i)
        text = (page.get_text("text") or "").strip()
        refs = _extract_page_figures(doc, page, i, images_dir, seen, slug, min_image_px, page_cover_ratio)
        image_count += len(refs)
        block = "\n\n".join(chunk for chunk in (text, "\n".join(refs)) if chunk)
        if block:
            blocks.append(block)
    return "\n\n".join(blocks), image_count


def _pdf_vision(doc, artifacts_dir: Path, slug: str, dpi: int, model: str, lang: str | None,
                min_image_px: int, page_cover_ratio: float, mode: str = "prose") -> tuple[str, int]:
    """Render each page (PyMuPDF) → OpenRouter open-weight vision OCR + figures. `mode`:
    "prose" (scanned/garbled book) or "design" (slide/mind-map/infographic — reconstruct layout)."""
    import tempfile

    images_dir = artifacts_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    seen: set[int] = set()
    image_count = 0
    blocks: list[str] = []
    n = doc.page_count
    with tempfile.TemporaryDirectory() as td:
        page_png = Path(td) / "page.png"
        for i in range(n):
            page = doc.load_page(i)
            page.get_pixmap(dpi=dpi).save(str(page_png))
            try:
                text = vision.ocr_image(page_png, model=model, language_hint=lang, mode=mode).strip()
            except vision.VisionError as e:
                print(f"[ocr] page {i + 1}: vision failed ({e}); leaving blank", file=sys.stderr)
                text = ""
            refs = _extract_page_figures(doc, page, i, images_dir, seen, slug, min_image_px, page_cover_ratio)
            image_count += len(refs)
            block = "\n\n".join(chunk for chunk in (text, "\n".join(refs)) if chunk)
            if block:
                blocks.append(block)
            if (i + 1) % 10 == 0 or i + 1 == n:
                print(f"[ocr] page {i + 1}/{n} ({image_count} figures)")
    return "\n\n".join(blocks), image_count


def _pdf_derive_slugs(meta: dict, pdf_path: Path) -> tuple[str, str]:
    author_slug = slugify(meta.get("author") or "") or "unknown"
    book_slug = slugify(meta.get("title") or "") or slugify(pdf_path.stem) or "untitled"
    return author_slug, book_slug


def _write_book_md(md_path, kind, title, author, author_slug, book_slug, page_count,
                   image_count, original_path, sha, body, cover_present, extra_meta=None) -> None:
    meta = {
        "type": "source",
        "source_kind": kind,
        "title": title,
        "author": author,
        "author_slug": author_slug,
        "book_slug": book_slug,
        "page_count": page_count or None,
        "image_count": image_count or None,
        "acquired": today(),
        "original_path": str(original_path),
        "sha256": sha,
    }
    if extra_meta:
        meta.update(extra_meta)
    header = [f"# {title}", ""]
    if cover_present:
        header += [f"![[{book_slug}/cover.jpg]]", ""]
    bullets = [f"- Author: {author}"]
    if page_count:
        bullets.append(f"- Pages: {page_count}")
    bullets += [f"- Source: `{original_path}`", f"- SHA-256: `{sha}`"]
    header += bullets
    md_path.write_text(frontmatter.document(meta, body, header=header), encoding="utf-8")


def run_pdf(args, pdf_path: Path) -> int:
    import fitz  # pymupdf

    print(f"[meta] reading: {pdf_path}")
    doc = fitz.open(str(pdf_path))
    pdf_meta = _pdf_extract_meta(doc)

    auto_author, auto_slug = _pdf_derive_slugs(pdf_meta, pdf_path)
    author_slug = args.author or auto_author
    book_slug = args.slug or auto_slug

    library = Path(args.library) if args.library else None
    final_pdf_path = _relocate_binary(pdf_path, library, author_slug, book_slug, ".pdf")

    target_dir = vault_root() / "10-sources" / "books" / author_slug
    sibling_dir = target_dir / book_slug
    md_path = target_dir / f"{book_slug}.md"
    print(f"[target] {md_path}")

    if md_path.exists() and not args.force:
        print("[skip] outputs already exist (use --force to re-run)")
        doc.close()
        return 0

    target_dir.mkdir(parents=True, exist_ok=True)
    sibling_dir.mkdir(parents=True, exist_ok=True)

    sha = sha256_of(final_pdf_path)
    cover_path = sibling_dir / "cover.jpg"
    cover_ok = True
    try:
        _pdf_render_cover(doc, cover_path, dpi=args.cover_dpi)
    except Exception as e:
        cover_ok = False
        print(f"[warn] cover render failed: {e}")

    # Decide the extraction path. Vision wins when the text layer is unusable (sparse scan OR
    # garbled glyph-substitution) OR when the page is a complex DESIGN (slide/mind-map/infographic
    # — meaning is in the layout, not reading order). Otherwise plain text extraction (free).
    sample = "".join((doc.load_page(i).get_text("text") or "") for i in range(min(doc.page_count, 10)))
    chars_per_page = len(sample) / max(1, min(doc.page_count, 10))
    sparse = chars_per_page < 100
    garbled = _looks_garbled(sample)
    design = (not args.no_design) and _looks_like_design(doc)

    if args.design:
        path, mode = "vision", "design"
    elif args.scan:
        path, mode = "vision", "prose"
    elif args.no_ocr:
        path, mode = "text", None
    elif design:
        path, mode = "vision", "design"
        print("[detect] complex visual design (slides / mind-map / infographic) → vision (design mode)")
    elif sparse or garbled:
        path, mode = "vision", "prose"
        why = "sparse text layer" if sparse else "garbled text layer (glyph substitution)"
        print(f"[detect] {why} → vision OCR (use --no-ocr to force text extraction)")
    else:
        path, mode = "text", None

    if path == "vision":
        min_px = 300 if mode == "design" else 64  # design: skip decorative icons, keep real figures
        print(f"[markdown] vision OCR ({mode}) via {args.vision_model} (render @{args.ocr_dpi}dpi)...")
        body, image_count = _pdf_vision(
            doc, sibling_dir, book_slug, dpi=args.ocr_dpi, model=args.vision_model,
            lang=args.lang, min_image_px=min_px, page_cover_ratio=0.8, mode=mode,
        )
    else:
        print("[markdown] digital PDF → PyMuPDF text extraction...")
        body, image_count = _pdf_text(doc, sibling_dir, book_slug, min_image_px=64, page_cover_ratio=0.8)

    doc.close()
    body = _structural_clean(body)
    print(f"[markdown] {len(body):,} chars, {image_count} figures extracted")

    title = pdf_meta.get("title") or book_slug.replace("-", " ").title()
    author = pdf_meta.get("author") or author_slug.replace("-", " ").title()
    _write_book_md(
        md_path, "pdf-book", title, author, author_slug, book_slug, pdf_meta.get("page_count", 0),
        image_count, final_pdf_path, sha, body, cover_ok,
        extra_meta={"subject": pdf_meta.get("subject") or None, "keywords": pdf_meta.get("keywords") or None},
    )
    print(f"\n[done] {md_path}\n       {sibling_dir}/")
    print("       Run `source.py reflow` (+ optional `llm-clean`), then lint-check before ingesting.")
    return 0


# --------------------------------------------------------------------------- #
# epub pipeline (stdlib OPF + markdownify; optional pandoc)                    #
# --------------------------------------------------------------------------- #

OPF_NS = {
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
    "cnt": "urn:oasis:names:tc:opendocument:xmlns:container",
}


def _epub_read_opf_path(zf: zipfile.ZipFile) -> str:
    container = zf.read("META-INF/container.xml")
    root = ET.fromstring(container)
    rootfile = root.find(".//cnt:rootfiles/cnt:rootfile", OPF_NS)
    if rootfile is None or not rootfile.get("full-path"):
        raise RuntimeError("epub container.xml has no rootfile path")
    return rootfile.get("full-path")


def _epub_parse_opf(zf: zipfile.ZipFile, opf_path: str) -> dict:
    root = ET.fromstring(zf.read(opf_path))
    base = str(Path(opf_path).parent)

    def _resolve(href: str) -> str:
        return str(Path(base, href)).lstrip("/") if base != "." else href

    title = (root.findtext(".//dc:title", default="", namespaces=OPF_NS) or "").strip()
    author = (root.findtext(".//dc:creator", default="", namespaces=OPF_NS) or "").strip()
    language = (root.findtext(".//dc:language", default="", namespaces=OPF_NS) or "").strip()

    manifest: dict[str, tuple[str, str, str]] = {}
    for item in root.findall(".//opf:manifest/opf:item", OPF_NS):
        manifest[item.get("id")] = (
            _resolve(item.get("href", "")),
            item.get("media-type", ""),
            item.get("properties", "") or "",
        )

    spine: list[str] = []
    for itemref in root.findall(".//opf:spine/opf:itemref", OPF_NS):
        idref = itemref.get("idref")
        if idref in manifest and manifest[idref][1] in ("application/xhtml+xml", "text/html"):
            spine.append(manifest[idref][0])

    cover_href = None
    for meta in root.findall(".//opf:metadata/opf:meta", OPF_NS):
        if meta.get("name") == "cover" and meta.get("content") in manifest:
            cover_href = manifest[meta.get("content")][0]
            break
    if cover_href is None:
        for _id, (href, mtype, props) in manifest.items():
            if "cover-image" in props and mtype.startswith("image/"):
                cover_href = href
                break

    return {"title": title, "author": author, "language": language, "spine": spine, "cover_href": cover_href}


def _epub_extract_cover(zf: zipfile.ZipFile, cover_href: str, sibling_dir: Path) -> bool:
    try:
        data = zf.read(cover_href)
    except KeyError:
        return False
    ext = Path(cover_href).suffix.lower() or ".jpg"
    sibling_dir.mkdir(parents=True, exist_ok=True)
    (sibling_dir / f"cover{ext}").write_bytes(data)
    if ext != ".jpg":
        (sibling_dir / "cover.jpg").write_bytes(data)
    return True


def _parse_class_map(spec: str | None) -> dict[str, int]:
    if not spec:
        return {}
    out: dict[str, int] = {}
    for pair in spec.split(","):
        pair = pair.strip()
        if not pair:
            continue
        cls, _, lvl = pair.partition("=")
        cls, lvl = cls.strip(), lvl.strip()
        if cls and lvl.isdigit() and 1 <= int(lvl) <= 6:
            out[cls] = int(lvl)
        else:
            sys.exit(f"[error] bad --class-map entry: {pair!r} (expected class=level, level 1-6)")
    return out


def _apply_class_map(xhtml: str, class_map: dict[str, int]) -> str:
    """Rewrite <p class="X">…</p> (and <div>) into <hN>…</hN> for mapped classes. Deterministic."""
    for cls, lvl in class_map.items():
        pattern = re.compile(
            rf'<(p|div)\b[^>]*\bclass="[^"]*\b{re.escape(cls)}\b[^"]*"[^>]*>(.*?)</\1>',
            re.S | re.I,
        )

        def _sub(m: re.Match) -> str:
            inner = re.sub(r"<[^>]+>", " ", m.group(2))
            inner = re.sub(r"\s+", " ", html.unescape(inner)).strip()
            return f"<h{lvl}>{inner}</h{lvl}>"

        xhtml = pattern.sub(_sub, xhtml)
    return xhtml


def _html_to_md(html_text: str, use_pandoc: bool) -> str:
    """XHTML → GFM Markdown. Default: markdownify (pure Python). Optional: pandoc if requested + present."""
    if use_pandoc and shutil.which("pandoc"):
        proc = subprocess.run(
            ["pandoc", "-f", "html", "-t", "gfm-raw_html", "--wrap=none"],
            input=html_text.encode("utf-8"), capture_output=True,
        )
        if proc.returncode == 0:
            return proc.stdout.decode("utf-8")
        print(f"[warn] pandoc failed ({proc.stderr.decode('utf-8', 'replace')[:200]}); using markdownify")
    from markdownify import markdownify as md_convert

    return md_convert(html_text, heading_style="ATX", strip=["script", "style"])


_OVER_ESCAPE_RE = re.compile(r"\\([.\-_#>*\[\]()'\"|~`])")
_ORPHAN_PAGENUM_RE = re.compile(r"^\*{0,2}[ivxlcdm\d]{1,5}\*{0,2}\s*$", re.M | re.I)
_IMG_LINE_RE = re.compile(r"^\s*!\[[^\]]*\]\([^)]*\)\s*$", re.M)
_SVG_RE = re.compile(r"<svg\b.*?</svg>", re.S | re.I)


def _epub_structural_clean(body: str, strip_images: bool) -> tuple[str, int]:
    """Structural cleanup only (fidelity rule). Returns (clean_body, images_stripped)."""
    body = body.replace(" ", " ")
    for ch in ("​", "‌", "‍", "﻿"):
        body = body.replace(ch, "")
    body = _SVG_RE.sub("", body)
    body = _OVER_ESCAPE_RE.sub(r"\1", body)
    body = _ORPHAN_PAGENUM_RE.sub("", body)
    images_stripped = 0
    if strip_images:
        images_stripped = len(_IMG_LINE_RE.findall(body))
        body = _IMG_LINE_RE.sub("", body)
    body = re.sub(r"(\w)-\n(\w)", r"\1\2", body)
    body = re.sub(r"[ \t]+\n", "\n", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip(), images_stripped


def run_epub(args, epub_path: Path) -> int:
    class_map = _parse_class_map(args.class_map)

    print(f"[meta] reading: {epub_path}")
    with zipfile.ZipFile(epub_path) as zf:
        opf_path = _epub_read_opf_path(zf)
        meta = _epub_parse_opf(zf, opf_path)

        author = meta["author"] or "Unknown"
        author_slug = args.author or slugify(meta["author"]) or "unknown"
        book_slug = args.slug or slugify(meta["title"]) or slugify(epub_path.stem) or "untitled"

        library = Path(args.library) if args.library else None
        final_epub_path = _relocate_binary(epub_path, library, author_slug, book_slug, ".epub")

        target_dir = vault_root() / "10-sources" / "books" / author_slug
        sibling_dir = target_dir / book_slug
        md_path = target_dir / f"{book_slug}.md"
        print(f"[target] {md_path}")

        if md_path.exists() and not args.force:
            print("[skip] outputs already exist (use --force to re-run)")
            return 0

        target_dir.mkdir(parents=True, exist_ok=True)
        sha = sha256_of(final_epub_path)

        cover_ok = False
        if meta["cover_href"]:
            cover_ok = _epub_extract_cover(zf, meta["cover_href"], sibling_dir)

        print(f"[markdown] converting via {'pandoc' if args.pandoc else 'markdownify'} (class-map={class_map or 'none'})...")
        chunks = []
        for href in meta["spine"]:
            try:
                xhtml = zf.read(href).decode("utf-8", "replace")
            except KeyError:
                continue
            if class_map:
                xhtml = _apply_class_map(xhtml, class_map)
            chunks.append(_html_to_md(xhtml, use_pandoc=args.pandoc))
        body = "\n\n".join(chunks)

    body, images_stripped = _epub_structural_clean(body, strip_images=not args.keep_images)
    print(f"[markdown] {len(body):,} chars, {images_stripped} image lines stripped")

    title = meta.get("title") or book_slug.replace("-", " ").title()
    note = "primary source — epub→md (markdownify), verbatim; structural cleanup only. Ingest via axi25-ingest."
    _write_book_md(
        md_path, "epub-book", title, author, author_slug, book_slug, None, None,
        final_epub_path, sha, body, cover_ok,
        extra_meta={"lang": meta["language"] or None, "note": note},
    )
    print(f"\n[done] {md_path}\n       {sibling_dir}/")
    print("       lint-check the .md and read the diff before ingesting (green lint != structure preserved).")
    return 0


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="source.py book", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("file", help="Path to the .pdf or .epub file")
    p.add_argument("--author", help="Author slug (default: from file metadata)")
    p.add_argument("--slug", help="Book slug (default: from title or filename)")
    p.add_argument("--library", help="External directory to copy the binary into (outside the vault)")
    p.add_argument("--force", action="store_true", help="Re-run even if outputs exist")
    p.add_argument("--lang", default=None, help="Language hint for vision OCR (e.g. pt, en)")
    # PDF-only
    p.add_argument("--scan", action="store_true", help="[pdf] Force vision OCR, prose mode (scanned/bad-text-layer)")
    p.add_argument("--design", action="store_true", help="[pdf] Force vision OCR, design mode (slides/mind-maps/infographics)")
    p.add_argument("--no-design", action="store_true", help="[pdf] Disable auto design-layout detection")
    p.add_argument("--no-ocr", action="store_true", help="[pdf] Never OCR — text extraction only")
    p.add_argument("--vision-model", default=vision.DEFAULT_MODEL, help="[pdf] OpenRouter open-weight vision model for OCR")
    p.add_argument("--ocr-dpi", type=int, default=200, help="[pdf] Render DPI for vision OCR (default: 200)")
    p.add_argument("--cover-dpi", type=int, default=100, help="[pdf] Cover render DPI (default: 100)")
    # epub-only
    p.add_argument("--class-map", help='[epub] CSS class→heading recovery, e.g. "chap-title=1,sect-title=2"')
    p.add_argument("--keep-images", action="store_true", help="[epub] Keep image reference lines (default strips them)")
    p.add_argument("--pandoc", action="store_true", help="[epub] Use pandoc if present (optional upgrade over markdownify)")
    args = p.parse_args(argv)

    path = Path(args.file).expanduser().resolve()
    if not path.is_file():
        print(f"[error] file not found: {path}")
        return 1

    ext = path.suffix.lower()
    if ext == ".pdf":
        return run_pdf(args, path)
    if ext == ".epub":
        return run_epub(args, path)
    print(f"[error] unsupported book format: {ext} (expected .pdf or .epub)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
