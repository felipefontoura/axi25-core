"""Vision OCR client — a scanned page image → faithful Markdown, via OpenRouter.

Replaces docling + tesseract for the scanned/bad-text-layer PDF path. Renders happen in
book.py (PyMuPDF, local, light); this sends each page PNG to an OPEN-WEIGHT vision model
(default google/gemma-4-31b-it) so verbatim reproduction of copyrighted pages is NOT
blocked by moderation (`is_moderated: false` in the catalog).

FIX-ONLY: transcribe what's on the page, recover reading order + structure, never
summarize, translate, or invent. Same fidelity contract as core.openrouter's cleanup.
"""
from __future__ import annotations

import base64
from pathlib import Path

from . import openrouter

DEFAULT_MODEL = "google/gemma-4-31b-it"

# prose mode — a page of a scanned/garbled BOOK: linear reading order is the right structure.
_SYSTEM_PROSE = (
    "You are an OCR + layout engine. Transcribe the page image into faithful Markdown.\n"
    "DO: output every word exactly as printed, in reading order; recover paragraphs, "
    "headings ('## ' for section/chapter titles, '### ' for subsections — never '# '), "
    "lists ('- '), and tables. Keep the ORIGINAL language.\n"
    "DO NOT: translate, summarize, paraphrase, add, drop, or reorder content. Do not "
    "describe the image. Ignore running headers/footers and standalone page numbers.\n"
    "Output ONLY the Markdown — no preface, no explanation, no code fences."
)

# design mode — a COMPLEX VISUAL DESIGN (slide, mind map, infographic, diagram): the meaning
# lives in the 2D layout, not in reading order. Reconstruct the information architecture.
_SYSTEM_DESIGN = (
    "You are converting a COMPLEX VISUAL DESIGN (a slide, mind map, infographic, diagram, or "
    "poster) into structured Markdown. The meaning is in the LAYOUT — position, grouping, arrows, "
    "hierarchy, columns — NOT in left-to-right reading order. Reconstruct the INFORMATION "
    "ARCHITECTURE the design conveys:\n"
    "- The main title → '## '. Named groups/sections → '### ' or bold.\n"
    "- A timeline or process → an ordered/sequential list, in the intended order.\n"
    "- A mind map or hierarchy → NESTED bullet lists mirroring the branches.\n"
    "- Columns / quadrants → separate sections, each in its own logical order.\n"
    "- Connections / arrows → state them explicitly (e.g. 'A → B').\n"
    "- A chart or pictogram → one short line naming what it shows, then any data labels verbatim.\n"
    "Transcribe ALL text VERBATIM in its original language — never invent, translate, or summarize "
    "the words; only organize them by the structure the layout implies. Ignore purely decorative "
    "icons. Output ONLY the Markdown — no preface, no explanation, no code fences."
)


class VisionError(RuntimeError):
    """Raised on OCR failures."""


def _data_uri(image_path: Path) -> str:
    ext = image_path.suffix.lower().lstrip(".") or "png"
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def ocr_image(image_path: Path | str, *, model: str = DEFAULT_MODEL,
              language_hint: str | None = None, mode: str = "prose") -> str:
    """OCR one page image into Markdown. `mode`: "prose" (book page, linear) or "design"
    (slide / mind map / infographic — reconstruct the information architecture).
    Raises VisionError on failure.
    """
    image_path = Path(image_path)
    if not image_path.is_file():
        raise VisionError(f"image not found: {image_path}")
    system = _SYSTEM_DESIGN if mode == "design" else _SYSTEM_PROSE
    user_text = ("Convert this complex visual design to structured Markdown."
                 if mode == "design" else "Transcribe this page to faithful Markdown.")
    if language_hint:
        user_text += f" The text is in {language_hint}."
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": [
            {"type": "text", "text": user_text},
            {"type": "image_url", "image_url": {"url": _data_uri(image_path)}},
        ]},
    ]
    try:
        out = openrouter.chat(messages, model=model)
    except openrouter.OpenRouterError as e:
        raise VisionError(str(e)) from e
    out = out.strip()
    if out.startswith("```"):
        out = out.split("\n", 1)[1] if "\n" in out else ""
        if out.rstrip().endswith("```"):
            out = out.rstrip()[:-3]
    return out.strip()
