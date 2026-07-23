#!/usr/bin/env python3
"""
source.py — the single entrypoint of the axi25-source acquisition layer.

Turn ANY raw media (local disk OR https/internet) into clean, faithful Markdown in
10-sources/ (or 50-zeitgeist/ for podcasts/cuts), ready for axi25-ingest. Cloud-first:
pip packages + one OpenRouter API key, no heavy local ML.

    source.py <input> [handler flags]      # auto-detect from path/URL
    source.py <format> <input> [flags]     # force a format

Formats (each maps to a handler in handlers/):

    book     .pdf / .epub file            → PyMuPDF (+ vision OCR for scans) / markdownify
    article  web URL (article/paper/thread) → trafilatura (local-first)
    stream   any yt-dlp URL               → yt-dlp + OpenRouter STT (+ diarization)
    audio    local audio/video file/dir   → OpenRouter STT (+ diarization)

Post-processing utilities (mechanical / cheap — delegated to postprocess/):

    source.py reflow <file.md>            → deterministic dehyphenate + reflow (free)
    source.py llm-clean <file.md> …       → LLM fix-only cleanup (OpenRouter open-weights)
    source.py frame <video> <ts> …        → capture one frame (pip ffmpeg)
    source.py frames <video> <mode> <p>   → capture many frames (pip ffmpeg)

Acquisition only — this NEVER writes to 20-wiki/ (that is axi25-ingest).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

_HERE = Path(__file__).resolve().parent
_LIB = _HERE / "postprocess"

FORMATS = {"book", "article", "stream", "audio"}

AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".flac", ".ogg", ".opus", ".aac",
              ".mp4", ".mov", ".mkv", ".avi", ".webm", ".wmv", ".flv"}
BOOK_EXTS = {".pdf", ".epub"}
TEXT_EXTS = {".txt", ".md", ".markdown"}

# Hosts auto-routed to the stream handler. yt-dlp itself supports ~1800 sites — this list
# only covers the unambiguous media platforms so bare `source.py <url>` auto-detects them.
STREAM_HOSTS = (
    "youtube.com", "youtu.be", "youtube-nocookie.com",
    "vimeo.com", "twitch.tv", "dailymotion.com", "dai.ly",
    "soundcloud.com", "tiktok.com", "rumble.com", "bilibili.com",
    "odysee.com", "fb.watch", "streamable.com", "loom.com",
)

# utility subcommand → postprocess script (all Python now — no shell scripts)
UTILITIES = {
    "reflow": "reflow_ocr.py",
    "llm-clean": "llm_clean.py",
    "frame": "extract_frame.py",
    "frames": "extract_frames.py",
}


def _is_url(s: str) -> bool:
    return s.startswith(("http://", "https://"))


def detect(target: str) -> str | None:
    """Return the handler format for an input string, or None if undetectable."""
    if _is_url(target):
        host = (urlparse(target).netloc or "").lower().removeprefix("www.")
        if any(host == h or host.endswith("." + h) for h in STREAM_HOSTS):
            return "stream"
        if urlparse(target).path.lower().endswith(".pdf"):
            return "pdf-url"  # special: needs local download first
        return "article"

    p = Path(target).expanduser()
    ext = p.suffix.lower()
    if p.is_dir():
        return "audio"  # only dir-based acquisition is batch transcription
    if ext in BOOK_EXTS:
        return "book"
    if ext in AUDIO_EXTS:
        return "audio"
    if ext in TEXT_EXTS:
        return "text"
    return None


def dispatch(fmt: str, argv: list[str]) -> int:
    if fmt == "book":
        from handlers import book
        return book.main(argv)
    if fmt == "article":
        from handlers import article
        return article.main(argv)
    if fmt == "stream":
        from handlers import stream
        return stream.main(argv)
    if fmt == "audio":
        from handlers import audio
        return audio.main(argv)
    raise ValueError(f"unknown format: {fmt}")


def run_utility(name: str, argv: list[str]) -> int:
    path = _LIB / UTILITIES[name]
    return subprocess.call([sys.executable, str(path), *argv])


def main() -> int:
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0

    head = argv[0]

    if head in FORMATS:
        return dispatch(head, argv[1:])
    if head in UTILITIES:
        return run_utility(head, argv[1:])

    fmt = detect(head)
    if fmt == "text":
        print(f"[info] '{head}' is already text — nothing to acquire.")
        print("       Feed it to axi25-ingest directly (it produces the wiki, not a source).")
        return 0
    if fmt == "pdf-url":
        print(f"[info] '{head}' points to a PDF.")
        print("       Download it, then: source.py book /path/to/file.pdf")
        print("       (papers convert far better from the real PDF than from an HTML abstract.)")
        return 2
    if fmt is None:
        print(f"[error] could not detect a format for: {head}")
        print("        Force one: source.py <book|article|stream|audio> <input> [flags]")
        return 1

    return dispatch(fmt, argv)


if __name__ == "__main__":
    sys.exit(main())
