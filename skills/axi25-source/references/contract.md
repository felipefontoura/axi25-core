# Source-acquisition contract

> Loaded on demand by `axi25-source`. The uniform shape every acquired source note follows.

## Fidelity rule (the prime directive)

Acquisition produces a **verbatim seed**. Do only **structural** cleanup — dehyphenation,
paragraph reflow, page-number/running-head removal, heading recovery from what the text itself
marks. **Never** rewrite, summarize, translate, paraphrase, reorder, or invent. Interpretation
is `axi25-ingest`, not here. A green `markdownlint-cli2` is necessary, not sufficient — read the
diff and confirm no structure was lost and word count didn't drop.

## `source_kind` — the canonical discriminator

| source_kind | handler | destination |
|---|---|---|
| `pdf-book` / `epub-book` | book | `10-sources/books/<author_slug>/<book_slug>.md` |
| `article` / `paper` / `thread` / `talk` | article | `10-sources/{articles,papers,posts}/<slug>.md` |
| `video-reference` | stream (default) | `10-sources/videos/reference/<creator>/<slug>.md` |
| `podcast-episode` | stream (zeitgeist) | `50-zeitgeist/podcasts/<show>/<slug>.md` |
| `cut` | stream (zeitgeist) | `50-zeitgeist/podcasts/<show>/<parent>/cuts/<id>-<slug>.md` |

Zeitgeist kinds (`podcast-episode`, `cut`) route to `50-zeitgeist/` (temporal discourse, expires
in months), everything else to `10-sources/` (permanent raw material).

## Frontmatter (uniform across formats)

Always present: `type: source`, `source_kind`, `title`, `acquired` (ISO date), `original_path`.
Common optional: `author`, `author_slug`, `lang`, `sha256` (for local binaries), `note`.
Per-kind adds its own keys (e.g. `page_count`/`image_count` for books; `video_id`/`channel`/
`duration` for streams; `show`/`guest`/`episode_id`/`audience_proxy` for zeitgeist).

Frontmatter *keys* are always English (stable schema). Body content follows the user's language.

## Binary policy — no binaries in git

Never commit a PDF/epub/audio/video into the vault. Convert to Markdown and register:
`original_path` (where the binary lives) + `sha256` (integrity). Use `--library <dir>` to relocate
the binary outside the vault. Extracted assets (cover, figures) go to a **sibling directory**
(`<slug>/`) referenced by wikilink/markdown image — small images only; full-page scans are skipped.

## Handoff

Acquisition stops at the `.md`. Report the path (+ char/word count, image/speaker notes) and
suggest the next step (`axi25-ingest` for wiki extraction / zeitgeist signal scouting) — for the
user to decide. Never chain into ingestion without an explicit OK.
