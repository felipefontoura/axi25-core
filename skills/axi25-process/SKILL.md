---
name: axi25-process
description: >
  Process all pending captures in AXI25 inbox. Use when the user says
  "process", "process inbox", "process captures", "clean inbox", "what's
  pending", or asks to handle unprocessed items. Also use when the user asks
  "what's in my inbox" or "anything pending". Scans 00-capture/ for unprocessed
  items, classifies each, and routes to the correct wiki location.
---

# Process Inbox

Scan the four inboxes under `00-capture/` and route each to its destination.
Read `90-system/references/page-templates.md` for templates.

**Voice**: Respond in the language the user is speaking (see `90-system/references/user-profile.md`).

## The four inboxes and where they go

| Inbox | Destination | How |
|---|---|---|
| `quick/` | any layer | classify each item (it could be anything) and route |
| `diary/` | `40-journal/daily/` | process as journal via `axi25-journal` |
| `studies/` | `25-studies/` | promote the finished draft via `axi25-study` |
| `worklogs/` | `35-worklogs/` | promote the finished draft via `axi25-worklog` (then offer harvest) |

**WIP rule** — `studies/` and `worklogs/` are drafts the user builds incrementally.
Do NOT promote a draft that is still in progress. Process it only when the
user signals the studies/work is finished (or explicitly asks). When unsure
whether a draft is done, ASK. `quick/` and `diary/` can be processed freely.

## Steps

1. List unprocessed files (`status: unprocessed` or no frontmatter) per inbox.
2. Route by inbox:
   - **`diary/`** → hand to `axi25-journal` (daily entry + signal extraction).
   - **`studies/`** (if finished) → hand to `axi25-study` (→ `25-studies/`). If WIP, skip.
   - **`worklogs/`** (if finished) → hand to `axi25-worklog` (→ `35-worklogs/`, then teaser/harvest). If WIP, skip.
   - **`quick/`** → classify each item, then route:
     - **Mature reusable idea** → concept in `20-wiki/concepts/` (only if ≥3 connections / clear impact)
     - **Study note** → `axi25-study` (`25-studies/`)
     - **Work note** → `axi25-worklog` (`35-worklogs/`)
     - **Life/reflection** → `axi25-journal` (`40-journal/daily/` + signals)
     - **Task/action** → `30-projects/active/`
     - **URL/reference with substantial content** → `axi25-ingest`
     - **Mixed** → split, route each part
3. After processing each file: set `status: processed` + `processed_date: YYYY-MM-DD`, then delete/empty it from the inbox once its content lives in the destination.
4. Update `index.md` if new pages created.
5. Append to `log.md`:
   ```
   ## [YYYY-MM-DD] process | Inbox
   - Processed: N items (quick/diary/studies/worklogs)
   - Routed: list (destination per item)
   ```
6. Report summary.

## Cross-Skill Delegation

Not every capture should be handled inline. Some classifications require delegating to a specialized skill that owns deeper extraction or processing logic.

- **URL/reference with substantial external content** (article, book chapter, video, podcast): Classify as "URL/reference" and **delegate to `axi25-ingest`**. Do NOT create wiki pages directly from the raw content — the ingest skill applies the Deep Extraction Standard (DES) with its 7-layer extraction, voice rules, and size targets. Your job is to classify and hand off; the ingest skill owns the wiki-page creation.

- **Personal reflection or feeling**: Classify as "Reflection/feeling" and **delegate to `axi25-journal`**. The journal skill handles signal extraction, area updates, and pattern detection. Route the capture there rather than creating signals inline.

- **Mature reusable idea**: Route to `20-wiki/concepts/` only when it has recurring use, clear decision/project impact, or at least 3 real connections. Otherwise route to journal or study first.

- **Study/technical/theoretical/philosophical/theological notes not yet crystallized**: Delegate to `axi25-study` and save in `25-studies/`. Do NOT promote to concept/entity by default. From the `studies/` inbox, promote only when the draft is finished (WIP rule).

- **Work notes (executed work — implementation, debugging, deploy, reverse engineering)**: Delegate to `axi25-worklog` and save in `35-worklogs/`. From the `worklogs/` inbox, promote only when the draft is finished (WIP rule); then offer the harvest.

- **Task/action**: Route directly to `30-projects/active/` without delegation. Add to an existing project or create a new one as appropriate.

- **Mixed captures**: Split into components first, then apply the rules above to each part independently.
