---
name: axi25-review
description: >
  Generate a weekly review of AXI25. Use when the user says "weekly review",
  "how was my week", "week summary", "review", or asks about their week. Reads
  journals, log, areas, and projects to generate a comprehensive review. Also reads
  study notes to surface study-in-formation and promotion candidates. Suggests focus
  for next week based on patterns and open loops.
---

# Weekly Review

Comprehensive weekly assessment across all life areas.

**Voice**: Respond in the language the user is speaking (see `90-system/references/user-profile.md`).

## Steps

1. Read journal entries for the last 7 days: `40-journal/daily/`
2. Read study notes for the last 7 days: `25-studies/`
3. Read `log.md` entries for the last 7 days
4. Read all area pages: `20-wiki/areas/`
5. Read active projects: `30-projects/active/`
6. Generate → `40-journal/weekly/YYYY-WNN.md`:

```markdown
---
type: weekly-review
week: YYYY-WNN
period: YYYY-MM-DD to YYYY-MM-DD
---

# Weekly Review — Week NN

## Summary
High-level narrative.

## By Area
### Work
### Health
### Family
### Learning
### Finance

## Knowledge Growth
- Sources ingested: N
- Pages created/updated: N
- New patterns: list

## Study Learning
- Study notes created: N
- Working theories: list
- Candidate promotions: list

## Spiritual / Philosophical Signals
- Interior patterns, theological questions, discernment signals

## Decisions
- Active: list with status
- New this week: list

## Open Loops
Unresolved items needing attention.

## Next Week Focus
Priorities based on patterns and open loops.
```

Then: update all area pages with their current state, run a light lint (orphans +
ghost links), and append the operation to `log.md`.
