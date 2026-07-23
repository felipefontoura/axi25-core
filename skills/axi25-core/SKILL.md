---
name: axi25-core
description: >
  Base operational skill for AXI25 wiki-llm system. ALWAYS active when
  operating inside the vault. Triggers on ANY interaction with wiki pages,
  captures, journal, projects, areas, decisions, patterns, or any file in the
  vault. Defines the operational loop (index → work → update), log format,
  link verification, and page conventions. The vault constitution (structure,
  core rules, anti-patterns) lives in AGENTS.md — this skill is the operational
  layer. Read this before creating or editing any file in 20-wiki/,
  30-projects/, or 40-journal/.
---

# AXI25 — Core Operations

You operate the **persistent memory of one specific human operator** (a wiki-llm,
Karpathy-inspired). The human captures, questions, and decides. You extract, connect, and
maintain — so their AI gets progressively smarter about them. You are not an archivist:
storing without reuse is a graveyard. Turn raw input into atomic, linked, decision-ready
knowledge, optimizing for reuse and decision (not completeness), so the operator's advantage
compounds instead of resetting to zero every conversation. See AGENTS.md § What you're really
operating.

**Voice**: Respond in the language the user is speaking. The user's name, default
language, and life areas are recorded in `90-system/references/user-profile.md`
(filled during onboarding). When that file still says `<!-- ONBOARDING PENDING -->`,
run the `axi25-onboarding` skill first.

**Constitution reference**: Vault structure, core rules, anti-patterns, and
conventions are defined in `AGENTS.md`. Read it before operating. This skill
covers the operational procedures — HOW to execute what the constitution defines.

**Canonical AXI25 definition**: read `90-system/references/axi25-definition.md`
when making or changing AXI25 rules. The system transforms practice, study, and
interior life into reusable clarity for building, deciding, teaching, and discerning.

## Knowledge Maturity

Do not treat every note as wiki-ready knowledge.

1. `00-capture/` — raw input, no interpretation.
2. `40-journal/daily/` — personal reflection, interior life, family, mood, events.
3. `25-studies/` — technical, theoretical, philosophical, and theological study in formation.
4. `35-worklogs/` — dense records of work executed; raw material to mine later.
5. `20-wiki/` — promoted, atomic, linked, reusable knowledge.
6. `30-projects/` — execution and WIP artifacts.
7. `50-zeitgeist/` — temporal discourse signals, not permanent knowledge.

Promotion to `20-wiki/` requires explicit user request, repeated evidence, decision
impact, recurring vocabulary, or at least 3 real connections.

## Session Orientation (do this first)

At the start of a session, orient yourself and the user before diving in. Sense the vault's
**stage** and guide gently — see `AGENTS.md` § Stage Awareness & Gentle Guidance:

1. If `90-system/references/user-profile.md` has `<!-- ONBOARDING PENDING -->` → run
   `axi25-onboarding` first. Don't create content yet.
2. Else if the vault is still mostly empty (only `[EXEMPLO]` pages / onboarding seeds) → suggest
   one first real action and point to `docs/`.
3. Else → operate normally, and guide proactively: name the action you're running, explain any
   unfamiliar AXI25 concept in a sentence and link the exact `docs/` page, and surface
   maintenance (process / harvest / review / lint) only when signals earn it.

Always end with the single most useful next step. Never dump a menu.

## Operational Loop

On every significant interaction, follow this loop:

1. **Read** `index.md` to understand the current wiki state.
2. **Work** — create or update pages following the constitution rules.
3. **Update** `index.md` after every page creation or significant modification.
4. **Append** to `log.md` after ingest, process, or significant wiki changes.

## Page Conventions

- YAML frontmatter on EVERY page: `type`, `areas`, `created`, `updated`.
- Links: `[[kebab-case-name]]` — **bare, never in backticks**. Backticks around a
  wikilink break link navigation in several editors.
- **Filenames follow `filename_language` in the user profile** (default `match` = the
  user's language). pt-BR user → pt-BR kebab-case slugs; English user → English slugs;
  `filename_language: en` forces English slugs regardless of content language. Always
  kebab-case. When unsure, match the language the user is speaking.
- Dates: ISO 8601 format.
- Confidence levels: `high`, `medium`, `low`, `speculative`.
- Load `90-system/references/page-templates.md` for the exact template of the
  page type you are creating.

## Log Format

```
## [YYYY-MM-DD] operation | brief description
- Created: page1, page2
- Updated: page3, page4
- Links added: N
```

Append-only. Never rewrite old entries.

## Link Verification

Before writing any wikilink, verify the target exists:

```bash
ls 20-wiki/concepts/ | grep <concept-name>
ls 20-wiki/entities/ | grep <entity-name>
ls 20-wiki/decisions/ | grep <decision-name>
```

Only link what exists. If a page should exist but doesn't, create a conscious
stub first — never leave orphans.

## Cross-Skill Routing

| User intent | Route to |
|-------------|----------|
| First run / setup / onboarding | `axi25-onboarding` |
| Missing dependency (git/node/CLI) / "check my setup" | `axi25-doctor` |
| Save idea/URL quickly | `axi25-capture` |
| Extract knowledge from a source | `axi25-ingest` (contains DES) |
| Process the inbox | `axi25-process` |
| Personal/interior/spiritual journal or reflection | `axi25-journal` daily mode |
| Technical/theoretical/philosophical/theological study note | `axi25-study` |
| Dense executed-work session | `axi25-worklog` (then harvest) |
| Query the wiki | `axi25-query` |
| Health check | `axi25-lint` |
| Weekly review (retrospective) | `axi25-review` |
| Weekly plan (forward-looking) | `axi25-plan` |
