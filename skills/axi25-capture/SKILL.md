---
name: axi25-capture
description: >
  Quick capture to AXI25 inbox. Use this skill whenever the user wants
  to save an idea, thought, note, study note, or work note for later processing.
  Triggers on: "capture", "save this", "note this", "remember this", "jot this
  down", "inbox", "quick note", or any short text that looks like something to
  remember. Do NOT process or analyze — just save to the right inbox and confirm.
  Processing/routing happens later via `axi25-process`.
---

# Capture

Save to the right inbox under `00-capture/` with proper frontmatter. Fast,
minimal, zero friction. Never classify into final layers here — that is
`axi25-process`.

**Voice**: Respond in the language the user is speaking (see `90-system/references/user-profile.md`).

## The four inboxes

Pick the inbox from the obvious signal; when unsure, default to `quick/`.

| Inbox | When | Behaviour |
|---|---|---|
| `quick/` | jotted thought, idea, URL — "don't know what it is yet" | new timestamped file |
| `diary/` | life, mood, family, prayer, philosophy reflection | new timestamped file |
| `studies/` | a study note (shallow or dense) | WIP draft — append to the in-progress draft if one exists, else create |
| `worklogs/` | a work note (shallow or dense) | WIP draft — append to the in-progress draft if one exists, else create |

`studies/` and `worklogs/` are **drafts the user builds incrementally** — they often
keep adding to the same file across a session before it is finished. Append rather
than spawning many fragments, unless the user is clearly starting a new topic.

## Steps

1. Choose the inbox (above). Default `quick/`.
2. For `quick/` and `diary/`: create `00-capture/<inbox>/YYYY-MM-DD-HHMMSS.md`.
   For `studies/` and `worklogs/`: append to the active draft
   (`00-capture/<inbox>/<topic-or-date>.md`) if it exists, else create it.
3. Frontmatter:
   ```markdown
   ---
   type: quick | diary | study-note | worklog
   date: YYYY-MM-DDTHH:MM:SS
   status: unprocessed
   ---

   [user's text]
   ```
4. Confirm: "✅ Captured → <inbox>/filename"

Do NOT process, classify into final layers, or integrate. That happens later via
`axi25-process` (which routes each inbox to its destination).
