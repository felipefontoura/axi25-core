# Contributing to AXI25 Core

Thanks for helping improve the harness-agnostic vault OS. This guide gets you productive fast.

## The one golden rule

**Edit the source, never the projections.**

- The source of truth is `skills/`, `references/`, `AGENTS.md`, and `bin/axi25.mjs`.
- `.claude/skills/`, `.agents/skills/`, and the root context files *inside a vault* are **generated
  copies** written by `wire`. Never hand-edit them — your change would be overwritten and `verify`
  will fail. Change the source, then re-`wire`.

## Setup

You only need **Node ≥ 18** — this project has **zero runtime dependencies**.

```bash
git clone https://github.com/felipefontoura/axi25-core.git
cd axi25-core
node .ci/verify.mjs      # run the full test suite (same as `npm test`)
```

`markdownlint-cli2` (used by `npm run lint`) is fetched on demand via `npx`.

## Run the tests

```bash
npm test        # structural + functional round-trip + Agent Skills spec conformance
npm run lint    # markdownlint over all docs
```

`npm test` (`.ci/verify.mjs`) enforces, among other things:

- **Projection lock** — a fresh `init` must be deterministic, and hand-editing a projected file must
  make `verify` fail.
- **Agent Skills spec** — every `skills/*/SKILL.md` must conform to the
  [agentskills.io](https://agentskills.io) spec: `name` ≤ 64 chars, lowercase/hyphen charset, matching
  its directory; `description` 1–1024 chars; `compatibility` ≤ 500; body under 500 lines; no unknown
  frontmatter keys.
- **Zero symlinks** — real directories only (Windows-safe).

CI runs the same suite on **Linux, macOS, and Windows** (`.github/workflows/ci.yml`). Cross-OS
byte-identical hashing is load-bearing, so all three must pass.

## Adding or changing a skill

1. Create `skills/<name>/SKILL.md` with valid frontmatter (`name` must equal `<name>`). Keep the body
   focused; move deep material into `skills/<name>/references/*.md` (progressive disclosure).
2. Bundled scripts go in `skills/<name>/scripts/`; keep them self-contained and cross-platform (Node
   is the assumed runtime; if you need Python, ship a `pyproject.toml` + `setup.sh`/`setup.ps1` like
   `axi25-source`, and declare requirements in the `compatibility` frontmatter field).
3. Runtime artifacts a skill creates (`.venv/`, `.cache/`, `__pycache__/`, `.env`) are ignored by
   `wire`/`verify` — never commit them.
4. Run `npm test`. The spec guard will reject a non-conforming skill.

## Commits & pull requests

- Keep commits atomic and messages descriptive (imperative mood: "Add X", "Fix Y").
- Open a PR against `main`; the CI matrix must be green.
- Describe **what** changed and **why**; link any related issue.

## Choosing OpenRouter models

If your change touches a model default, justify it with a **bake-off**: run candidates on the same
real input, score on task-specific checks, divide by catalog price, and prefer the cheapest that isn't
beaten. Document the result in `skills/<name>/references/models.md` (see `axi25-source` for the pattern).

By contributing, you agree that your contributions are licensed under the project's [LICENSE](LICENSE),
and that you will follow the [Code of Conduct](CODE_OF_CONDUCT.md).
