# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Claude Code plugin: `.claude-plugin/plugin.json` (with version and icon) and
  `marketplace.json`, so the skills install with `/plugin marketplace add felipefontoura/axi25-core`.
- `npm test` checks that the plugin manifest version matches `package.json`.

### Changed

- README: a "Data handling and privacy" section; the plugin manifest links to it, to the issues page and to the docs.
- `axi25-doctor`: on Windows it no longer suggests `-ExecutionPolicy Bypass`; the user decides.

## [2.0.2] — 2026-10-06

### Changed

- Docs: npm and MIT badges, a pointer to the full `@axi25/vault`, and the release runbook now
  covers npm's 2FA requirement and the vault package name.

## [2.0.1] — 2026-10-06

### Fixed

- `axi25-onboarding`: the scaffold hint now points to `npx @axi25/core init` (the published
  package) instead of the unpublished `npx axi25 init`.

### Changed

- Relicensed under the [MIT License](LICENSE); the package now publishes publicly.

## [2.0.0] — 2026-07-23

The first release of **AXI25 Core** as a standalone, harness-agnostic vault OS extracted from the
AXI25 vault. Behavior is now a single versioned source of truth that projects into any vault.

### Added

- **Projection engine** (`bin/axi25.mjs`) driven by a declarative `PROJECTIONS` table:
  `init` · `wire` · `update` · `verify` · `doctor`. Zero dependencies, Node ≥ 18.
- **Lockfile guard** (`.axi25-lock.json`) with canonicalized (EOL/BOM/case) content hashes, so
  `verify` is byte-identical on Linux, macOS, and Windows — proven by a CI matrix.
- **Two consumption models** from one repo (npm and git submodule) with identical vault output.
- **Thin `AGENTS.md` router** + on-demand `references/` (progressive disclosure) replacing the former
  monolithic contract.
- **`axi25-source` skill** — cloud-first source acquisition (pip packages + one OpenRouter API key,
  no heavy local ML): book/article/stream/audio handlers; digital-PDF text, vision OCR for
  scanned/garbled pages, and a **design mode** for slides/mind-maps/infographics; **speaker
  diarization with name inference**; model defaults chosen by cost-vs-quality bake-off.
- **Agent Skills spec guard** in the test suite — every `SKILL.md` is validated against
  [agentskills.io](https://agentskills.io) on every run.
- Runtime-artifact isolation: a skill's `.venv/`, `.cache/`, `__pycache__/`, and `.env` are ignored by
  `wire`/`verify` and never committed.

### Changed

- Distribution renamed to the scoped package **`@axi25/core`**.

[Unreleased]: https://github.com/felipefontoura/axi25-core/compare/v2.0.2...HEAD
[2.0.2]: https://github.com/felipefontoura/axi25-core/compare/v2.0.1...v2.0.2
[2.0.1]: https://github.com/felipefontoura/axi25-core/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/felipefontoura/axi25-core/releases/tag/v2.0.0
