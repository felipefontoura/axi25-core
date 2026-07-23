#!/usr/bin/env node
/**
 * axi25-core — verify (the "test" stage). Structural checks + a functional round-trip that
 * must hold on every OS. Exits non-zero on failure.
 *
 *   node .ci/verify.mjs   (or: npm test)
 */
import { promises as fs } from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const CLI = path.join(ROOT, "bin", "axi25.mjs");
const fails = [];
const oks = [];
const ok = (m) => oks.push(m);
const fail = (m) => fails.push(m);

async function exists(p) {
  try {
    await fs.lstat(p);
    return true;
  } catch {
    return false;
  }
}

async function walkSymlinks(dir, out = []) {
  for (const e of await fs.readdir(dir, { withFileTypes: true })) {
    if (["node_modules", ".git"].includes(e.name)) continue;
    const full = path.join(dir, e.name);
    if (e.isSymbolicLink()) out.push(path.relative(ROOT, full));
    else if (e.isDirectory()) await walkSymlinks(full, out);
  }
  return out;
}

function run(args, cwd = ROOT) {
  return spawnSync(process.execPath, [CLI, ...args], { cwd, encoding: "utf8" });
}

// Minimal SKILL.md frontmatter parser — enough to validate against the Agent Skills spec
// (agentskills.io). Folds `key: >` block scalars to one line to measure their length.
function parseFrontmatter(text) {
  const m = text.match(/^---\n([\s\S]*?)\n---/);
  if (!m) return null;
  const lines = m[1].split("\n");
  const fields = {};
  for (let i = 0; i < lines.length; i++) {
    const kv = lines[i].match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (!kv) continue;
    const key = kv[1];
    let val = kv[2];
    if (/^[>|][-+]?$/.test(val)) {
      // folded/literal block scalar: gather more-indented continuation lines
      const parts = [];
      while (i + 1 < lines.length && (/^\s{2,}\S/.test(lines[i + 1]) || lines[i + 1].trim() === "")) {
        parts.push(lines[++i].trim());
      }
      val = parts.join(" ").replace(/\s+/g, " ").trim();
    } else {
      val = val.replace(/^["']|["']$/g, "");
    }
    fields[key] = val;
  }
  return fields;
}

const SKILL_NAME_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/; // lowercase alnum + single hyphens, no lead/trail/double

async function main() {
  // 1. Required files present
  const required = [
    "bin/axi25.mjs", "AGENTS.md", "CLAUDE.md", "package.json", ".gitattributes",
    ".markdownlint-cli2.jsonc",
    "references/definition.md", "references/operations.md", "references/page-templates.md",
    "references/maturity.md", "references/naming.md", "docs/philosophy.md",
    // open-source front-door files (gold standard)
    "README.md", "LICENSE", "CHANGELOG.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md",
    ".editorconfig", ".github/PULL_REQUEST_TEMPLATE.md",
  ];
  for (const f of required) (await exists(path.join(ROOT, f))) || fail(`missing required file: ${f}`);
  ok(`required files present (${required.length})`);

  // 2. Skills: at least 10, each with a SKILL.md
  const skillsDir = path.join(ROOT, "skills");
  const skills = (await fs.readdir(skillsDir, { withFileTypes: true }))
    .filter((d) => d.isDirectory())
    .map((d) => d.name)
    .sort();
  if (skills.length < 10) fail(`too few skills (${skills.length})`);
  for (const s of skills)
    (await exists(path.join(skillsDir, s, "SKILL.md"))) || fail(`skill ${s} missing SKILL.md`);
  ok(`skills present (${skills.length}), each with SKILL.md`);

  // 2b. Every SKILL.md conforms to the Agent Skills spec (agentskills.io):
  //     name (≤64, lowercase/hyphen charset, matches dir), description (1-1024), compatibility
  //     (≤500 if present), body < 500 lines. A permanent guard so no skill drifts out of spec.
  const KNOWN_KEYS = new Set(["name", "description", "license", "compatibility", "metadata", "allowed-tools"]);
  let specViol = 0;
  for (const s of skills) {
    const text = await fs.readFile(path.join(skillsDir, s, "SKILL.md"), "utf8");
    const fm = parseFrontmatter(text);
    const v = (m) => { specViol++; fail(`${s}/SKILL.md: ${m}`); };
    if (!fm) { v("no YAML frontmatter"); continue; }
    const name = fm.name || "";
    const desc = (fm.description || "").trim();
    const compat = fm.compatibility || "";
    if (name !== s) v(`name '${name}' must match directory '${s}'`);
    if (!SKILL_NAME_RE.test(name) || name.length > 64) v(`name '${name}' violates charset/length`);
    if (!desc) v("description is empty");
    if (desc.length > 1024) v(`description ${desc.length} chars > 1024`);
    if (compat && compat.length > 500) v(`compatibility ${compat.length} chars > 500`);
    const bodyLines = text.split("\n").length;
    if (bodyLines > 500) v(`SKILL.md ${bodyLines} lines > 500 (progressive disclosure)`);
    for (const k of Object.keys(fm)) if (!KNOWN_KEYS.has(k)) v(`unknown frontmatter key '${k}'`);
  }
  if (specViol === 0) ok(`all ${skills.length} skills conform to the Agent Skills spec (agentskills.io)`);

  // 3. Zero symlinks (Windows-safe)
  const links = await walkSymlinks(ROOT);
  links.length === 0 ? ok("zero symlinks (Windows-safe)") : fail(`found symlink(s): ${links.slice(0, 5).join(", ")}`);

  // 4. Functional round-trip in a scratch vault
  const scratch = await fs.mkdtemp(path.join(os.tmpdir(), "axi25-verify-"));
  try {
    const a = run(["init", scratch]);
    a.status === 0 ? ok("init: scaffolds + wires a fresh vault") : fail(`init failed: ${a.stderr || a.stdout}`);

    // core-owned projections exist; user data exists and carries the fresh marker
    for (const f of ["AGENTS.md", ".agents/skills", ".claude/skills", ".axi25-lock.json",
                     "90-system/references/maturity.md", "opencode.json", "CLAUDE.md"])
      (await exists(path.join(scratch, f))) || fail(`init did not produce: ${f}`);
    const prof = await fs.readFile(path.join(scratch, "90-system/references/user-profile.md"), "utf8");
    prof.includes("ONBOARDING PENDING") ? ok("fresh vault ships ONBOARDING PENDING") : fail("user-profile missing fresh marker");

    const v1 = run(["verify", scratch]);
    v1.status === 0 ? ok("verify: passes on a freshly wired vault") : fail(`verify failed after init: ${v1.stdout}`);

    // determinism: a second wire into a different dir yields identical projection hashes
    const scratch2 = await fs.mkdtemp(path.join(os.tmpdir(), "axi25-verify-"));
    run(["init", scratch2]);
    const l1 = JSON.parse(await fs.readFile(path.join(scratch, ".axi25-lock.json"), "utf8"));
    const l2 = JSON.parse(await fs.readFile(path.join(scratch2, ".axi25-lock.json"), "utf8"));
    JSON.stringify(l1.projections) === JSON.stringify(l2.projections)
      ? ok("lock is deterministic (identical projections across runs)")
      : fail("lock projections differ across runs (non-deterministic hashing)");
    await fs.rm(scratch2, { recursive: true, force: true });

    // guard: hand-editing a projected file makes verify fail
    await fs.appendFile(path.join(scratch, "AGENTS.md"), "\n<!-- tampered -->\n");
    const v2 = run(["verify", scratch]);
    v2.status !== 0 ? ok("verify: catches a hand-edited projection (guard works)") : fail("verify passed on a tampered vault (guard broken)");
  } finally {
    await fs.rm(scratch, { recursive: true, force: true });
  }

  // Report
  for (const m of oks) process.stdout.write(`  \x1b[32m✓\x1b[0m ${m}\n`);
  for (const m of fails) process.stdout.write(`  \x1b[31m✗\x1b[0m ${m}\n`);
  if (fails.length) {
    process.stderr.write(`\n  FAILED: ${fails.length} check(s)\n`);
    process.exit(1);
  }
  process.stdout.write(`\n  All checks passed.\n`);
}

main().catch((e) => {
  process.stderr.write(`\n  verify error: ${e.stack || e.message}\n`);
  process.exit(1);
});
