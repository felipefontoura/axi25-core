---
name: axi25-source
description: >
  Cloud-first source acquisition: turn ANY raw media (local file OR https URL) into clean,
  faithful Markdown in 10-sources/ (or 50-zeitgeist/ for podcasts/cuts), ready for
  axi25-ingest. One CLI (scripts/source.py) auto-detects source x format and dispatches to
  four handlers: book (PDF via PyMuPDF, scanned PDF via open-weight vision OCR, epub via
  markdownify), article (web/paper/thread via trafilatura), stream (any yt-dlp URL +
  OpenRouter transcription, with zeitgeist routing), audio (local audio/video → OpenRouter
  STT + diarization). Runs on pip packages + ONE OpenRouter API key — no heavy local ML.
  Triggers on any acquisition intent: "turn this into a source", "import this into the
  vault", "acquire this source", "import this book/PDF/epub", "ingest <url>", "transcribe
  this video/podcast/audio", "diarize", or a dropped file / pasted URL. Source acquisition
  ONLY — never writes to 20-wiki/ (that is axi25-ingest).
compatibility: >
  Requires an OpenRouter API key (OPENROUTER_API_KEY) and internet access. First use runs
  scripts/setup.sh (needs uv; creates an isolated venv with light pip deps — no ML models,
  no host tools). Optional offline accelerators if on PATH: tesseract (scanned-PDF OCR),
  pandoc (epub).
metadata:
  version: "2.0"
---

# axi25-source (cloud-first acquisition)

One job for the whole layer: **raw media → clean, faithful Markdown in `10-sources/`** (or
`50-zeitgeist/` for podcast-episodes/cuts), ready for `axi25-ingest`. Read the contract once:
`references/contract.md` (frontmatter schema, `source_kind` table, fidelity rule, binary policy).

## The two layers (say them out loud before acting)

```
  ACQUISITION (this skill)    raw media → faithful Markdown in 10-sources/
      ▼  handoff (separate invocation, human checkpoint)
  INGESTION  (axi25-ingest)   Markdown → wiki (DES) + zeitgeist signals
```

Acquisition NEVER interprets, summarizes, scouts signals, or writes to `20-wiki/`. It produces
the verbatim seed and stops.

## One CLI, one key, no heavy ML

Everything lives in `scripts/`, with its own `.venv`. **The only requirement is an OpenRouter
API key** — it powers transcription, diarization, vision OCR, and llm-clean. No torch, no
docling, no whisper models, no host ffmpeg/tesseract/pandoc. Setup once:

```bash
cd .claude/skills/axi25-source/scripts && ./setup.sh     # macOS/Linux (uv)
#                                          ./setup.ps1    # Windows (PowerShell)
```

Put the key in `scripts/.env`: `OPENROUTER_API_KEY=...`. If setup is missing when the user asks
to acquire something, offer to run it (or hand off to `axi25-doctor`) — don't fail silently.

Run from the scripts dir; auto-detect handles source × format:

```bash
uv run python source.py <input> [flags]        # auto-detect
uv run python source.py <format> <input> …     # force a format
```

## Dispatch (what `source.py` decides)

| Input signal | Format | Engine / output |
|--------------|--------|-----------------|
| `.pdf` / `.epub` file | **book** | PyMuPDF (digital) · open-weight vision OCR (scanned) · markdownify (epub) → `10-sources/books/<author>/<slug>.md` |
| web URL (article/paper/thread) | **article** | trafilatura (local, no key) → `10-sources/{articles,papers,posts}/<slug>.md` |
| any yt-dlp URL | **stream** | yt-dlp + OpenRouter STT → `10-sources/videos/reference/` or `50-zeitgeist/podcasts/` |
| local audio/video file (or dir) | **audio** | OpenRouter STT (+ diarization) → transcript next to source |
| URL ending `.pdf` | (guidance) | download it, then `source.py book <file>` — the real PDF beats an HTML abstract |
| pasted long-form text | (guidance) | already text → `axi25-ingest` directly |

Ambiguous (a 40-min YouTube link that could be reference or podcast): ask ONE disambiguating
question, then route.

## Per-format cheatsheet

### book — `source.py book <file.pdf|.epub>`

```bash
./source.py book /path/book.pdf --author addy-osmani --slug beyond-vibe-coding
./source.py book /path/scanned.pdf --scan                 # force vision OCR, prose mode
./source.py book /path/culture-deck.pdf --design          # force vision OCR, design mode
./source.py book /path/book.epub --class-map "chap-title=1,sect-title=2"
```

The handler auto-detects which of three paths a PDF needs:

- **Digital PDF** (clean text layer) → PyMuPDF text extraction (verbatim, free, no key). Structure
  is rebuilt later by `llm-clean` if needed.
- **Scanned OR garbled PDF** → auto-detected (sparse text, or a corrupt glyph-substitution layer —
  e.g. mojibake like `Copyriglzt`) → open-weight **vision OCR, prose mode**. `--scan` forces it,
  `--no-ocr` forbids it. Copyrighted material stays filter-safe on open-weight models.
- **Complex design** (slides, mind maps, infographics, diagrams) → auto-detected (sparse +
  landscape/scattered layout) → **vision OCR, design mode**: reconstructs the *information
  architecture* (timeline→ordered list, mind map→nested outline, connections stated) instead of a
  flat linear transcription, and drops decorative icons. `--design` forces it, `--no-design` opts out.
- **epub** → `markdownify` (pure Python). `--pandoc` uses pandoc if installed (optional upgrade).
- `--class-map` recovers headings ONLY for classes you confirmed are headings (never invent).

### article — `source.py article <url>`

```bash
./source.py article <url>                # default source_kind=article
./source.py article <url> --kind paper   # → papers/   (--kind thread → posts/)
./source.py article <url> --html rendered.html   # JS-gated: browser Save-As fallback
```

**Paywall/`display:none` gotcha**: a gated page can extract as a short stub and *look* complete
— if the word count is suspiciously low, inspect raw HTML for a gate before concluding "no content".

### stream — `source.py stream <url>`

**You (the agent) classify the show.** Probe first, read the metadata, decide reference /
podcast-episode / cut, then run with explicit flags.

```bash
./source.py stream <url> --probe          # prints title/uploader/duration → you classify
./source.py stream <url>                  # reference video (default)
./source.py stream <url> --kind zeitgeist --source-kind podcast-episode \
    --show flow-podcast --guest igor-akita --episode-id 312 --num-speakers 3
```

Podcast-episode is diarized via an audio-capable chat model (default `gemini-3.5-flash-lite`:
separates speakers cheaply). For **speaker-name inference** from the dialogue (people address each
other by name), run with `--diarize-model google/gemini-3.5-flash` — resolved names then appear in
the transcript and pre-fill the `## Speakers` section; otherwise voices stay `SPEAKER_NN` for you to
map. (Diarization does NOT come through OpenRouter's transcription endpoint — hence an audio-chat
model; still one key. See `references/models.md`.) Then hand off to `axi25-ingest`.

### audio — `source.py audio <file|dir>`

```bash
./source.py audio "Cap 1.mp4" --lang pt                   # SRT + txt
./source.py audio meeting.m4a --diarize --num-speakers 3  # speaker-labelled
./source.py audio ~/Courses/lectures --batch --lang pt    # batch a directory
```

Long audio is chunked (16 kHz mono, < 25 MB/request) and timestamps re-offset automatically.

## Post-processing (`postprocess/`)

```bash
./source.py reflow <file.md>              # deterministic dehyphenate + reflow (free, no key)
./source.py llm-clean <file.md>           # LLM fix-only cleanup (OpenRouter open-weights)
./source.py frame  <video> <MM:SS>        # one frame (pip ffmpeg)
./source.py frames <video> uniform 8      # many frames (pip ffmpeg)
```

`llm-clean` is FIX-ONLY (repair OCR + structure, preserve every sentence, keep the language) —
no restyling, summarizing, or analysis. A word-count guard rejects a chunk that got summarized.

## After running — ALWAYS

1. **`source.py reflow`** — deterministic, free. Always safe.
2. **`source.py llm-clean`** — to make structure impeccable (open-weight, ~$0.05/book).
3. **Lint-check and read the diff.** A green `markdownlint-cli2` is necessary, not sufficient.
   Confirm heading hierarchy / paragraphs / speakers are clean and word count didn't drop.
4. **Report + suggest the next path — never take it.** Give the path (+ char/word count, image/
   speaker notes) and suggest what comes next, for the user to decide:
   - book / article / reference video → "extract the mechanisms into the wiki via `axi25-ingest`?"
   - podcast-episode → "have `axi25-ingest` scout zeitgeist signals?"

   Do NOT chain into ingestion or interpretation without an explicit OK.

## Cost (fractions of a cent, mostly)

Audio-short / article / digital book → fractions of a cent. Long podcast → a few cents.
Scanned-book vision OCR (page-by-page) is the one pricey case (cents→~$1) — offer the optional
local `tesseract` path there if the user wants it free/offline.

## Invariants (from the contract)

- `source_kind` is the canonical discriminator; frontmatter is uniform across formats.
- Fidelity: structural cleanup only (artifacts, cruft) — never rewrite/summarize the author.
- No binaries in git: convert to Markdown; register `original_path` + `sha256`; assets → sibling dir.
- Zeitgeist kinds (podcast-episode, cut) route to `50-zeitgeist/`, not `10-sources/`.

## When NOT to use this skill

- "extract the concepts into the wiki" / a file already in `10-sources/` → `axi25-ingest`.
- "note this URL" without intent to convert → `axi25-capture`.
