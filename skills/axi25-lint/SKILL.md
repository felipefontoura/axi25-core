---
name: axi25-lint
description: >
  Health-check AXI25 wiki. Use when the user says "lint", "health check",
  "review the wiki", "check wiki quality", "any problems", "orphan pages",
  "inconsistencies", "wiki health", "orphans", "contradictions", or asks about
  the quality or consistency of their knowledge base. Also trigger periodically as
  part of weekly reviews. Finds orphan pages, weak connections, ghost links,
  contradictions, stale content, premature promotions, and suggests improvements.
---

# Lint

Health-check the wiki. Fix obvious issues, ask about ambiguous ones.

**Voice**: Respond in the language the user is speaking (see `90-system/references/user-profile.md`).

## Checks (in order)

1. **Orphans**: pages in `20-wiki/` with zero inbound `[[links]]` (ignore `README.md` folder docs)
2. **Weak pages**: fewer than 3 outbound `[[connections]]`
3. **Ghost links**: `[[links]]` pointing to non-existent pages. **Exclude (these are NOT ghosts):**
   - `README.md` folder docs.
   - **Wikilink-syntax examples** in docs/constitution (e.g. AGENTS.md showing `` `[[link]]` ``, `[[kebab-case-name]]`; maps showing a pipeline `[[raw-source]] → [[synthesis]]`) — literal examples, not real links.
   - **Skill names** (`axi25-*`) — not wiki pages.
   - **Candidates in raw material** (work-log bodies, "Promotion Candidates") — kept as `` `slug` `` (backtick), become a page only on promotion; do not count as ghosts.
   - **Escaped aliases in a table**: `[[page\|alias]]` resolves to `page` (the `\|` is a pipe escape in a markdown cell) — parse the target BEFORE the `\|`/`|`, not after.
4. **Contradictions**: conflicting claims across pages
5. **Stale**: `updated` date older than 30 days
6. **Incomplete frontmatter**: missing type, areas, or created
7. **Duplicate concepts**: very similar pages that should merge
8. **Area health**: area pages without recent signals (7+ days)
9. **Premature concepts/entities**: pages created from a single internal reflection, low connection count, or unclear decision/project relevance
10. **Promotion debt**: study notes (`25-studies/`) with repeated candidate promotions but no review
11. **Layer-type mismatch**: enforce the life/study/work axis (see AGENTS.md § Study Note vs Work Log).
    - file in `25-studies/` whose frontmatter `type` ≠ `study-note`
    - file in `35-worklogs/` whose frontmatter `type` ≠ `worklog`
    - file in `40-journal/daily/` carrying a `type` of `study-note`/`worklog` (genre in the wrong home)
12. **Harvest debt**: work-log drafts in `00-capture/worklogs/` (`status: unprocessed`) older than 14 days — finished sessions never harvested/promoted, strategic raw material going stale
13. **Misclassified genre**: a `25-studies/` file that opens like a work session (*"full session of…", "got X running", "reverse-engineering…"*), or a `35-worklogs/` file that opens like study (*"studied X", "notes on…", "reflection on…"*) → flag for re-routing, ASK before moving
14. **Markdown lint**: run `npx markdownlint-cli2` over changed/new `.md` (vault config). **REPORT only — never blind `--fix`** (autofix can mask structural loss, e.g. flattened chapters lint clean). List offenders; fix BY HAND, reviewing the diff. `10-sources/` is verbatim — don't rewrite a source to satisfy a cosmetic rule. See AGENTS.md § Markdown Lint.

## Output Format

```markdown
## Lint Report — YYYY-MM-DD

### 🔴 Critical
- Ghost link: [[page]] in concepts/xyz.md

### 🟡 Medium
- Orphan: entities/some-entity.md
- Weak: concepts/vague-idea.md (1 connection)

### 🟡 Layer coherence
- Type mismatch: 25-studies/topic.md has type `worklog` (expected `study-note`)
- Harvest debt: 00-capture/worklogs/2026-05-20-foo.md unharvested for 21 days
- Misclassified: 25-studies/foo.md opens like a work session → likely worklog

### 🟢 Suggestions
- Merge: [[concept-a]] ≈ [[concept-b]]
- Stale: areas/finance.md (45 days)
- Missing page: "machine learning" mentioned 5x, no concept page

### Stats
- Pages: N | Avg connections: N | Orphan rate: N% | Score: N/10
```

Auto-fix: ghost links, incomplete frontmatter, layer-type mismatch on `type` when the home folder makes the genre unambiguous (`25-studies/` → `study-note`, `35-worklogs/` → `worklog`).
Ask user: merges, contradictions, genre re-routing (moving a file between `25-studies/` and `35-worklogs/`).
Append to `log.md`.
