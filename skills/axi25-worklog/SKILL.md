---
name: axi25-worklog
description: >
  Create and harvest WORK LOGS in AXI25 — dense records of executed
  technical work (implementation, debugging, deploy, reverse engineering,
  experiments). Drafted in `00-capture/worklogs/`, then promoted (via harvest)
  to `35-worklogs/` as strategic raw material mined for content, projects,
  learning, and connections. Triggers when the user writes or points to a dense
  work session ("full session of", "~Nh getting X running", "reverse-engineering
  of", "work log", "logged this session"), or asks to harvest one ("harvest
  today's log", "what does this log yield", "mine the worklog", "opportunities
  from this log"). A work log is NOT a journal entry (that is `axi25-journal`,
  which is LIFE) nor a study note (that is `axi25-study`). NEVER auto-promote a
  work log to wiki. The harvest is an exploratory intelligence report along a
  learning journey — NOT fixed knowledge.
---

# Work Log

`35-worklogs/` is a first-class layer: the permanent library of dense work
sessions, **strategic raw material** the user mines to extract value — learning,
projects, content, and connections — along a learning journey.

**Voice**: Respond in the language the user is speaking (see `90-system/references/user-profile.md`).

## Lifecycle (capture → harvest → permanent home)

```
00-capture/worklogs/<slug>.md   (WIP draft, status: unprocessed)
        │  session ends → harvest (proactive, confirmed)
        ▼
35-worklogs/<slug>.md           (frozen raw log, status: processed)
35-worklogs/harvest/<slug>.md   (opportunity report)
```

The raw log is preserved **verbatim** when it graduates — nothing is lost. Being
in `35-worklogs/` means it was harvested; the `harvest/` pair is the evidence.

## What belongs here (vs neighbors)

- `35-worklogs/` → WORK I DID. Implementation, debugging, deploy postmortem,
  market reverse engineering, experiments. Dense, technical, project-tied.
- `25-studies/` → STUDY IN FORMATION (`axi25-study`). Understanding a concept/
  book/course. Opens with *"studied X", "notes on…", "reflection on…"*.
- `40-journal/daily/` → LIFE (`axi25-journal`). Interior state, mood, family.

Disambiguate by purpose: worklog = OUTPUT (build/execute); study = INPUT
(understand). A work log opens with a session (*"full session of…", "~Nh getting X
running", "reverse-engineering…"*). If ambiguous, ASK.

## Creating / drafting a Work Log

Drafts live in `00-capture/worklogs/<slug>.md` — build incrementally during the
session (append as you go). Filename kebab-case in the user's `filename_language`
(default: match the user's language; slug = project/topic); body content in the
user's language. NEVER rewrite or summarize the raw content.

```markdown
---
type: worklog
date: YYYY-MM-DD
areas: [work, learning]
projects: [<project-slug>]
status: unprocessed
---

# Work Log — YYYY-MM-DD

## Context

## What I Did / Tested

## Discoveries

## Dead Ends / What Didn't Work

## Links / Commands / Evidence
```

## Harvesting a Work Log — proactive, confirm first

The harvest turns a raw session into surfaced opportunities along a **learning
journey**, and is the act that PROMOTES the log to `35-worklogs/`. The harvest is
an exploratory **intelligence report** ("what did this session yield?"), NOT a
to-do inbox and NOT fixed knowledge.

### Trigger model: teaser → confirm

When a draft in `00-capture/worklogs/` is finished/mentioned (`status:
unprocessed`), offer a SHORT teaser, then harvest only if the user accepts. Do
NOT harvest silently.

> *"This log has ~8 opportunities (2 expensive lessons, 3 content seeds, 1 recurring
> thread with the previous session). Harvest it?"*

If the user explicitly asks ("harvest today's log", "what does it yield"), skip the
teaser and harvest directly.

### Harvest flow

1. Read the work log fully.
2. For the **Journey** lens, scan prior `35-worklogs/*.md` (titles + intros, last
   ~10 by date) to find recurring threads, emerging competencies, and the arc of
   a problem evolving across sessions.
3. **Promote the raw log**: move it from `00-capture/worklogs/` to
   `35-worklogs/<slug>.md` and set `status: processed`. Preserve the body verbatim.
4. Write the report `35-worklogs/harvest/<slug>.md` (template below) — same filename.
5. Append a one-line summary to `log.md`.

**Do NOT** create concept/entity wiki pages from a harvest by default.

### Harvest template

The five lenses below are generic. If the user has defined a personal strategy
framework in `90-system/references/user-profile.md` (e.g. named content channels or
business pillars), map the Content/Toolkit lenses onto it; otherwise use the generic labels.

```markdown
---
type: worklog-harvest
date: YYYY-MM-DD
source: 35-worklogs/YYYY-MM-DD-<slug>.md
status: open          # open | partial | done
---

# Harvest — YYYY-MM-DD

## 🧠 Learning — usable lessons
- [ ] <expensive/durable lesson> → concept candidate `concept-slug`
## 🚀 Projects — seeds and what feeds
- [ ] <new seed OR what feeds an existing project> → [[project]]
## 🎬 Content — angle with a hook
- [ ] <angle with hook> → format: video|post|thread|article
## 🔧 Toolkit — packageable kit/template
- [ ] <reusable pattern worth packaging> → template|script|swipe|agent
## 🔗 Relations — how it connects
- <how it links> [[a]] ↔ [[b]]

## 🧭 Journey — arc of learning
- <thread returning from earlier logs / emerging competency / problem evolving>
```

Drop any lens with nothing real to surface — never pad.

**Checkbox legend** — the checkbox is a conversion tracker (query-able):
`- [ ]` = open opportunity · `- [x]` = converted (acted + routed) → `[[destination]]`.
Only the 4 actionable lenses use checkboxes; **Relations** and **Journey** are
analysis (plain `-` bullets). Concept candidates stay as a `slug` in backticks
(not a ghost wikilink); they become `[[link]]` only when promoted to the wiki.

### The harvest is a REPORT, not an inbox

Each `- [ ]` is an opportunity. When you ACT on one, it **leaves** for its real
home (content → `30-projects/` or `00-capture/quick/`; learning → `25-studies/`
or a wiki candidate; kit → a project/toolkit) carrying `source: 35-worklogs/<slug>`,
**and** gets marked done in the report (`- [x] … → [[where]]`).
The report stays as the permanent record of "raw work → leverage" (e.g. "a 10h
session yielded 3 videos + 1 kit"). Update the file `status` to `partial`/`done`.

### Routing destinations (for Content & Toolkit)

| Target | Output examples |
|---|---|
| Video / podcast episode | scripted episode from a debugging arc |
| Thread / post / newsletter | distilled lesson: hook + story + takeaway |
| Kit (template, script, swipe, agent) | extracted pattern packaged for reuse or sale |
| Course module | curriculum piece from a real session |
| Client case study | structured proof of capability |
| Product feature | technical building block reused |
| Network asset (intro, pitch) | story snippet from a real session |

## Anti-Patterns

- Don't auto-harvest silently — always teaser → confirm (unless directly asked).
- Don't modify the raw log body — the report lives in the `harvest/` companion.
- Don't promote harvest items to wiki concepts/entities by default.
- Don't treat the harvest as fixed knowledge — exploratory report along a journey.
- Don't let the report rot into an inbox — acted items leave for their real home
  AND get marked done; the report is read, not drained.
- Don't run this on a study note (that is `axi25-study`).
- Don't pad empty lenses to look complete.
