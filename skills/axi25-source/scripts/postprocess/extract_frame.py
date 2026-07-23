#!/usr/bin/env python3
"""
Capture one frame from a video at a given timestamp (via the pip-bundled ffmpeg).

Useful for grabbing a diagram/slide a speaker shows on screen, as a sibling image for a
video source. If <output> is omitted, saves `<video>_<timestamp>.png` next to the video.

Usage:
    source.py frame <video> <MM:SS|HH:MM:SS> [output.png]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import media


def parse_timestamp(ts: str) -> str:
    """Normalize MM:SS or HH:MM:SS into HH:MM:SS for ffmpeg -ss."""
    parts = ts.split(":")
    if len(parts) == 2:
        return f"00:{parts[0].zfill(2)}:{parts[1].zfill(2)}"
    if len(parts) == 3:
        return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2].zfill(2)}"
    raise ValueError(f"invalid timestamp: {ts!r} (use MM:SS or HH:MM:SS)")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="source.py frame", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("timestamp", help="MM:SS or HH:MM:SS")
    ap.add_argument("output", type=Path, nargs="?", help="output PNG (default: next to the video)")
    args = ap.parse_args(argv)

    ts = parse_timestamp(args.timestamp)
    out = args.output or args.video.with_name(f"{args.video.stem}_{args.timestamp.replace(':', '-')}.png")

    print(f"[frame] {ts} of {args.video.name} -> {out.name}")
    try:
        media.extract_frame(args.video, ts, out)
    except media.MediaError as e:
        print(f"[error] {e}", file=sys.stderr)
        return 1
    print(f"[done] {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
