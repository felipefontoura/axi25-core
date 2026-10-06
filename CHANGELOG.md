# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/felipefontoura/axi25-core/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/felipefontoura/axi25-core/releases/tag/v2.0.0
