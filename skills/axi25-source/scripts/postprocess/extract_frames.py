#!/usr/bin/env python3
"""
Capture many frames from a video (via the pip-bundled ffmpeg). Pure-Python replacement
for the old bash `extract_frames.sh` — Windows-safe, no host ffmpeg.

Modes:
    source.py frames <video> uniform <count>     # <count> frames evenly across the video
    source.py frames <video> at <MM:SS,MM:SS,…>  # one frame per given timestamp

Frames land in `<video_stem>_frames/frame-NNN.png` next to the source.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import media
from postprocess.extract_frame import parse_timestamp


def _hms(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="source.py frames", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video", type=Path)
    ap.add_argument("mode", choices=["uniform", "at"])
    ap.add_argument("param", help="count (uniform) or comma-separated timestamps (at)")
    args = ap.parse_args(argv)

    out_dir = args.video.with_name(f"{args.video.stem}_frames")
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "uniform":
        try:
            count = int(args.param)
        except ValueError:
            print(f"[error] uniform needs an integer count, got {args.param!r}", file=sys.stderr)
            return 1
        try:
            dur = media.duration_seconds(args.video)
        except media.MediaError as e:
            print(f"[error] {e}", file=sys.stderr)
            return 1
        stamps = [_hms(dur * (i + 1) / (count + 1)) for i in range(count)]
    else:  # at
        stamps = [parse_timestamp(t.strip()) for t in args.param.split(",") if t.strip()]

    written = 0
    for i, ts in enumerate(stamps, 1):
        dst = out_dir / f"frame-{i:03d}.png"
        try:
            media.extract_frame(args.video, ts, dst)
            written += 1
            print(f"[frame] {ts} -> {dst.name}")
        except media.MediaError as e:
            print(f"[warn] {ts}: {e}", file=sys.stderr)

    print(f"[done] {written}/{len(stamps)} frames -> {out_dir}/")
    return 0 if written else 1


if __name__ == "__main__":
    sys.exit(main())
