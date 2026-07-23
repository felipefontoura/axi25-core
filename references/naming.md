---
type: system-reference
name: naming
---

# Naming and Language Rules

> Loaded on demand. The one-line "language seam" lives in `AGENTS.md`; the full policy is here.

## The three-way split

1. **You interact in the user's language — always.** The skills, `AGENTS.md`, and these
   reference docs are English *instructions to you* (semantic code). They are NOT the language
   you speak. At runtime you reply, ask, explain, and narrate in whatever language the user is
   using: user writes pt-BR → you answer pt-BR; user writes English → you answer English; and so
   on. Never mirror the English of the instruction files back at the user.
2. **Vault content is written in the user's default language** (`language` in the profile): wiki
   pages, journal/study/worklog entries, generated content, and per-folder notes the user reads.
3. **Filenames follow `filename_language`.**

## Filenames

- **AI-generated filenames follow the user's language**, kebab-case. Converses in pt-BR →
  pt-BR slugs (`respiracao-consciente.md`); in English → English slugs (`conscious-breathing.md`);
  same for any other language.
- The choice is stored as `filename_language` in `user-profile.md`. Default `match` (mirror the
  user's default language). A user may force one language — e.g. `filename_language: en` forces
  100% English slugs regardless of content language.
- **File content is always the user's default language.** So with a forced `filename_language`
  the slug and the body may differ — that is intentional.
- When in doubt, match the language the user is speaking.

## Human-facing labels

Categorical labels the user reads or picks — zeitgeist **signal types**, worklog **harvest
lenses**, tags, section headings, any status shown in a message — are written in the user's
language, consistently. Do not emit a random EN/pt-BR mix in one vault.

- **Frontmatter *keys* stay English** (stable schema).
- **Pure machine-state enums stay English** for portability: `type`, `status`, `confidence`,
  `maturity`. But when you *show* a status to the user, phrase it in their language.
- The five zeitgeist signal types are concepts, not fixed strings — localize the label
  (EN: hot-take, contrarian, new-frame, new-data, tension · pt-BR: hot-take, contrário,
  frame-novo, dado-novo, tensão · and so on).

## Code

In `.py` / `.sh` / `.ts` / `.js`: variables, functions, classes, docstrings, comments, logs —
all English. Only user-facing strings may be localized.

## Which docs are English (instruction) vs user-language (artifact)

- **English (semantic code for the agent):** `SKILL.md` files and their auxiliaries, `AGENTS.md`,
  and these `references/*` — they *instruct* you; you *speak* the user's language at runtime.
- **User's language (vault artifacts):** wiki pages, journal/study/worklog entries, generated
  content, per-folder `README.md`s — anything the user reads as a vault artifact.

When the profile is not set yet, infer the language from how the user writes, and confirm it
during onboarding.
