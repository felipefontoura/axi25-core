---
name: axi25-study
description: >
  Create and process STUDY NOTES in AXI25 — technical, theoretical,
  philosophical, or theological study in formation. Drafted in
  `00-capture/studies/`, then finalized (promoted) to `25-studies/`, the maturity
  rung between capture and wiki knowledge. Triggers when the user says "study
  note", "notes on [book/course]", "I'm studying", "study log", "philosophical
  reflection", "theological reflection", "study in formation", or shares formal
  study of a concept/theory/book/course being digested (hypotheses, observations,
  open questions). A study note is NOT a life-journal entry (that is
  `axi25-journal`) and NOT a work log (that is `axi25-worklog`, dense executed
  work). Study notes may mature and be promoted to `20-wiki/`, but are NEVER
  auto-promoted.
---

# Study Notes

`25-studies/` is a first-class layer: study in formation — the maturity rung
between raw capture and promoted wiki knowledge. It holds formal study of
concepts, theories, books, courses, and philosophical/theological reflection
being digested. Stable ideas are later promoted to `20-wiki/`.

**Voice**: Respond in the language the user is speaking (see `90-system/references/user-profile.md`).

## Lifecycle (capture → finalize → permanent home → wiki)

```
00-capture/studies/<topic>.md   (WIP draft, status: unprocessed)
        │  study finished (axi25-study)
        ▼
25-studies/<topic-slug>.md      (finalized note, status: processed)
        │  promotion (explicit ask / repeated evidence)
        ▼
20-wiki/concepts|syntheses/      (note stays as provenance; maturity: promoted)
```

The note is preserved **verbatim** when it graduates — nothing is lost. Named by
**topic** (study is subject-centric), not by date.

## What belongs here (vs neighbors)

- `25-studies/` → STUDY IN FORMATION. Understanding a concept/theory/book/course.
- `35-worklogs/` → WORK DONE (`axi25-worklog`). Dense executed technical session.
- `40-journal/daily/` → LIFE (`axi25-journal`). Interior state, mood, family.

Disambiguate by purpose: study = INPUT (understand — *"studied X", "notes on…",
"reflection on…"*); worklog = OUTPUT (build/execute). If ambiguous, ASK.

## Creating / drafting a Study Note

Drafts live in `00-capture/studies/<topic>.md` — build incrementally as you study
(append across days; one growing file per topic). Filename kebab-case in the user's
`filename_language` (default: match the user's language); body in the user's language.

```markdown
---
type: study-note
date: YYYY-MM-DD
areas: [learning]
topic: <concept/book/course>
projects: []
status: unprocessed
maturity: raw|study|working-theory|promoted
---

# Study Notes — <topic>

## Context

## What I Studied

## Observations

## Hypotheses

## Open Questions

## Connections

## Promotion Candidates
```

Default `maturity`: `study`.

## Processing a Study Note (finalize → promote)

1. Read the draft from `00-capture/studies/` (or the file the user points to).
2. Confirm it is a study note (not a work log → `axi25-worklog`; not life →
   `axi25-journal`). If unclear, ASK.
3. **Finalize** (when the study is done): move it to `25-studies/<topic-slug>.md`
   and set `status: processed`. Preserve the body verbatim. WIP drafts stay in
   `00-capture/studies/` until finished.
4. Extract only lightweight signals to relevant areas/projects when obvious.
5. Do NOT create concept/entity pages by default from a single study note.
6. If the user asks to promote, route to the ingest-like promotion flow:
   - Promote stable ideas to `20-wiki/concepts/`.
   - Promote convergent analyses to `20-wiki/syntheses/`.
   - Keep uncertainty and unresolved hypotheses in `25-studies/`.
   - On promotion, set the source note `maturity: promoted` (it stays as provenance).
7. Append operation summary to `log.md`.

## Anti-Patterns

- Don't auto-promote a study note to `20-wiki/` — promotion needs explicit user
  intent, repeated evidence across notes/projects, decision impact, or ≥3 connections.
- Don't create a concept/entity from a single note.
- Don't let study notes become a dead archive — surface promotion candidates in
  weekly review (`axi25-review`).
- Don't put executed work here (that is `axi25-worklog`) or life/interior
  reflection here (that is `axi25-journal`).
