# Model choices — chosen by bake-off, not by taste

> Every OpenRouter model default in this skill was picked by testing candidates on the SAME real
> input and comparing quality vs cost. The rule: cheapest model that isn't beaten on the task.
> Re-run the bake-offs when the catalog shifts. Prices are $/M tokens (prompt·completion) unless noted.

## Decisions

| Task | Default | Why (evidence) |
|---|---|---|
| **STT** (transcription) | `openai/whisper-large-v3` | 6/6 phrase-fidelity on a pt clip, 7 segments, ~$0.0015/min. Deepgram-nova3 costs 3× AND was less accurate (5/6 — missed "Poços de Caldas"). Ultra-cheap `qwen3-asr-flash` / `gpt-4o-mini-transcribe` **reject `verbose_json`** → no timestamps/segments. Mid-price whisper is the sweet spot. |
| **Vision OCR — prose** (scanned/garbled books) | `google/gemma-4-31b-it` | Byte-for-byte the same clean output as `qwen3.6-35b` and `qwen3.6-27b` (5× pricier) on a garbled Minto page. Cheapest wins outright. Open-weight → verbatim reproduction of copyrighted pages isn't filter-blocked. |
| **Vision OCR — design** (slides/mind-maps/infographics) | `google/gemma-4-31b-it` | **Best** of the set on a culture-deck timeline: correct `##`/`###`, nested year→events, and it noted the dashed-line connections. `qwen3.6-27b` (5×) came out worse (flat `###`, wrong `#`, no connections); `gemini-3.5-flash-lite` translated a section label. |
| **llm-clean** (fix-only text cleanup) | `google/gemma-4-31b-it` | 99% word-fidelity, dehyphenates, rebuilds headings — tied with `qwen3.6-35b`/`27b`. Cheapest, and unifies with the vision path (one model). |
| **Diarization** (speaker split; optional name inference) | `google/gemini-3.5-flash-lite` (default, cost) · `google/gemini-3.5-flash` (for names) | flash-lite separates the 2 speakers well at ~12× less than flash, but returns `00=?` (no names). flash was the ONLY tested model to also **infer the name** ("Felipe") from the dialogue. `voxtral-small-24b` (open-weight) **collapsed both speakers into one** — rejected. Default is flash-lite (user's cost call); use `--diarize-model google/gemini-3.5-flash` when speaker names matter. |

## The one real cost/quality trade-off — diarization

Diarization is the only non-trivial cost. Default `gemini-3.5-flash-lite` ≈ **fractions of a cent**
(~$0.40 for a 3 h podcast) and separates speakers, but does not name them. When names matter, pass
`--diarize-model google/gemini-3.5-flash` ≈ **$0.03 per 2 min** (~$5 for a 3 h podcast) — it infers
speaker names from the dialogue. Everything else (STT, vision, cleanup) is already fractions of a cent.

## How to re-run a bake-off

Render/clip the same real input, run each candidate, score on task-specific checks (phrase fidelity
for STT/diarization, structure + connections for design, word-count kept for cleanup), divide by the
catalog price. Prefer open-weight for anything reproducing copyrighted text (`is_moderated: false`).
