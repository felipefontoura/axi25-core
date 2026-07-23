---
name: axi25-ingest
description: >
  Ingest a source into AXI25 wiki using the Deep Extraction Standard (DES).
  Use whenever the user wants to integrate an article, document, book chapter,
  video notes, podcast notes, or any substantial content into their knowledge base.
  Triggers on: "ingest", "integrate this into the wiki", "process this source",
  "add to wiki", "read and integrate", or when the user points to a file in
  10-sources/ or pastes long-form content. Also use when the user drops a new
  file into the vault and wants it processed into knowledge. Do not use for early
  internal reflections or study notes unless the user explicitly asks to promote
  them. This is the CORE operation of the wiki-llm pattern — it transforms raw
  material into structured, linked wiki pages following the Deep Extraction Standard.
---

# Ingest — Deep Extraction Standard

Transform raw sources into structured, interlinked wiki knowledge. This is the
core wiki-llm operation: knowledge is compiled once and kept current, never
re-derived per query.

Read `90-system/references/page-templates.md` for templates before creating pages.

**Voice**: Respond in the language the user is speaking (see `90-system/references/user-profile.md`).

## Standard Ingest Workflow

1. Read the source (from `10-sources/`, `00-capture/`, or inline).
   - If it is an internal reflection/study note, route to `axi25-study` unless the user explicitly asked for promotion.
2. Discuss key takeaways with the user (unless they say "batch" or "just do it").
3. Create source summary in `20-wiki/syntheses/source-<title>.md` using DES (see below).
4. Extract atomic concepts → create or update `20-wiki/concepts/`.
5. Extract entities → create or update `20-wiki/entities/`.
6. Update relevant area pages → `20-wiki/areas/`.
7. Update relevant Maps of Content → `20-wiki/maps/`.
8. Update `index.md` and append to `log.md`.
9. Report: what was created, updated, linked.

## Optional: Zeitgeist Scouting

When the source has `scan_for_zeitgeist: true` in its frontmatter (or the user says
"scout signals", "do a zeitgeist scouting pass", "what signals are here"), run a
lightweight discourse scouting pass after the DES extraction. This is for users who
work with media / need to stay tuned to the current discourse ("spirit of the age").

1. Read the source (already ingested into `10-sources/` or `50-zeitgeist/discourse/`).
2. Identify 1-5 candidate signals. Five signal types (canonical English labels below; write the
   stored label in the user's language — localize per `AGENTS.md`), consistently:
   - **hot-take** — declarative punchy phrase, citable, polemic
   - **contrarian** — position against current consensus
   - **new-frame** — a new angle on a known topic
   - **new-data** — a specific number/fact/case-study that changes the argument
   - **tension** — disagreement between relevant voices
3. For each signal, write `50-zeitgeist/discourse/<type>/<source-slug>/signals/signal-NNN-<slug>.md`
   using the Discourse Signal template in `90-system/references/page-templates.md`.
4. Rate each signal with `pauta_rating` (1-5) using this default rubric (adapt to the user's domain):
   ```
   score = 1 (base)
     + 2 if it intersects one of the user's core areas (see user-profile)
     + 1 if it connects with other signals already captured
     + 1 if it has a teaching element (explains something new)
     + 1 if it has a narrative element (punchy phrase, story)
     − 1 if it requires context the user does not command
     − 1 if the production cost is prohibitive
     − 1 if it decays fast (< 3 months)
     clamp 1-5
   ```
5. Report a ranked table to the user. Do NOT auto-create synthesis or wiki pages
   — signals live in `50-zeitgeist/`, not `20-wiki/`.

**Routing by source type**:

| Source type | `50-zeitgeist/` path | Template |
|-------------|---------------------|----------|
| Article / blog post / newsletter | `discourse/articles/<slug>/` | Discourse Article |
| Paper / preprint | `discourse/papers/<slug>/` | Discourse Paper |
| Thread (Twitter/X, LinkedIn, HN) | `discourse/threads/<slug>/` | Discourse Thread |
| Talk / keynote | `discourse/talks/<slug>/` | Discourse Talk |

## Deep Extraction Standard (DES)

This vault is a **second brain** — not a collection of connected summaries. Every
`source-*` page in `20-wiki/syntheses/` must extract **craft**, not narrate facts.

**Mandatory application**: every mature source ingest (course, book, article,
paper, podcast, promoted study note) follows this standard. Early internal
brainstorms and study notes default to `25-studies/`, not DES.

### 7 Layers per Significant Idea

For each meaningful idea in the source:

1. **The idea** — in your own voice, clear and precise.
2. **Mechanism** — WHY does it work? The underlying principle, not just the fact.
3. **Source example** — unfolded, not just named. What happens, in what context, how it operates.
4. **Applied example** — mapped to the user's context/goals when there's obvious transfer.
5. **Anti-pattern or variant** — how it fails, how it varies.
6. **When to use / when NOT to use** — contextual applicability.
7. **Operational hook** — how the user applies this tomorrow.

### Frameworks vs Tactical Plays

- **Large frameworks** (3-act structure, storytelling levels, sales funnels)
  get **full decomposition**. Each component deserves 7 layers.
- **Tactical plays / individual patterns / pocket rules** do NOT get 7 layers each.
  The **category** gets it. Example: a family of related patterns in ≤100 lines
  covering all of them — not 7 layers per pattern.

### Voice (second brain ≠ landing page)

Cold, analytical, skeptical. Cut hype adjectives and self-praise. If an idea demands
emphasis, describe the mechanism; don't decorate it with adjectives ("pure gold",
"brutal", "state of the art", "strong signal", etc. are forbidden crutches).

### Structural Anti-Shortcuts

- **NEVER consolidate 3+ chapters into one section**. If a chapter has a distinct idea,
  it gets its own 7 layers. If it's a variation, name it explicitly ("Chapters 5-7
  apply chapter 4 to X/Y/Z, no new mechanism").
- **"Surgical application to your context"** is a **3-7 actionable-lines table**,
  not a 15-item checklist. Strong hooks > generic hooks.
- **Redundancy between sources is waste**. If source A already decomposed 4 phases and
  source B also does, only cross-reference; don't re-decompose.
- **Cross-ref between sources**: OK and desired. **Direct attributed quote**: only if
  it's in the raw of THAT source. Quote from another source: `per [[source-X]]: <quote>`.

### Execution Discipline

- **Sequential solo for single nuanced sources** (course, paper, conversation where
  cross-source consistency matters). For **batches of full books** in
  `10-sources/books/`, use **parallel** — see § Massive Book Ingest.
- **Human checkpoint after every delivered source**. Don't chain without explicit OK.
- **Verify wikilinks BEFORE writing**: `ls 20-wiki/concepts/ | grep <name>`,
  `ls 20-wiki/entities/ | grep <name>`. Orphans are technical debt — only link what
  exists (or create a conscious stub first).
- **Post-write literal self-check**:
  - `wc -l <file>` for size (never estimate)
  - Grep for hype crutches; if several, rewrite
  - Honest simulation: "if the raw were deleted now, does the synthesis teach?"

### Calibrated Size Targets

- **Dense books / full courses / manifestos**: 400-700 lines
- **Short tactical playbooks**: 200-400 lines
- **Academic papers** (5-15 pages): 150-350 lines
- **Isolated articles / single chapters**: 100-200 lines

A 50-line summary for a 45-min course = red flag. An 800-line summary for an
8-page paper = inflation.

### 6-Month Test (Author's Mental Ruler)

After writing: "reading only this synthesis in 6 months, can I teach the content —
without reopening the original?" If not, it's shallow. Rewrite.

**The test is a mental ruler for the author, not a section of the document.**
Do NOT include a "Depth test" section at the end (author self-validating their own
work = confirmation bias). Open directly with `## Context` and close with `## Connected`.

## Massive Book Ingest (`10-sources/books/`)

When there are **full books** in an author folder (`10-sources/books/<author>/*.md`,
complete text) and the user wants to cover everything ("massive ingest", "all of
<author>", "go massive"), do NOT go sequential-solo — **parallelize with subagents,
one per book**.

**Pattern (orchestrator = main loop):**

1. `ls 10-sources/books/<author>/` — map the books + their source syntheses (`20-wiki/syntheses/source-*`).
2. **One subagent per book** (Agent tool, in parallel in a single turn). For large books
   (>200K), 1 agent each; small playbooks can be grouped (~6 per agent).
3. Each subagent receives the DES spec and follows the **anti-drift discipline** below.
4. **After all finish**, the orchestrator centrally: indexes the new concepts (1 block in
   `index.md`), recomputes ghosts, updates `log.md`. Subagents do NOT touch index/log.

**Anti-drift discipline (what makes parallel safe):**

- **Partition by book** — each agent extracts only ITS book's concepts. No overlap.
- **Check-exists before creating** (`ls 20-wiki/concepts/<slug>.md`) — if it exists, SKIP.
- **Each agent owns ONE synthesis** (its book's) — updates `## Concepts Extracted` there.
  Never edits another agent's synthesis/concept → zero concurrent-write conflict.
- **No ghosts**: link only what was confirmed via `ls`.
- **Normal DES frontmatter + voice**; content in the user's language, slug per the
  user profile's `filename_language` (default: match the user's language), faithful to
  the source (canonical numbers/quotes, invent nothing).

**Known risk**: if the session hits the token limit mid-run, agents die on the final
step (report/synthesis-update). Concepts already created stay on disk (idempotent) —
the orchestrator just finalizes index/syntheses/ghosts, or re-runs (check-exists skips
what exists).

## When to NOT Use This Skill

- "what do I know about X" → `axi25-query`
- "note this" (quick save without extraction) → `axi25-capture`
- "scout signals from [source already in the vault]" → use the zeitgeist scouting phase above (no full DES re-extraction needed)
