# Architecture

Why AXI25 Core is built the way it is. Read this to understand the system's design decisions —
not how to *use* it (that's the [README](../README.md)) or how to *develop* it (that's
[CONTRIBUTING](../CONTRIBUTING.md)).

## The problem: drift

One operator accumulates several vaults over time. Before this repo, each vault carried its own
inline copy of the "OS" — the Agent Skills and the `AGENTS.md` contract. Fix a skill in one vault
and the others silently fell behind; a vault two generations old still ran the old naming and the
old rules. The knowledge that should compound was instead fragmenting.

**AXI25 Core is the single source of truth for that OS.** A vault holds only *data*; it consumes
the *behavior* from here. Fix a skill once, and every vault that pulls the core gets the fix.

## The core/data boundary

The split is strict, and it's what makes a single source of truth possible:

| | Owned by the core (this repo) | Owned by the vault |
| --- | --- | --- |
| **What** | behavior | data |
| **Examples** | `skills/`, `AGENTS.md`, `references/`, the CLI | `00-capture/` … `50-zeitgeist/`, `index.md`, `log.md` |
| **The seam** | reads `user-profile.md` for name/language/areas | `90-system/references/user-profile.md` |

The **profile is the only personalization seam**: the core never contains user data, the vault
never edits core files, and the profile is the single file the core reads to adapt to a person. If
that invariant holds, drift is structurally impossible — the vaults only carry data, and behavior
comes from one versioned place.

## Projection: how behavior reaches a vault

The core is `skills/` + `references/` + `AGENTS.md` + the CLI. `wire` projects it into a vault,
guided by one declarative table — `PROJECTIONS` in [`bin/axi25.mjs`](../bin/axi25.mjs) — the single
source of *what goes where*. Projections are **real file copies, never symlinks** (Windows has no
reliable unprivileged symlinks), and the config surfaces (`CLAUDE.md`, `opencode.json`) are
templated so they merge non-destructively with a user's existing file.

### Why root files must be projected (harness discovery)

The non-obvious core of the design: **every harness reads from conventional locations at the vault
root — none of them look inside a submodule.** So the behavior has to be *projected out* to where
each harness expects it:

| Harness | Reads | Projection |
| --- | --- | --- |
| **Claude Code** | `.claude/skills/` + `CLAUDE.md` | real skills copy; `CLAUDE.md` imports `@AGENTS.md` |
| **OpenAI Codex** | `AGENTS.md` + `.agents/skills/` | literal `AGENTS.md` at root (no include mechanism) |
| **OpenCode** | `opencode.json → instructions` + `.agents/skills/` | config points `instructions` at `AGENTS.md` |
| **Pi** | `AGENTS.md` + `.agents/skills/` | literal `AGENTS.md` at root |

This is why a submodule alone is never enough (see [consumption models](#two-consumption-models)):
a submodule mounts at one path, but the contract requires files at the root and in two skill
directories. `wire` is the thin step that bridges that gap.

## The lockfile and integrity

After projecting, `wire` writes `.axi25-lock.json` — a map of each projection to a **canonicalized
content hash**. `verify` recomputes those hashes and fails if:

- a projected file was **hand-edited** (its hash no longer matches the lock), or
- the **core drifted** and the vault wasn't re-wired (when the core source is available in-tree).

Hashes are canonicalized before hashing — CRLF/CR → LF, BOM stripped, tree entries sorted, filenames
checked for case collisions — so the result is **byte-identical on Linux, macOS, and Windows**. The
CI matrix runs `verify` on all three to prove it. This is load-bearing: without it, the same skill
would hash differently per OS and the guard would fail spuriously.

A skill may create runtime artifacts at setup time (e.g. `axi25-source` builds a Python `.venv`).
Those live *inside* a projected skill dir but must never be copied, hashed, or committed — so
`RUNTIME_IGNORE` (`.venv`, `.cache`, `__pycache__`, `.env`, `*.pyc`, …) is excluded from both
`copyTree` and the tree hash. A user running `setup.sh` can't break `verify`.

## Two consumption models

The same repo serves two ways, with **identical vault output**. The model is chosen by *which CLI
you invoke*, not by config — `wire`'s source is simply the package the running CLI belongs to.

| | How | Source of truth | Best for |
| --- | --- | --- | --- |
| **npm** | `npx @axi25/core …` | the published version | every vault (consume + update) |
| **submodule** | mount at `.axi25/`, run `node .axi25/bin/axi25.mjs wire .` | the pinned commit, editable in-tree | the "workshop" vault where you author skills |

Because the output is identical, switching a vault between models is trivial. See
[`docs/maintenance.md`](maintenance.md) for the operational commands.

## Skills and the Agent Skills spec

Skills follow the open [Agent Skills](https://agentskills.io) standard: a folder with a `SKILL.md`
(YAML frontmatter `name` + `description`, plus instructions), optionally bundling `scripts/`,
`references/`, and `assets/`. Two design rules:

- **Progressive disclosure.** `SKILL.md` stays focused ("when + how + pointers"); deep material
  moves into the skill's `references/*.md`, loaded only when the skill fires. `AGENTS.md` itself is
  a *thin router* — it points to skills and references rather than inlining everything.
- **Conformance is guarded.** `.ci/verify.mjs` validates every `SKILL.md` against the spec on each
  run (name ≤ 64 + dir-match + charset, description 1–1024, compatibility ≤ 500, body < 500 lines,
  no unknown frontmatter keys). A non-conforming skill fails CI.

## The axi25-source engine (cloud-first)

`axi25-source` is the one skill with a heavy job — turning raw media into faithful Markdown — and
its architecture is a deliberate answer to the "unzip and it works" tension. Instead of a multi-GB
local ML stack, it is **pip packages + one OpenRouter API key**:

- **PDF** has three paths, auto-detected: digital → PyMuPDF text (free); scanned/garbled text layer
  → open-weight **vision OCR** (prose mode); slide/mind-map/infographic → vision **design mode**,
  which reconstructs the information architecture instead of a flat transcription.
- **Diarization** does *not* come through OpenRouter's transcription endpoint (the OpenAI schema has
  no speaker field), so it runs via an **audio-capable chat model** with a labelling prompt — one
  key, and it can infer speaker names from the dialogue.
- **Model defaults are chosen by a cost-vs-quality bake-off**, not by taste — see
  [`skills/axi25-source/references/models.md`](../skills/axi25-source/references/models.md).

The engine's runtime state (`.venv`, caches, `.env`) is isolated from the projection lock (above),
so a third party sets it up without breaking `verify`, and no secret is ever committed.

## Portability, in one line

**Node is the whole runtime** (zero deps, `>= 18`); no symlinks; hashes canonicalized; a three-OS
CI matrix proves it. The core imposes no other tool on a consumer — not even the maintainer's own
(`mise`, `uv`, etc. are the user's optional layer, never a core requirement).
