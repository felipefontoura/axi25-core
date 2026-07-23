# AXI25 — Page Templates

> Reference for all page types. Read this when creating or updating pages. Body
> headings below are the canonical English form — when the user's default language
> (see `user-profile.md`) is not English, write the same structure in that language.

---

## Concept (20-wiki/concepts/)

Atomic idea. One concept per file. The core Zettelkasten unit.

```markdown
---
type: concept
areas: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
confidence: high|medium|low|speculative
source_count: 0
---

# Concept Name

## Idea
One clear sentence capturing the essence.

## Detail
2-4 paragraphs explaining the concept.

## Connections
- [[related-concept]] — how they relate
- [[contrasting-concept]] — why they differ
- [[applied-in-project]] — practical application

## Sources
- [[source-name]]

## Open Questions
- What remains unclear or worth investigating?
```

**Naming**: `kebab-case.md` — e.g., `spaced-repetition.md`

---

## Entity (20-wiki/entities/)

A person, company, tool, or technology worth tracking.

```markdown
---
type: entity
category: person|company|tool|technology
areas: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Entity Name

## Who/What
Brief description and context.

## Relevant To
- [[concept-or-project]] — why it matters
- [[another-connection]]

## Key Facts
Notable details worth remembering.

## Sources
- [[source-name]]
```

**Naming**: `kebab-case.md` — e.g., `andrej-karpathy.md`, `ruby-on-rails.md`

---

## Area (20-wiki/areas/)

A life domain. The default core set is: work, health, family, learning, finance.
Add more as needed (e.g. spirituality, content, clients).

```markdown
---
type: area
review_cycle: weekly
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Area Name

## Current State
Brief assessment of where things are now.

## Goals
- Active goal 1
- Active goal 2

## Key Concepts
- [[relevant-concept]]
- [[another-concept]]

## Active Projects
- [[proj-name]]

## Recent Signals
_Extracted from journal by the agent._
- YYYY-MM-DD: signal description → [[related-concept]]

## Decisions
- [[decision-name]]

## Patterns
- [[pattern-name]]
```

**Naming**: `area-name.md` — e.g., `health.md`, `work.md`

---

## Decision (20-wiki/decisions/)

A significant choice worth recording. Track reasoning and outcomes over time.

```markdown
---
type: decision
area: work|health|family|learning|finance
date: YYYY-MM-DD
status: considering|active|completed|reversed
review_date: YYYY-MM-DD
---

# Decision Title

## Context
What situation prompted this decision?

## Options
1. Option A — pros and cons
2. Option B — pros and cons
3. Option C — pros and cons

## Chosen
Which option and why.

## Connected
- [[area-name]]
- [[relevant-concept]]
- [[project-name]]

## Outcome
_Fill in after review_date. What actually happened?_
```

**Naming**: `decision-short-description.md` — e.g., `decision-move-to-remote.md`

---

## Pattern (20-wiki/patterns/)

A recurring pattern detected by the agent from journal entries, signals, or wiki analysis.

```markdown
---
type: pattern
areas: []
confidence: high|medium|low
observations: 0
first_detected: YYYY-MM-DD
last_confirmed: YYYY-MM-DD
---

# Pattern Description

## Observation
What pattern has been detected? Be specific.

## Evidence
- YYYY-MM-DD: what happened
- YYYY-MM-DD: what happened

## Implications
- What does this mean for the relevant areas?
- Which decisions does this inform?

## Suggested Actions
What should the user consider doing?
```

**Naming**: `pattern-short-description.md` — e.g., `pattern-sleep-productivity.md`

---

## Synthesis (20-wiki/syntheses/)

A saved answer, analysis, or comparison. Created when a query produces valuable insight worth keeping.

```markdown
---
type: synthesis
date: YYYY-MM-DD
trigger: query|ingest|review
---

# Title / Question

## Analysis
The full synthesized answer.

## Key Insight
1-2 sentences with the core takeaway.

## Connected
- [[concept-1]]
- [[concept-2]]
- [[entity-1]]
```

**Naming**: `synthesis-short-description.md` — e.g., `synthesis-rag-vs-wiki.md`

---

## Map of Content (20-wiki/maps/)

A thematic index that organizes concepts, entities, and projects around a topic.
A navigational hub (the LYT / "MOC" idea).

```markdown
---
type: map
areas: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Topic Name

## Foundations
- [[fundamental-concept-1]]
- [[fundamental-concept-2]]

## Key Ideas
- [[concept-a]]
- [[concept-b]]

## People & Tools
- [[entity-1]]
- [[entity-2]]

## My Work
- [[project-1]]
- [[project-2]]

## Open Frontiers
- [[emerging-concept]]
```

**Naming**: `map-topic.md` — e.g., `map-ai-engineering.md`

---

## Source Summary (20-wiki/syntheses/)

Created during ingest. Summarizes a source from `10-sources/`. For deep extraction,
follow the Deep Extraction Standard (DES) in `axi25-ingest/SKILL.md`.

```markdown
---
type: source-summary
source_path: 10-sources/articles/filename.md
date_ingested: YYYY-MM-DD
---

# Source: Title

## Summary
Brief overview of the source (3-5 sentences).

## Key Takeaways
- Takeaway 1
- Takeaway 2
- Takeaway 3

## Concepts Extracted
- [[new-or-updated-concept]] — what was added
- [[another-concept]] — what was updated

## Entities Mentioned
- [[entity-name]]

## Contradictions
_Does this source conflict with anything in the wiki? If so, what?_
```

---

## Journal Entry (40-journal/daily/)

Written by the user. The agent reads and processes but does not modify.

```markdown
---
date: YYYY-MM-DD
---

# YYYY-MM-DD

Free-form writing. Thoughts, events, reflections, observations.
No required structure — write naturally.
```

---

## Journal Signal (40-journal/signals/)

Extracted by the agent from journal entries.

```markdown
---
date: YYYY-MM-DD
source: 40-journal/daily/YYYY-MM-DD.md
---

# Signals — YYYY-MM-DD

## Mood/Energy
- Energy: high|medium|low
- Mood: description

## Events
- Event description → [[related-entity-or-area]]

## Mentions
- [[concept-or-project]] referenced

## Patterns Confirmed
- [[pattern-name]] — +1 observation

## Patterns Emerging
- Possible new pattern: description
```

---

## Study Note (00-capture/studies/ → 25-studies/)

Technical, theoretical, philosophical, or theological study notes not yet promoted
to wiki concepts. The staging layer between capture and canonical wiki knowledge.

```markdown
---
type: study-note
date: YYYY-MM-DD
areas: [learning]
topic: <concept/book/course>
projects: []
status: unprocessed     # unprocessed in 00-capture/studies/ → processed in 25-studies/
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

**Critical rules**:

- Do NOT auto-promote to `20-wiki/` from a single note.
- Promote only with explicit user intent or repeated evidence; set `maturity: promoted` on the source.
- Keep unresolved ambiguity here until it matures.
- Use `40-journal/daily/` for interior/personal state; use `35-worklogs/` for dense executed work.

---

## Work Log (00-capture/worklogs/ → 35-worklogs/)

Dense record of work executed — raw material to mine later. NOT a journal entry.
Never summarized; captured as the session happened. Drafted in `00-capture/worklogs/`
(WIP); graduates to `35-worklogs/` (verbatim) when harvested.

```markdown
---
type: worklog
date: YYYY-MM-DD
areas: [work, learning]
projects: [<project-slug>]
status: unprocessed     # unprocessed in 00-capture/worklogs/ → processed in 35-worklogs/
---

# Work Log — YYYY-MM-DD

## Context

## What I Did / Tested

## Discoveries

## Dead Ends / What Didn't Work

## Links / Commands / Evidence
```

**Naming**: `YYYY-MM-DD-<slug>.md` (slug = project/topic). The harvest in
`35-worklogs/harvest/` shares the same filename.

---

## Work Log Harvest (35-worklogs/harvest/)

Companion to a work log — opportunities surfaced along a learning journey.
Exploratory, never knowledge set in stone. Drop any empty lens; never pad.

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

**Checkbox** = conversion tracker: `- [ ]` open opportunity · `- [x]` converted
(acted + routed) → `[[destination]]`. Checkboxes only on the 4 actionable lenses;
**Relations** and **Journey** are analysis (plain `-` bullets). Concept candidates
stay as a `slug` in backticks — they become `[[link]]` only when promoted to the wiki.

---

## Project (30-projects/active/)

```markdown
---
type: project
area: work|health|family|learning|finance
status: active|paused|completed
started: YYYY-MM-DD
updated: YYYY-MM-DD
---

# Project Name

## Goal
What is this project trying to achieve?

## Key Concepts
- [[relevant-concept]]

## Tasks
- [ ] Task 1
- [ ] Task 2

## Status
Current state and recent progress.

## Connected
- [[area-name]]
- [[decision-name]]
```

---

## Weekly Review / Plan (40-journal/weekly/)

Both live in `40-journal/weekly/YYYY-WNN.md` and can coexist in one file.
`type`: `weekly-review` (retrospective), `weekly-plan` (prospective), or
`weekly-plan-review` (both — review first, plan after, separated by an HR).
See `axi25-review/SKILL.md` and `axi25-plan/SKILL.md` for the full body structure.

---

# Zeitgeist Templates (50-zeitgeist/)

> Temporal snapshots of public discourse — the "spirit of the age". For users who
> work with media / track trends. Signals are **intentionally shallow** (no deep DES):
> the value is the discourse pulse, not a masterclass. They decay in months.
> This product ships the **text-discourse** pipeline (articles, papers, threads, talks).
> You paste the text in; `axi25-ingest` § Zeitgeist Scouting extracts signals.

## Zeitgeist — Discourse Article (50-zeitgeist/discourse/articles/)

Article, newsletter, blog post, or essay captured as a sample of public discourse.

```markdown
---
type: source
source_kind: discourse-article
kind: zeitgeist
platform: substack|blog|newsletter|medium|other
author: <author-slug>
source_url: https://...
title: "<original title>"
date_published: YYYY-MM-DD
captured_at: YYYY-MM-DD
captured_period: YYYY-MM
audience_proxy: <e.g. tech-en | mainstream | niche-dev>
scan_for_zeitgeist: true
---

# <Author>: "<Title Hook>"

URL: <source_url>

---

[content — full text, paragraphs preserved]
```

**Naming**: `<author-slug>-<topic-slug>.md`. A **sibling folder** with the same name holds signals (`signals/`).

---

## Zeitgeist — Discourse Paper (50-zeitgeist/discourse/papers/)

Preprint or academic paper captured as a sample of scientific discourse. Different
from `10-sources/papers/` (deep DES): here the focus is **which thesis the paper is
putting in the air** and how people react, not deep extraction.

```markdown
---
type: source
source_kind: discourse-paper
kind: zeitgeist
platform: arxiv|semanticscholar|conference|other
authors: [<author-slugs>]
source_url: https://...
title: "<original title>"
date_published: YYYY-MM-DD
captured_at: YYYY-MM-DD
captured_period: YYYY-MM
audience_proxy: <e.g. ml-research | ai-engineering>
scan_for_zeitgeist: true
---

# <First Author>: "<Title Hook>"

URL: <source_url>

---

[abstract + key sections + public reactions if available]
```

**Naming**: `<first-author-slug>-<topic-slug>.md`. Sibling `signals/` folder.

---

## Zeitgeist — Discourse Thread (50-zeitgeist/discourse/threads/)

A Twitter/X thread, LinkedIn post, Hacker News discussion, or any short multi-voice
public-discourse format. Focus on **tension between voices** and **circulating hot-takes**.

```markdown
---
type: source
source_kind: discourse-thread
kind: zeitgeist
platform: twitter|linkedin|hn|reddit|other
author: <author-slug>
source_url: https://...
date_published: YYYY-MM-DD
captured_at: YYYY-MM-DD
captured_period: YYYY-MM
audience_proxy: <e.g. dev-community>
engagement_proxy: <e.g. 5K likes, 1K reposts>
scan_for_zeitgeist: true
---

# <Author> on <Platform>: "<Thread Hook>"

URL: <source_url>

---

[thread content — posts preserved with author and timestamp]

## Notable reactions
[if any: replies that reinforce or contradict the original thesis]
```

**Naming**: `<author-slug>-<topic-slug>.md`. Sibling `signals/` folder.

---

## Zeitgeist — Discourse Talk (50-zeitgeist/discourse/talks/)

A talk, keynote, or conference presentation captured as a sample of public discourse.
Paste in the transcript (you provide the text; there is no audio pipeline in this edition).

```markdown
---
type: source
source_kind: discourse-talk
kind: zeitgeist
platform: conference-site|video-platform|other
speaker: <speaker-slug>
event: <event-slug>
source_url: https://...
title: "<original title>"
date_published: YYYY-MM-DD
captured_at: YYYY-MM-DD
captured_period: YYYY-MM
audience_proxy: <e.g. conference-attendees>
scan_for_zeitgeist: true
---

# <Speaker> at <Event>: "<Title Hook>"

URL: <source_url>

---

[transcript text — paragraphs preserved]
```

**Naming**: `<speaker-slug>-<topic-slug>.md`. Sibling `signals/` folder.

---

## Zeitgeist — Discourse Signal (50-zeitgeist/discourse/<type>/<source>/signals/)

A **prediction / scouting** signal identified while reading a discourse source. NOT a
clip that already went viral — a signal that **could** enter the public conversation.
Intelligence to feed your content/positioning.

```markdown
---
type: source
source_kind: discourse-signal
kind: zeitgeist
platform: <twitter|linkedin|substack|arxiv|blog|hn|conference>
author: <author-slug>
parent_source: <source-slug>
signal_id: <NNN>
signal_type: <one of the five types, in the user's language — see list below>
discourse_angle: "<what public conversation this feeds>"
viral_hypothesis: "<why it might spread>"
pauta_rating: <1-5>
captured_at: YYYY-MM-DD
---

# <Author>: "<hook phrase>"

## Excerpt
[excerpt from the original, with link/position preserved]

## Zeitgeist signal
[1-2 paragraphs: what public conversation does this feed? Already running or could enter?]

## Why it lands
[mechanism: hot-take? against consensus? new insight? citable phrase?]

## Angle for your content
- agree and expand with X
- counter-narrate showing Y
- contextualize the nuance clips will omit
- connect with Z you already study

## Connected
- [[concept-1]]
- [[entity-1]]
```

**Naming**: `signal-NNN-<slug>.md`.

**Signal types** (the five) — canonical English labels below. Write the actual `signal_type`
value in the user's language (localize per `AGENTS.md` § Naming and Language Rules), consistently:

- `hot-take` — declarative, polemic, citable phrase
- `contrarian` — position against current consensus
- `new-frame` — a new way to see a known topic
- `new-data` — a specific number/fact/case-study that changes the argument
- `tension` — disagreement between relevant voices

---

## Zeitgeist — Multi-Format Synthesis (50-zeitgeist/syntheses/)

Crosses N signals from **different sources** (article + thread + talk) on a common
theme in a period. **Intentionally shallow.** The value is the **gap between formats** —
each format retains something different from the same discourse.

```markdown
---
type: source-summary
kind: zeitgeist
captured_period: YYYY-MM
audience_proxy: <proxy>
sources_analyzed:
  - article: <author>-<topic>
  - thread: <author>-<topic>
  - talk: <speaker>-<topic>
date_ingested: YYYY-MM-DD
---

# Zeitgeist — <topic> (<period>)

## Context
Why this theme? What window? Which audience?

## Sources
- Article: [[author-topic]]
- Thread: [[author-topic]]
- Talk: [[speaker-topic]]

## What spread
Themes/phrases/theses that appeared across multiple formats and performed.

## What got left out
Nuances that only appeared in long sources and never became a clip/thread.

## Gap = signal
The divergence between formats says more about the audience than the content.

## Hooks for your content
Narrative angle: agree? expose the lost nuance? exploit the vacuum?

## Connected
- [[concept-1]]
- [[entity-1]]
```

**Naming**: `zeitgeist-<topic>-<period>.md` — e.g., `zeitgeist-ai-jobs-2026-04.md`.
