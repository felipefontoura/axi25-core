---
name: axi25-journal
description: >
  Process LIFE journal entries in AXI25. Handles both digital entries and
  handwritten journal scans. Use when the user says "journal", "process my
  diary", "how was my day", "process today", "extract signals", "daily signals",
  or writes a personal reflection about their day, mood, energy, family, prayer,
  gratitude, crisis, or interior state. Also triggers when handwritten scans
  appear in 00-capture/diary/. Handles both CREATING new daily entries and
  PROCESSING existing ones to extract signals, update areas, and detect patterns.
  NOTE: journal is LIFE only. STUDY in formation (theological/philosophical/
  technical study being digested) lives in `25-studies/` and is handled by
  `axi25-study`. Dense technical WORK LOGS live in `35-worklogs/` and are handled
  by `axi25-worklog`. Neither belongs here.
---

# Journal

Process LIFE journal entries. Extract signals. Detect patterns. Cover personal
daily life, spiritual/interior reflections, and handwritten journals.

Read `90-system/references/page-templates.md` for signal and journal templates.

**Voice**: Respond in the language the user is speaking (see `90-system/references/user-profile.md`).

## What is NOT a journal entry

Journal is LIFE. Two neighbors are handled by other skills — if a file opens this
way, hand it off:

- **Study note** → `25-studies/` via `axi25-study`. Formal study of a concept/
  theory/book/course in formation. Opens with study/reflection (*"studied X",
  "notes on [book]", "philosophical/theological reflection on Z"*).
- **Work log** → `35-worklogs/` via `axi25-worklog`. Dense technical session.
  Opens with a session (*"full session of…", "~Nh getting X running",
  "reverse-engineering…"*).

If ambiguous, ASK.

## Creating a Digital Entry

If the user shares a reflection or daily update, save to `40-journal/daily/YYYY-MM-DD.md`:

```markdown
---
date: YYYY-MM-DD
---

# YYYY-MM-DD

[user's text]
```

Use `40-journal/daily/` for prayer, gratitude, crisis, family, mood, events, and
interior state.

## Processing a Digital Entry

1. Read today's (or specified) journal from `40-journal/daily/`.
2. Extract signals → `40-journal/signals/YYYY-MM-DD.md`:
   - Mood/Energy (from language cues).
   - Events mentioned.
   - People → check/update `20-wiki/entities/`.
   - Projects → check/update `30-projects/`.
   - Decisions → check/update `20-wiki/decisions/`.
3. Update area pages: add to "Recent Signals" (keep last 10).
4. Check `20-wiki/patterns/`:
   - Existing pattern confirmed → increment `observations`, update `last_confirmed`.
   - New pattern emerging → create with `confidence: low`.
5. Append to `log.md`.

**NEVER modify the original journal entry.**

## Handwritten Journal Flow

When physical notebook scans appear in `00-capture/diary/YYYY-MM-DD/`:

1. **Receive scans**: photo(s) of the notebook go to the day's folder
   (`00-capture/diary/YYYY-MM-DD/`).
2. **Transcribe**: read the image + manual review. Generate or update the entry in
   `40-journal/daily/YYYY-MM-DD.md`.
   - If a digital entry already exists for that day, **merge**: the notebook
     content becomes a "Notebook (handwritten)" section within the existing daily entry.
   - If no digital entry exists, create it from the handwritten content.
3. **Extract signals**: pipeline follows the normal flow (extraction →
   `40-journal/signals/`).
4. **Delete the scan** ONLY after the transcription is confirmed saved in
   `40-journal/daily/`. **Never delete blindly** — verify the daily file exists
   and contains the transcribed content first. The source of truth is the
   physical notebook; the vault stores only distilled information.
