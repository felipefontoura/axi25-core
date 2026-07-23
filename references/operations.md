# AXI25 — Operations Reference

> Detailed instructions for each operation. Read the relevant section when executing a command.
> Each operation is owned by a skill in `.agents/skills/` — this file is the shared, condensed reference.

---

## INGEST

**Trigger**: User says "ingest", points to a mature source, or drops content to integrate. Owned by `axi25-ingest` (full Deep Extraction Standard there).

**Steps**:

0. Check maturity: if the material is a study note or early hypothesis, route to `25-studies/` (or `40-journal/daily/` if it is life reflection) unless the user explicitly asks to promote it.
1. Read the source from `10-sources/` or `00-capture/` or inline content.
2. Discuss key takeaways with the user (unless they say "batch" or "just do it").
3. Create source summary → `20-wiki/syntheses/source-<title>.md` (Source Summary template).
4. Extract atomic concepts: check if a concept page already exists in `20-wiki/concepts/`; if exists → UPDATE; if new → CREATE with minimum 3 connections.
5. Extract entities (people, tools, companies, technologies): same create-or-update logic in `20-wiki/entities/`.
6. Update relevant area pages in `20-wiki/areas/`.
7. Update any relevant Maps of Content in `20-wiki/maps/`.
8. Update `index.md`; append to `log.md`.
9. Report to user: what was created, updated, and linked.

**Critical rules**:

- NEVER modify files in `10-sources/`.
- PREFER updating existing pages over creating new ones.
- Each new page needs MINIMUM 3 `[[connections]]`.
- Flag any contradictions with existing wiki content.
- One concept per page — if an idea is compound, split it.
- Do NOT use ingest to canonize immature internal reflection. Use `25-studies/` first.

---

## PROCESS

**Trigger**: User says "process", "process inbox", or "process captures". Owned by `axi25-process`.

**Steps**:

1. Scan the four inboxes under `00-capture/` for files with `status: unprocessed` (or no status).
2. Route by inbox:
   - **`diary/`** → `axi25-journal` (`40-journal/daily/` + signals)
   - **`studies/`** (only if the draft is finished — WIP rule) → `axi25-study` (`25-studies/`)
   - **`worklogs/`** (only if finished — WIP rule) → `axi25-worklog` (`35-worklogs/`, then harvest)
   - **`quick/`** → classify each item and route: concept (`20-wiki/`), study (`axi25-study`), work note (`axi25-worklog`), life (`axi25-journal`), task (`30-projects/`), URL/source (`axi25-ingest`), or split if mixed
3. After processing each file: add `status: processed` + `processed_date: YYYY-MM-DD`, then remove it from the inbox once its content lives in the destination.
4. Update `index.md` if new wiki pages were created.
5. Append to `log.md`.
6. Report summary to user.

---

## SCOUT (Zeitgeist Signals)

**Trigger**: User says "scout signals", "zeitgeist scouting", or a source has `scan_for_zeitgeist: true` in frontmatter. Owned by `axi25-ingest` § Zeitgeist Scouting. For users who work with media / track discourse.

**Steps**:

1. Read the source file.
2. Identify 1-5 candidate signals — the five types (hot-take, contrarian, new-frame, new-data, tension), with the stored label written in the user's language.
3. Write each signal to `50-zeitgeist/discourse/<type>/<source-slug>/signals/signal-NNN-<slug>.md`.
4. Rate with `pauta_rating` (1-5) using the domain-adapted rubric.
5. Report a ranked table to the user.

**Critical rules**:

- Signals live in `50-zeitgeist/`, NEVER in `20-wiki/`.
- Max 5 signals per source (scout, don't dump).
- Every signal needs `pauta_rating` and `discourse_angle`.
- Shelf life: discourse signals expire in 3-6 months.

---

## QUERY

**Trigger**: User asks a question about their knowledge, life, areas, or anything in the wiki. Owned by `axi25-query`.

**Steps**:

1. Read `index.md` to identify relevant pages.
2. Read those pages (concepts, entities, areas, decisions, patterns, syntheses).
3. If the question asks about in-progress study, also read `25-studies/`.
4. If the question asks about interior life, also read `40-journal/daily/`, `40-journal/signals/`, and the relevant area page.
5. Respond with: a clear answer, `[[citations]]` to wiki pages used, a confidence level, and gaps (what is missing).
6. If the user says "save this": create a synthesis page → `20-wiki/syntheses/synthesis-<topic>.md`, update `index.md`, append to `log.md`.

---

## LINT

**Trigger**: User says "lint", "health check", "review wiki quality". Owned by `axi25-lint` (full check list there).

Run the checks in order: orphans, weak pages, ghost links, contradictions, stale pages, incomplete frontmatter, duplicate concepts, area health, premature concepts/entities, promotion debt, layer-type mismatch, harvest debt, misclassified genre, markdown lint. Fix obvious issues automatically (ghost links, incomplete frontmatter); ask about ambiguous ones (merges, contradictions, genre re-routing). Append to `log.md`.

---

## REVIEW (Weekly)

**Trigger**: User says "weekly review", "review", "how was my week". Owned by `axi25-review`.

Read journal + study notes + `log.md` + area pages + active projects for the last 7 days. Generate `40-journal/weekly/YYYY-WNN.md` (see `axi25-review/SKILL.md` for the body). Update area pages, run a light lint, append to `log.md`.

---

## PLAN (Weekly)

**Trigger**: User says "weekly plan", "plan the week", "plan W##". Owned by `axi25-plan`. Forward-looking complement to REVIEW.

Gather context (last review, area pages, active projects, decisions, patterns, recent journal/study). **Dialogue with the user** about priorities, capacity, non-negotiables, and the explicit NO list. Write `40-journal/weekly/YYYY-WNN.md` (`type: weekly-plan`). Update related pages; append to `log.md`.

---

## STUDY NOTES (25-studies/)

**Trigger**: User says "study note", "I'm studying", "notes on [book]", "philosophical/theological reflection", or shares in-progress study. Owned by `axi25-study`.

Draft in `00-capture/studies/`; finalize to `25-studies/<topic-slug>.md` when the study is done. Set `maturity` (raw|study|working-theory|promoted). Do NOT auto-create concepts/entities from a single note. Promote to `20-wiki/` only with explicit user request, repeated evidence, or clear decision/project impact; on promotion set `maturity: promoted`. Append to `log.md`.

---

## CAPTURE

**Trigger**: User says "capture", "save this", "note this". Owned by `axi25-capture`.

Pick the inbox (default `quick/`): `quick/` (untriaged) · `diary/` (life) · `studies/` (study draft, WIP) · `worklogs/` (work draft, WIP). For `studies/`/`worklogs/`, append to the active draft if one exists. Create/append `00-capture/<inbox>/…md` with `type` + `date` + `status: unprocessed` frontmatter. Confirm. Do NOT process — routing happens via PROCESS.
