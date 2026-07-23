"""FFmpeg helpers — via the pip-provided static binary (imageio-ffmpeg), never a host tool.

This is what keeps the skill "pip + one key": no system ffmpeg/ffprobe required. yt-dlp is
pointed at this same binary (ffmpeg_location = ffmpeg_dir()). Duration is parsed from
ffmpeg's own stderr (we don't ship ffprobe).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


class MediaError(RuntimeError):
    """Raised when the ffmpeg step fails."""


def ffmpeg_exe() -> str:
    """Absolute path to the pip-bundled ffmpeg binary. Requires `imageio-ffmpeg`."""
    try:
        import imageio_ffmpeg
    except ImportError as e:  # pragma: no cover - dependency guard
        raise MediaError(
            "imageio-ffmpeg not installed — run setup.sh (audio/stream need it)."
        ) from e
    return imageio_ffmpeg.get_ffmpeg_exe()


def ffmpeg_dir() -> str:
    """Directory holding the ffmpeg binary — pass to yt-dlp as `ffmpeg_location`."""
    return str(Path(ffmpeg_exe()).parent)


_DUR_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)")


def duration_seconds(path: Path) -> float:
    """Media duration in seconds, parsed from ffmpeg's stderr banner (no ffprobe needed)."""
    proc = subprocess.run(
        [ffmpeg_exe(), "-i", str(path)],
        capture_output=True, text=True,
    )
    m = _DUR_RE.search(proc.stderr or "")
    if not m:
        raise MediaError(f"could not read duration of {path}")
    h, mnt, sec = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return h * 3600 + mnt * 60 + sec


def extract_chunk(src: Path, start: float, length: float, dst: Path) -> None:
    """Extract [start, start+length) as 16 kHz mono 32 kbps mp3 (tiny upload, well < 25 MB)."""
    proc = subprocess.run(
        [ffmpeg_exe(), "-y", "-ss", f"{start:.3f}", "-t", f"{length:.3f}",
         "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", "-b:a", "32k", str(dst)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise MediaError(f"ffmpeg chunk failed: {(proc.stderr or '')[:300]}")


def extract_frame(src: Path, timestamp: str, dst: Path, quality: int = 2) -> None:
    """Capture one frame at `timestamp` (HH:MM:SS) as a PNG/JPG (by dst suffix)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [ffmpeg_exe(), "-ss", timestamp, "-i", str(src),
         "-frames:v", "1", "-q:v", str(quality), "-y", str(dst)],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise MediaError(f"ffmpeg frame failed: {(proc.stderr or '')[:300]}")
