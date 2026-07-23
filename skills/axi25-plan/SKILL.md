---
name: axi25-plan
description: >
  Generate a weekly PLAN for AXI25. Use when the user says "weekly plan",
  "plan the week", "plan W##", "what to do this week", "organize the week", or any
  mention of weekly planning/intention-setting. This is the FORWARD-LOOKING
  complement to axi25-review (which looks BACK). Triggers on planning language, not
  review language. Creates a structured weekly plan with goals by area, day-by-day
  schedule, non-negotiables, an explicit "what NOT to do" list, and success
  indicators. Updates the previous week's decision-routine if one exists.
---

# Weekly Plan

Forward-looking weekly planning. While `axi25-review` asks "what happened?",
this asks "what will I make happen?"

**Voice**: Respond in the language the user is speaking (see `90-system/references/user-profile.md`).

## When to Use

- Start of a new week (Sunday night or Monday morning)
- After a review (review feeds data, plan feeds action)
- When the user explicitly asks to plan the week
- When the user says "plan W##" or similar

**Do NOT trigger on**: "how was my week", "summary", "review" — those route to `axi25-review`.

## Relationship to axi25-review

| axi25-review | axi25-plan |
|---------------|-------------|
| Looks BACK | Looks FORWARD |
| "What happened?" | "What will I make happen?" |
| Outcome → indicators checked | Indicators → declared as targets |
| Open loops surfaced | Open loops → scheduled or deferred |
| Patterns confirmed | Patterns → baked into non-negotiables |

Ideal flow: **review Sunday → plan Monday** (or same session: review first,
then plan). The plan references the review's conclusions.

## Steps

### 1. Gather context (READ)

Read in order:

1. **Last weekly review**: `40-journal/weekly/YYYY-W(N-1).md` — conclusions, open loops, "next week focus"
2. **Last weekly plan** (if exists): `40-journal/weekly/YYYY-WNN.md` — planned vs. what the review found
3. **Active area pages**: `20-wiki/areas/*.md` — current goals and signals
4. **Active projects**: `30-projects/active/*.md` — status and next steps
5. **Active decisions**: `20-wiki/decisions/*.md` (status=active) — especially decision-routines with review dates
6. **Patterns**: `20-wiki/patterns/*.md` — which patterns are live and need accounting
7. **Recent journal entries** (last 3-4 days): `40-journal/daily/` — mood, energy, momentum
8. **Recent study notes** (last 3-4 days): `25-studies/` — study in formation, working theories, candidate promotions

### 2. Dialogue with the human (ASK)

**This is the key difference from review.** The plan requires the human's intent.
Present a draft and ask for confirmation/correction on:

- **Priority ranking**: "Of these areas/projects, which are top priority this week?"
- **Capacity estimate**: "Realistically, how much energy/time do you have?"
- **Non-negotiables**: "Any hard commitments this week? (appointments, deadlines, family)"
- **Explicit NO list**: "What are you deliberately NOT doing this week?"
- **Study focus**: "Which ideas need to mature this week without becoming projects yet?"

If the human already provided direction in their prompt (e.g., "focus on the launch
this week"), use that as the primary signal and confirm the rest.

### 3. Generate the plan (WRITE)

Write to `40-journal/weekly/YYYY-WNN.md` — **same file** where the review
lives, but with `type: weekly-plan` (or `weekly-plan-review` if both exist).

```markdown
---
type: weekly-plan
week: YYYY-WNN
period: YYYY-MM-DD to YYYY-MM-DD
based_on: YYYY-W(N-1)
---

# Weekly Plan — WNN (YYYY-MM-DD → YYYY-MM-DD)

## Thesis of the week

1-2 sentences: what is the core hypothesis or intention this week?
e.g., "Execution week: ship the launch and read the market's response."

## Goals by area

### Work
- [ ] Goal 1 (measurable)
- [ ] Goal 2

### Health
- [ ] Goal (e.g., sleep ≤23:30 on 5/7 days)

### Family
- [ ] Goal

### Finance
- [ ] Goal

### Learning
- [ ] Goal (optional — leave empty if not a focus week)

### Spirituality / Philosophy
- [ ] Goal or discernment focus (optional)

## Day-by-day distribution

| Day | Focus | Key action |
|---|---|---|
| **MON DD** | AREA | Key action |
| **TUE DD** | AREA | Key action |
| ... | ... | ... |
| **SUN DD** | REVIEW | Review WNN + plan W(N+1) |

## Non-negotiables

- **Sleep ≤HH:MM** — target N/7 days
- **Morning HH-HH = deep-work block** — no phone, no email
- **Fixed commitment** — e.g., a weekly appointment
- **Daily journal** — any format

## What NOT to do this week

- ❌ Item 1 — reason
- ❌ Item 2 — reason
- ❌ Item 3 — reason

Be explicit and aggressive. Every "not doing" frees energy for what matters.

## Success indicators

(How will the review know the week worked?)

1. Measurable indicator 1 (e.g., "launch shipped by MON?")
2. Measurable indicator 2
3. Measurable indicator 3
4. Qualitative indicator (e.g., "did the routine feed or kill creativity?")
5. **Thesis validated or refuted?** — is the week's thesis true?

## Decision-routine (if any)

If a `decision-routine-W(N-1)` is active with a review date in this week:

- List indicators to verify
- Note: "Review of decision-routine scheduled for YYYY-MM-DD"

## Connected

- [[relevant-project]]
- [[relevant-decision]]
- [[relevant-pattern]]
- [[previous-week-review]]
```

### 4. Update related pages

- **Area pages** (`20-wiki/areas/*.md`): add "Weekly plan WNN: ..." to Recent Signals if the plan defines a new intention
- **Active decisions** (`20-wiki/decisions/*.md`): if a decision-routine hits its review date this week, add a note
- **Project pages** (`30-projects/active/*.md`): update Status with the week's intended milestone
- **`index.md`**: add/update the weekly plan entry
- **`log.md`**: append entry

### 5. Confirm with the human

Present the key structure — thesis, top 2-3 priorities, what's explicitly NOT
happening, non-negotiables — and ask: "Anything to adjust before we lock it in?"

## Anti-Patterns

- **Don't plan without reviewing last week** — the plan must acknowledge what happened or didn't
- **Don't create wishlists** — every goal needs a day assigned or a measurable outcome
- **Don't skip the "NOT doing" list** — this is where the real prioritization happens
- **Don't plan more than 3 focus areas per week** — dispersion kills execution
- **Don't ignore patterns from last week** — if sleep was broken, the plan must account for it
- **Don't overwrite a review** — if a review for the same week exists, merge plan sections into it rather than replacing

## Notes on File Conventions

- Weekly plans live in `40-journal/weekly/YYYY-WNN.md` — same location as reviews
- If both review and plan exist for the same week, they coexist in the same file (review first, plan after, separated by an HR `---`)
- The `type` frontmatter reflects the primary purpose: `weekly-review`, `weekly-plan`, or `weekly-plan-review`
