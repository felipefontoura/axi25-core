# Maintenance runbooks

Operational recipes for running AXI25 Core across vaults and releasing new versions. For the *why*
behind these mechanics, see [`docs/architecture.md`](architecture.md).

Throughout, "the core CLI" is `bin/axi25.mjs`. In a submodule vault you run it as
`node .axi25/bin/axi25.mjs <cmd> .`; via npm it's `npx @axi25/core <cmd>`.

## Scaffold a new vault

```bash
npx @axi25/core init my-vault      # folder tree + anchors + wired core
# then open my-vault/ in your agent and type:  onboarding
```

## Update the core in an existing vault

The vault's projected files are regenerated from the core, so an update is: **refresh the source,
re-wire, verify, commit.**

**Submodule vault** (the `.axi25/` model):

```bash
git submodule update --remote .axi25        # pull the latest main into the submodule
node .axi25/bin/axi25.mjs wire .            # re-project into the vault
node .axi25/bin/axi25.mjs verify .          # confirm the lock matches
git add -A && git commit -m "Update axi25-core"
```

**npm vault** (the snapshot model):

```bash
npx @axi25/core@latest update               # rewrite projections from the latest published version
npx @axi25/core verify
git add -A && git commit -m "Update axi25-core"
```

`verify` failing after a wire means a projected file was hand-edited — fix it in the **core**, not
in the vault, then re-wire.

## Repoint an existing vault to consume the core

> **Repointing requires a clean working tree.** `wire` overwrites `AGENTS.md`, `CLAUDE.md`,
> `opencode.json`, the skill dirs, and some references. If the vault has uncommitted work, commit
> (or stash) it *first* — otherwise the repoint tangles with your WIP. Learned the hard way.

```bash
# 0. make sure the vault is clean
git -C my-vault status --porcelain        # must be empty

# 1. add the core as a submodule tracking main
git -C my-vault submodule add -b main https://github.com/felipefontoura/axi25-core.git .axi25

# 2. project it in
node my-vault/.axi25/bin/axi25.mjs wire my-vault

# 3. review the diff (AGENTS.md swaps the old contract for the thin router) and commit
git -C my-vault add -A
git -C my-vault commit -m "Adopt @axi25/core as a submodule; wire its projections"
```

The old inline `AGENTS.md` is replaced by the core's thin router — that is intentional. Any
project-specific content that used to live in `AGENTS.md` belongs in `user-profile.md` (the
personalization seam) or a separate vault doc, not in the generated file.

## Add or change a skill

1. Edit the **source** in `skills/<name>/` (never a vault's projected copy).
2. `npm test` — the suite enforces the projection round-trip and Agent Skills spec conformance.
3. If you touched a model default, justify it in `skills/<name>/references/models.md` with a bake-off
   (same real input across candidates, score per task, divide by price; prefer the cheapest that
   isn't beaten). See `axi25-source` for the pattern.
4. Commit, open a PR, let the three-OS CI matrix go green.
5. Consumers pick it up on their next update (above).

## Release a new version

Versions follow [SemVer](https://semver.org). The version lives in `package.json`.

```bash
# 1. bump the version + add a CHANGELOG entry
#    (edit package.json "version" and CHANGELOG.md's [Unreleased] → [x.y.z])
npm test && npm run lint                     # green locally
git add -A && git commit -m "Release vX.Y.Z"
git tag vX.Y.Z
git push origin main --tags

# 2. (once OSS — see below) publish to npm
npm publish
```

Submodule consumers move to the new version with `git submodule update --remote .axi25 && wire`;
npm consumers with `npx @axi25/core@latest update`.

## Re-run a model bake-off

When the OpenRouter catalog shifts, re-validate the model defaults: render/clip the same real input,
run each candidate, score on task-specific checks (phrase fidelity for STT/diarization, structure +
connections for design, word-count kept for cleanup), divide by the catalog price, and prefer the
cheapest that isn't beaten. Prefer open-weight models for anything reproducing copyrighted text
(`is_moderated: false`). Record the outcome in the relevant `references/models.md`.
