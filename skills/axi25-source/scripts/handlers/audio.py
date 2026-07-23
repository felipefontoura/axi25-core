#!/usr/bin/env python3
"""
Transcribe local audio/video into clean text — cloud-first via OpenRouter STT.

  default     : OpenRouter STT (openai/whisper-large-v3) → SRT + clean txt
  --diarize   : diarization-capable STT (x-ai/grok-stt-1.0) → speaker-labelled SRT + "[Name]: …" txt
  --batch     : transcribe every media file in a directory

Long audio is chunked (16 kHz mono, < 25 MB/request) and timestamps re-offset — see
core.transcribe. Artifacts land NEXT TO the source file (portable). Map SPEAKER_NN → real
names yourself after diarization.

Source acquisition only — never writes to 20-wiki/ (that is axi25-ingest).

Usage:
    source.py audio "Cap 1.mp4" --lang pt
    source.py audio meeting.m4a --diarize --num-speakers 3
    source.py audio ~/Courses/lecture-series --batch --lang pt
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# allow running this handler standalone (put scripts/ on sys.path for `core`)
import sys as _sys, pathlib as _pathlib
_sys.path.insert(0, str(_pathlib.Path(__file__).resolve().parent.parent))

from core import subtitles, transcribe

_MEDIA_EXTS = {".mp3", ".m4a", ".wav", ".flac", ".ogg", ".opus", ".aac",
               ".mp4", ".mov", ".mkv", ".avi", ".webm", ".wmv", ".flv"}


def _write_outputs(base: Path, segments: list, fmt: str) -> list[Path]:
    written: list[Path] = []
    if fmt in ("srt", "both"):
        p = base.with_suffix(".srt")
        p.write_text(subtitles.build_srt(segments), encoding="utf-8")
        written.append(p)
    if fmt in ("txt", "both"):
        p = base.with_suffix(".txt")
        p.write_text(subtitles.build_txt(segments), encoding="utf-8")
        written.append(p)
    return written


def run_single(src: Path, args) -> int:
    t0 = time.time()
    try:
        result = transcribe.transcribe(src, language=args.lang, model=args.model, chunk_seconds=args.chunk)
    except transcribe.TranscribeError as e:
        print(f"[stt] {e}", file=sys.stderr)
        print("      Set OPENROUTER_API_KEY in scripts/.env — https://openrouter.ai/keys")
        return 1
    written = _write_outputs(args.out or src, result["segments"], args.format)
    print(f"[done] {len(result['segments'])} cues in {time.time() - t0:.0f}s -> {' + '.join(str(p) for p in written)}")
    return 0


def run_diarize(src: Path, args) -> int:
    try:
        segments = transcribe.transcribe_diarized(
            src, language=args.lang, model=args.diarize_model,
            num_speakers=args.num_speakers, chunk_seconds=args.chunk,
        )
    except transcribe.TranscribeError as e:
        print(f"[stt] {e}", file=sys.stderr)
        return 1
    stem = src.with_suffix("")
    (Path(f"{stem}.srt")).write_text(subtitles.build_srt(segments), encoding="utf-8")
    (Path(f"{stem}_speakers.txt")).write_text(subtitles.speaker_blocks(segments), encoding="utf-8")
    speakers = sorted({s.get("speaker") for s in segments if s.get("speaker")})
    print(f"\n[done] diarized ({len(speakers)} speakers: {', '.join(speakers)}) -> {stem}.srt + {stem}_speakers.txt")
    print("       Map SPEAKER_NN → real names in the .txt.")
    return 0


def run_batch(base_dir: Path, args) -> int:
    files = sorted(f for f in base_dir.rglob("*") if f.suffix.lower() in _MEDIA_EXTS)
    if not files:
        print(f"[error] no media files under {base_dir}")
        return 1
    print(f"[batch] {len(files)} files\n")
    done = skipped = 0
    for f in files:
        txt = f.with_suffix(".txt")
        if txt.exists():
            print(f"[skip] {f.name} — .txt exists")
            skipped += 1
            continue
        print(f"[{done + 1}] {f.relative_to(base_dir)}")
        try:
            result = transcribe.transcribe(f, language=args.lang, model=args.model, chunk_seconds=args.chunk)
            txt.write_text(subtitles.build_txt(result["segments"]), encoding="utf-8")
            done += 1
        except transcribe.TranscribeError as e:
            print(f"  error: {e}", file=sys.stderr)
    print(f"\n[batch done] {done} transcribed, {skipped} skipped")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="source.py audio", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("input", type=Path, help="Audio/video file, or a directory (with --batch)")
    p.add_argument("--diarize", action="store_true", help="Multi-speaker: diarization-capable STT")
    p.add_argument("--batch", action="store_true", help="Transcribe every media file under a directory")
    p.add_argument("--num-speakers", type=int, default=None, help="Speaker count hint for diarization")
    p.add_argument("--lang", default=None, help="Language hint (ISO-639-1, e.g. pt, en). Auto if omitted.")
    p.add_argument("--model", default=transcribe.DEFAULT_MODEL, help="OpenRouter STT model")
    p.add_argument("--diarize-model", default=transcribe.DEFAULT_DIARIZE_MODEL, help="OpenRouter diarization-capable STT model")
    p.add_argument("--chunk", type=float, default=600.0, help="Chunk length in seconds (keep each chunk < 25 MB)")
    p.add_argument("--format", choices=["srt", "txt", "both"], default="both", help="output format(s)")
    p.add_argument("--out", type=Path, default=None, help="output path base (default: next to source)")
    args = p.parse_args(argv)

    src = args.input.expanduser().resolve()

    if args.batch or src.is_dir():
        if not src.is_dir():
            print(f"[error] --batch needs a directory: {src}", file=sys.stderr)
            return 1
        return run_batch(src, args)

    if not src.is_file():
        print(f"[error] not found: {src}", file=sys.stderr)
        return 1

    return run_diarize(src, args) if args.diarize else run_single(src, args)


if __name__ == "__main__":
    sys.exit(main())
