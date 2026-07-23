"""OpenRouter speech-to-text client. Stdlib + ffmpeg-pip only.

Replaces the local Whisper / whisperx / pyannote / Groq stack with cloud STT behind the
ONE OpenRouter key. Handles arbitrarily long audio by chunking (each chunk re-encoded to
16 kHz mono mp3 to stay well under the 25 MB request cap), then offsets timestamps back
to absolute time. Returns a whisper-compatible shape: {"text","language","model","segments"}.

Two entry points:
  - transcribe()          plain single-stream STT (reference video / cut / lecture)
  - transcribe_diarized() speaker-labelled STT via a diarization-capable model
                          (default x-ai/grok-stt-1.0). Segments carry a "speaker" field.

NOTE: the diarization response shape is provider-specific. This parses the common
`verbose_json` layout and looks for a per-segment speaker under a few likely keys; if the
provider returns none, it degrades to a single UNKNOWN speaker (and says so) rather than
failing. Adjust `_speaker_of` if a provider labels speakers differently.
"""
from __future__ import annotations

import base64
import json
import re
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from . import media, openrouter
from .envkeys import resolve as resolve_key

URL = "https://openrouter.ai/api/v1/audio/transcriptions"
DEFAULT_MODEL = "openai/whisper-large-v3"
# Diarization does NOT come through OpenRouter's /audio/transcriptions endpoint (the OpenAI schema
# has no speaker field). We diarize via an AUDIO-CAPABLE CHAT model that labels turns by prompt.
# Default = flash-lite (user's cost call, see references/models.md): separates speakers well at ~12×
# less than flash, but usually does NOT infer speaker NAMES. For name inference, pass
# --diarize-model google/gemini-3.5-flash. Still one OpenRouter key.
DEFAULT_DIARIZE_MODEL = "google/gemini-3.5-flash-lite"
_MAX_UPLOAD = 24 * 1024 * 1024  # keep under OpenRouter's 25 MB cap


class TranscribeError(RuntimeError):
    """Raised on unrecoverable STT failures."""


def _multipart(audio: Path, model: str, language: str | None, extra: dict[str, str]) -> tuple[bytes, str]:
    boundary = f"----axi25Boundary{uuid.uuid4().hex}"
    parts: list[bytes] = [
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{audio.name}"\r\n'.encode(),
        b"Content-Type: audio/mpeg\r\n\r\n",
        audio.read_bytes(),
        b"\r\n",
    ]
    fields = [("model", model), ("response_format", "verbose_json"), ("temperature", "0")]
    if language and language != "auto":
        fields.append(("language", language))
    fields.extend(extra.items())
    for field, value in fields:
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{field}"\r\n\r\n{value}\r\n'.encode())
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), boundary


def _post(audio: Path, key: str, model: str, language: str | None, extra: dict[str, str]) -> dict[str, Any]:
    body, boundary = _multipart(audio, model, language, extra)
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "X-Title": "axi25-source",
        "Accept": "application/json",
    }
    for attempt in range(1, 6):
        req = urllib.request.Request(URL, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=600) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", "replace")
            if e.code in (408, 429, 500, 502, 503, 529) and attempt < 5:
                wait = 5 * attempt
                print(f"[stt] HTTP {e.code} ({attempt}/5); sleeping {wait}s")
                time.sleep(wait)
                continue
            raise TranscribeError(f"HTTP {e.code}: {err[:400]}") from e
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < 5:
                time.sleep(5 * attempt)
                continue
            raise TranscribeError(f"network error after 5 attempts: {e}") from e
    raise TranscribeError("exhausted retries")


def _speaker_of(seg: dict) -> str | None:
    for key in ("speaker", "speaker_id", "speaker_label", "channel"):
        v = seg.get(key)
        if v is not None and v != "":
            return f"SPEAKER_{v}" if str(v).isdigit() else str(v)
    return None


def _chunk_and_post(audio_path: Path, key: str, model: str, language: str | None,
                    extra: dict[str, str], chunk_seconds: float) -> list[dict[str, Any]]:
    """Split the audio into chunks, POST each, return segments with absolute timestamps."""
    src = Path(audio_path)
    if not src.exists():
        raise TranscribeError(f"audio not found: {src}")
    duration = media.duration_seconds(src)
    n_chunks = max(1, int(duration // chunk_seconds) + (1 if duration % chunk_seconds else 0))
    tmp_dir = src.parent / f".{src.stem}.stt_tmp"
    tmp_dir.mkdir(exist_ok=True)

    segments: list[dict[str, Any]] = []
    try:
        for i in range(n_chunks):
            start = i * chunk_seconds
            length = min(chunk_seconds, duration - start)
            chunk = tmp_dir / f"chunk_{i:03d}.mp3"
            media.extract_chunk(src, start, length, chunk)
            if chunk.stat().st_size > _MAX_UPLOAD:
                raise TranscribeError(
                    f"chunk {i} is {chunk.stat().st_size} bytes (> 25 MB) — lower --chunk"
                )
            print(f"[stt] chunk {i + 1}/{n_chunks} ({start:.0f}-{start + length:.0f}s) via {model}...")
            data = _post(chunk, key, model, language, extra)
            for seg in data.get("segments") or []:
                text = (seg.get("text") or "").strip()
                if not text:
                    continue
                out = {
                    "start": start + float(seg.get("start") or 0.0),
                    "end": start + float(seg.get("end") or 0.0),
                    "text": text,
                }
                spk = _speaker_of(seg)
                if spk:
                    out["speaker"] = spk
                segments.append(out)
            chunk.unlink(missing_ok=True)
    finally:
        try:
            tmp_dir.rmdir()
        except OSError:
            pass
    return segments


def transcribe(audio_path: Path | str, *, language: str | None = None,
               model: str = DEFAULT_MODEL, chunk_seconds: float = 600.0,
               key: str | None = None) -> dict[str, Any]:
    """Plain single-stream transcription. Returns a whisper-shaped dict."""
    key = key or resolve_key("OPENROUTER_API_KEY")
    if not key:
        raise TranscribeError("OPENROUTER_API_KEY not set (env or scripts/.env)")
    segments = _chunk_and_post(Path(audio_path), key, model, language, {}, chunk_seconds)
    return {
        "text": " ".join(s["text"] for s in segments),
        "language": language,
        "model": model,
        "segments": segments,
    }


_TURN_RE = re.compile(r"^\[?SPEAKER[_ ]?(\d+)\]?\s*:?\s*(.*)$", re.I)
_LEGEND_RE = re.compile(r"^\s*SPEAKERS?\s*:\s*(.+)$", re.I)
_UNKNOWN = {"", "?", "??", "unknown", "unknwon", "desconhecido", "n/a", "na", "-"}

_DIARIZE_SYSTEM = (
    "You are a speech diarization + transcription engine. Transcribe VERBATIM in the original "
    "language — never summarize, translate, or paraphrase. Attribute every utterance to a speaker."
)


def _diarize_prompt(language: str | None, num_speakers: int | None) -> str:
    who = f"exactly {num_speakers} speakers" if num_speakers else "two or more speakers"
    lang = f" in {language}" if language else ""
    return (
        f"Transcribe this audio{lang}. It has {who}.\n"
        "Identify each distinct speaker and INFER their real name from the dialogue — people "
        "address each other by name (one says 'Aline...', later that person calls the other "
        "'Felipe', so you learn two names). Use a name ONLY when the audio makes it clear; leave "
        "it unknown otherwise.\n"
        "Output EXACTLY this and nothing else:\n"
        "- First line: `SPEAKERS: 00=<name or ?>, 01=<name or ?>` (one entry per speaker index).\n"
        "- Then the transcript: each turn on its own line prefixed `[SPEAKER_00]:`, `[SPEAKER_01]:` "
        "(same indices), merging consecutive turns by the same speaker. Verbatim, original language."
    )


def _parse_legend(line: str) -> dict[int, str | None]:
    """Parse a 'SPEAKERS: 00=Felipe, 01=?' legend into {index: name-or-None}."""
    names: dict[int, str | None] = {}
    for pair in line.split(","):
        if "=" not in pair:
            continue
        idx, name = pair.split("=", 1)
        idx = re.sub(r"[^0-9]", "", idx)
        name = name.strip()
        if idx.isdigit():
            names[int(idx)] = None if name.lower() in _UNKNOWN else name
    return names


def _parse_diarized(text: str) -> tuple[list[tuple[str, str]], dict[int, str | None]]:
    """Parse the model's output into (turns, names). Turns are (label, text) where label is the
    resolved real name when known, else SPEAKER_NN. `names` maps index → inferred name (or None).
    """
    names: dict[int, str | None] = {}
    raw: list[tuple[int, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        lg = _LEGEND_RE.match(line)
        if lg and not raw:  # legend precedes the transcript
            names = _parse_legend(lg.group(1))
            continue
        m = _TURN_RE.match(line)
        if m:
            raw.append((int(m.group(1)), m.group(2).strip()))
        elif raw:  # a wrapped continuation of the previous turn
            raw[-1] = (raw[-1][0], (raw[-1][1] + " " + line).strip())
    turns = [((names.get(idx) or f"SPEAKER_{idx:02d}"), t) for idx, t in raw if t]
    return turns, names


def transcribe_diarized(audio_path: Path | str, *, language: str | None = None,
                        model: str = DEFAULT_DIARIZE_MODEL, num_speakers: int | None = None,
                        chunk_seconds: float = 600.0, key: str | None = None) -> list[dict[str, Any]]:
    """Speaker-labelled transcription via an audio-capable CHAT model. Returns segments with a
    `speaker` field. Per-turn timestamps are ESTIMATED within each chunk (distributed by text
    length) — the audio-chat path returns labelled turns, not word timings.

    Speaker identity is stable within a chunk; across chunks it is approximate (each chunk is
    diarized independently). Raise --chunk so a short file fits one request for stable identity.
    """
    key = key or resolve_key("OPENROUTER_API_KEY")
    if not key:
        raise TranscribeError("OPENROUTER_API_KEY not set (env or scripts/.env)")
    src = Path(audio_path)
    if not src.exists():
        raise TranscribeError(f"audio not found: {src}")

    duration = media.duration_seconds(src)
    n_chunks = max(1, int(duration // chunk_seconds) + (1 if duration % chunk_seconds else 0))
    tmp_dir = src.parent / f".{src.stem}.diar_tmp"
    tmp_dir.mkdir(exist_ok=True)

    segments: list[dict[str, Any]] = []
    try:
        for i in range(n_chunks):
            start = i * chunk_seconds
            length = min(chunk_seconds, duration - start)
            chunk = tmp_dir / f"chunk_{i:03d}.mp3"
            media.extract_chunk(src, start, length, chunk)
            if chunk.stat().st_size > _MAX_UPLOAD:
                raise TranscribeError(f"chunk {i} is {chunk.stat().st_size} bytes (> 25 MB) — lower --chunk")
            b64 = base64.b64encode(chunk.read_bytes()).decode("ascii")
            messages = [
                {"role": "system", "content": _DIARIZE_SYSTEM},
                {"role": "user", "content": [
                    {"type": "text", "text": _diarize_prompt(language, num_speakers)},
                    {"type": "input_audio", "input_audio": {"data": b64, "format": "mp3"}},
                ]},
            ]
            print(f"[diarize] chunk {i + 1}/{n_chunks} ({start:.0f}-{start + length:.0f}s) via {model}...")
            try:
                out = openrouter.chat(messages, model=model, max_tokens=16384)
            except openrouter.OpenRouterError as e:
                raise TranscribeError(str(e)) from e
            turns, names = _parse_diarized(out)
            named = {f"SPEAKER_{i:02d}": n for i, n in names.items() if n}
            if named:
                print("[diarize]   inferred names: " + ", ".join(f"{k}→{v}" for k, v in sorted(named.items())))
            total = sum(len(t) for _, t in turns) or 1
            acc = 0.0
            for spk, txt in turns:
                seg_start = start + (acc / total) * length
                acc += len(txt)
                segments.append({"start": seg_start, "end": start + (acc / total) * length,
                                 "text": txt, "speaker": spk})
            chunk.unlink(missing_ok=True)
    finally:
        try:
            tmp_dir.rmdir()
        except OSError:
            pass

    if not segments:
        raise TranscribeError("diarization returned no speaker turns")
    return segments
