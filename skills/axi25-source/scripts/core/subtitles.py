"""Timestamp + SRT + paragraph builders from timestamped cues/segments. Stdlib only.

A cue/segment is a dict {"start","end","text"} (whisper/openrouter) OR a tuple
(start, end, text). Every transcript → text transform lives here — mechanical and
verbatim (only spacing/paragraph breaks, never word changes). Shared by the stream
and audio handlers so there is ONE implementation of each.
"""
from __future__ import annotations

import re
from typing import Iterable, Union

Cue = Union[dict, tuple]

_END_PUNCT = re.compile(r"[.!?…]$")


def _unpack(cue: Cue) -> tuple[float, float, str]:
    if isinstance(cue, dict):
        return float(cue["start"]), float(cue["end"]), (cue.get("text") or "").strip()
    start, end, text = cue
    return float(start), float(end), (text or "").strip()


def hms(seconds: float) -> str:
    """Human timestamp: HH:MM:SS, or MM:SS under an hour."""
    s = int(seconds or 0)
    h, rem = divmod(s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def srt_timestamp(seconds: float) -> str:
    """SRT timestamp: HH:MM:SS,mmm."""
    if seconds < 0:
        seconds = 0.0
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(cues: Iterable[Cue]) -> str:
    lines: list[str] = []
    for idx, cue in enumerate(cues, 1):
        start, end, text = _unpack(cue)
        if not text:
            continue
        if end <= start:
            end = start + 0.5
        lines.append(str(idx))
        lines.append(f"{srt_timestamp(start)} --> {srt_timestamp(end)}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines)


def build_txt(cues: Iterable[Cue], gap_threshold: float = 2.0,
              hard_gap: float = 3.0, max_sentences: int = 8) -> str:
    """Readable paragraphs from cues. New paragraph on a long pause (`hard_gap`), on a
    shorter pause after a finished sentence (`gap_threshold`), or after `max_sentences`.

    Verbatim — only paragraph breaks + spacing (fidelity rule). Timestamps dropped.
    """
    paragraphs: list[list[str]] = [[]]
    sentences = 0
    prev_end: float | None = None
    prev_text = ""
    for cue in cues:
        start, end, text = _unpack(cue)
        if not text:
            continue
        if paragraphs[-1] and prev_end is not None:
            gap = start - prev_end
            ends = bool(_END_PUNCT.search(prev_text))
            if gap > hard_gap or (gap > gap_threshold and ends) or (sentences >= max_sentences and ends):
                paragraphs.append([])
                sentences = 0
        paragraphs[-1].append(text)
        if _END_PUNCT.search(text):
            sentences += 1
        prev_end, prev_text = end, text
    return "\n\n".join(" ".join(p) for p in paragraphs if p) + "\n"


def speaker_blocks(segments: Iterable[dict]) -> str:
    """Diarized segments → `[HH:MM:SS] SPEAKER_NN: text` blocks (consecutive same-speaker merged)."""
    blocks: list[tuple[float, str, str]] = []
    speaker: str | None = None
    parts: list[str] = []
    start = 0.0
    for seg in segments:
        spk = seg.get("speaker") or "UNKNOWN"
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        if spk == speaker and parts:
            parts.append(text)
        else:
            if parts:
                blocks.append((start, speaker or "UNKNOWN", " ".join(parts)))
            speaker, parts, start = spk, [text], seg.get("start") or 0.0
    if parts:
        blocks.append((start, speaker or "UNKNOWN", " ".join(parts)))
    return "\n\n".join(f"[{hms(st)}] {sp}: {tx}" for st, sp, tx in blocks)
