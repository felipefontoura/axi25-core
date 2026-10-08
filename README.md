<div align="center">

# AXI25 Core

**The harness-agnostic operating system for a personal, AI-operated knowledge vault.**

One versioned source of truth — skills + contract + reference docs — that projects into any vault
so the same behavior runs on **Claude Code · OpenAI Codex · OpenCode · Pi**, with zero setup.

[![CI](https://github.com/felipefontoura/axi25-core/actions/workflows/ci.yml/badge.svg)](https://github.com/felipefontoura/axi25-core/actions/workflows/ci.yml)
[![npm](https://img.shields.io/npm/v/@axi25/core)](https://www.npmjs.com/package/@axi25/core)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
![node](https://img.shields.io/badge/node-%E2%89%A518-brightgreen)
![agent skills](https://img.shields.io/badge/agent%20skills-14-blue)
![deps](https://img.shields.io/badge/dependencies-0-brightgreen)
![platforms](https://img.shields.io/badge/platforms-linux%20%C2%B7%20macos%20%C2%B7%20windows-informational)

</div>

---

## What is this?

A **wiki-llm** vault is the persistent memory of one specific human operator: the compounding record
an AI reads so it stops restarting from zero every conversation. **AXI25 Core** is the *behavior* of
that vault — the [Agent Skills](https://agentskills.io), the operating contract (`AGENTS.md`), and the
reference docs — packaged as a single, versioned unit.

Your vaults hold **data**. This repo holds **behavior**. A thin `wire` step projects the behavior into
each vault, in exactly the shape every agent harness expects. Fix a skill once here, and every vault
that consumes it gets the fix — no more copies drifting apart.

## Quickstart

```bash
# scaffold a fresh vault (folder tree + anchors) and wire the core into it
npx @axi25/core init my-vault

# then open my-vault/ in your agent and type:  onboarding
```

Already working in Claude Code, Codex, OpenCode or Pi? Install just the 14 skills; the
`axi25-onboarding` skill scaffolds the rest of the vault on first run:

```bash
npx skills add felipefontoura/axi25-core

# then open the folder in your agent and type:  onboarding
```

In an existing vault:

```bash
npx @axi25/core wire      # (re)project the current core
npx @axi25/core update    # pull a newer core version
npx @axi25/core verify    # CI guard: assert the projected files still match the lockfile
npx @axi25/core doctor    # check environment + core freshness
```

Requires **Node ≥ 18** — that is the whole runtime. No other install.

Want the complete, ready-to-use vault (Obsidian AI panel, docs, guided setup) instead of a bare
one? Use [`@axi25/vault`](https://github.com/felipefontoura/axi25):
`npx @axi25/vault@latest init my-vault`.

## Supported harnesses

| Harness | Reads | Notes |
| --- | --- | --- |
| **Claude Code** | `.claude/skills/` + `CLAUDE.md` | native skill discovery |
| **OpenAI Codex** | `AGENTS.md` + `.agents/skills/` | via the AGENTS.md contract |
| **OpenCode** | `opencode.json` → `AGENTS.md` | config points at the contract |
| **Pi** | `AGENTS.md` + `.agents/skills/` | via the AGENTS.md contract |

## What's inside

**14 Agent Skills** — the operating loop of the vault:

`capture` · `ingest` · `process` · `journal` · `study` · `worklog` · `query` · `lint` · `review`
· `plan` · `onboarding` · `doctor` · `core` · **`source`**

The standout is **`axi25-source`** — cloud-first source acquisition. It turns any raw media into
clean, faithful Markdown using **pip packages + one OpenRouter API key** and no heavy local ML:

- **Books** — PyMuPDF for digital PDFs, open-weight **vision OCR** for scanned/garbled ones,
  `markdownify` for epub.
- **Complex designs** (slides, mind maps, infographics) — vision *design mode* reconstructs the
  information architecture, not a flat transcription.
- **Web** — `trafilatura` (local, no key).
- **Audio & video** — OpenRouter transcription + **speaker diarization with name inference**.

Every model default was chosen by a [cost-vs-quality bake-off](skills/axi25-source/references/models.md),
not by taste.

## How it works

The core lives in `skills/`, `references/`, and `AGENTS.md`. `wire` projects it into a vault as
**real copies** (never symlinks — Windows-safe), guided by one declarative table (`PROJECTIONS` in
`bin/axi25.mjs`), and writes a **lockfile** (`.axi25-lock.json`) of content hashes. `verify` fails if
a projected file was hand-edited or the core drifted — hashes are canonicalized (EOL/BOM/case) so the
result is byte-identical on Linux, macOS, and Windows (proven by the CI matrix).

**Two consumption models, one repo, identical output:**

| | How | Best for |
| --- | --- | --- |
| **npm** | `npx @axi25/core …` | every vault (consume + update) |
| **submodule** | mount at `.axi25/`, run `node .axi25/bin/axi25.mjs wire` | the "workshop" vault where you author skills |

→ **Design rationale:** [docs/architecture.md](docs/architecture.md) · **operational runbooks**
(update a vault, repoint, release): [docs/maintenance.md](docs/maintenance.md).

## Contributing

Contributions are welcome — see **[CONTRIBUTING.md](CONTRIBUTING.md)**. The golden rule: edit the
**source** in `skills/` and `references/`, never the projected copies; `wire` regenerates them, and
`npm test` enforces both the projection lock and [Agent Skills spec](https://agentskills.io) conformance.

By participating you agree to our [Code of Conduct](CODE_OF_CONDUCT.md). To report a vulnerability, see
[SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE).
