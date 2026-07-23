#!/usr/bin/env node
/**
 * axi25 — the harness-agnostic core CLI.
 *
 * Projects the AXI25 "OS" (skills + contract + reference docs) into a vault so it works,
 * with zero setup, on Claude Code, OpenAI Codex, OpenCode and Pi. Zero dependencies.
 * Node >= 18. The runtime IS the environment: all logic lives here, in portable Node —
 * the shell wrappers only relaunch this file. No symlinks (Windows-safe); hashes are
 * canonicalized (EOL/BOM/case) so `verify` is byte-identical on Linux, macOS and Windows.
 *
 *   npx @axi25/core init   [dir]   scaffold a fresh vault (tree + anchors) and wire it
 *   npx @axi25/core wire   [dir]   project the core into a vault
 *   npx @axi25/core update [dir]   npm-mode alias for wire (pulls the installed core version)
 *   npx @axi25/core verify [dir]   guard: assert projections match the lockfile (for CI)
 *   npx @axi25/core doctor [dir]   environment + freshness check
 *   npx @axi25/core --help
 *
 * The distribution model is chosen by WHICH cli you invoke, not by config:
 *   `npx @axi25/core …`                 → projects the npm version (from = this package)
 *   `node .axi25/bin/axi25.mjs …` → projects the submodule    (from = .axi25/)
 * The vault output is identical either way — only the source (`--from`) differs.
 */
import { promises as fs } from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const CORE_ROOT = path.resolve(HERE, ".."); // the core package this CLI belongs to = default --from

// ─── The projection table: the single source of what `wire` writes and `verify` checks ──────
// kind: "tree" (copy a directory) | "file" (copy a file) | "config" (templated surface).
// `from` is relative to the core root; `to` is relative to the vault root.
const PROJECTIONS = [
  { kind: "tree", from: "skills", to: ".agents/skills" }, // Codex · OpenCode · Pi
  { kind: "tree", from: "skills", to: ".claude/skills", mark: "GENERATED-DO-NOT-EDIT" }, // Claude Code
  { kind: "file", from: "AGENTS.md", to: "AGENTS.md" }, // Codex · Pi (literal at root)
  { kind: "file", from: "references/definition.md", to: "90-system/references/axi25-definition.md" },
  { kind: "file", from: "references/operations.md", to: "90-system/references/operations.md" },
  { kind: "file", from: "references/page-templates.md", to: "90-system/references/page-templates.md" },
  { kind: "file", from: "references/maturity.md", to: "90-system/references/maturity.md" },
  { kind: "file", from: "references/naming.md", to: "90-system/references/naming.md" },
  { kind: "file", from: ".markdownlint-cli2.jsonc", to: ".markdownlint-cli2.jsonc" },
  { kind: "config", to: "CLAUDE.md" }, // Claude Code entry → imports AGENTS.md
  { kind: "config", to: "opencode.json" }, // OpenCode config → points instructions at AGENTS.md
];

// Templated surfaces: content is GENERATED (not copied), so it can merge non-destructively
// with a user's pre-existing file. Everything else in PROJECTIONS is a byte-faithful copy.
const CONFIG_SURFACES = {
  "CLAUDE.md": () => "@AGENTS.md\n",
  "opencode.json": (existing) => {
    let obj = {};
    if (existing) {
      try {
        obj = JSON.parse(existing);
      } catch {
        obj = {};
      }
    }
    obj.$schema ||= "https://opencode.ai/config.json";
    const ins = new Set(Array.isArray(obj.instructions) ? obj.instructions : []);
    ins.add("AGENTS.md");
    obj.instructions = [...ins];
    obj["//"] = "the `instructions` entry is managed by `axi25 wire`";
    return JSON.stringify(obj, null, 2) + "\n";
  },
};

// ─── The vault skeleton (created by `init`; never overwritten if present) ───────────────────
const DIRS = [
  "00-capture/quick", "00-capture/diary", "00-capture/studies", "00-capture/worklogs",
  "10-sources/articles", "10-sources/books", "10-sources/courses", "10-sources/papers", "10-sources/assets",
  "20-wiki/concepts", "20-wiki/entities", "20-wiki/areas", "20-wiki/decisions",
  "20-wiki/patterns", "20-wiki/syntheses", "20-wiki/maps",
  "25-studies",
  "30-projects/active", "30-projects/someday", "30-projects/archive",
  "35-worklogs/harvest",
  "40-journal/daily", "40-journal/weekly", "40-journal/signals",
  "50-zeitgeist/discourse/articles", "50-zeitgeist/discourse/papers",
  "50-zeitgeist/discourse/threads", "50-zeitgeist/discourse/talks",
  "50-zeitgeist/syntheses", "50-zeitgeist/observations",
  "90-system/references", "90-system/prompts", "90-system/scripts",
];

const ANCHORS = {
  "index.md": `---\ntype: index\nupdated: ""\n---\n\n# Index — Wiki Catalog\n\n> The agent maintains this catalog of your \`20-wiki/\` pages. Empty for now — it fills as you build.\n`,
  "log.md": `# Operations Log\n\n> Append-only record of ingests, processing, and wiki changes. The agent writes here.\n\n<!-- entries start below this line -->\n`,
  "90-system/references/user-profile.md":
    `---\ntype: system-reference\nname: ""\nlanguage: ""\nfilename_language: match\ndate_format: ISO 8601\nset_up_on: ""\nworks_with_media: false\n---\n\n<!-- ONBOARDING PENDING -->\n<!--\n  This vault has not been set up. While this marker is present, run the\n  \`axi25-onboarding\` skill first. Onboarding fills this file and removes the marker.\n-->\n\n# User Profile\n\n> Every skill reads this file for your name, language, and areas. Onboarding writes it.\n`,
};

// ─── Portability primitives: canonicalize before hashing so results match on any OS ─────────
const TEXT_RE = /\.(md|mjs|js|ts|json|jsonc|sh|ps1|txt|ya?ml)$/i;

function canon(buf) {
  let s = buf.toString("utf8");
  if (s.charCodeAt(0) === 0xfeff) s = s.slice(1); // strip UTF-8 BOM (editors / PowerShell)
  return Buffer.from(s.replace(/\r\n?/g, "\n"), "utf8"); // CRLF / CR → LF
}
const digest = (buf) => "sha256:" + crypto.createHash("sha256").update(buf).digest("hex");
const fileHash = (rel, bytes) => digest(TEXT_RE.test(rel) ? canon(bytes) : bytes);
const posix = (p) => p.split(path.sep).join("/");
const fromPosix = (rel) => rel.split("/").join(path.sep);

// Runtime artifacts a skill may create at run/setup time (e.g. axi25-source's Python venv).
// They live INSIDE a projected skill dir but must never be copied, hashed, or committed —
// otherwise a user running setup.sh would break `verify`. Excluded from copyTree + treeHash.
const RUNTIME_DIRS = new Set([".venv", ".cache", "__pycache__", "node_modules", ".git"]);
const RUNTIME_SUFFIX = [".pyc", ".pyo", ".stt_tmp", ".groq_tmp"];
const isRuntimeArtifact = (name) =>
  name === ".env" || RUNTIME_DIRS.has(name) || RUNTIME_SUFFIX.some((s) => name.endsWith(s));

async function exists(p) {
  try {
    await fs.lstat(p);
    return true;
  } catch {
    return false;
  }
}
async function readIfExists(p) {
  try {
    return await fs.readFile(p, "utf8");
  } catch {
    return null;
  }
}

// Sorted list of file relpaths under `dir` (posix), excluding the generated marker.
async function listTree(dir) {
  const out = [];
  const rec = async (d, rel) => {
    for (const e of await fs.readdir(d, { withFileTypes: true })) {
      if (e.name === "GENERATED-DO-NOT-EDIT" || isRuntimeArtifact(e.name)) continue;
      const r = rel ? `${rel}/${e.name}` : e.name;
      if (e.isSymbolicLink()) continue;
      if (e.isDirectory()) await rec(path.join(d, e.name), r);
      else out.push(r);
    }
  };
  await rec(dir, "");
  return out.sort();
}

// Fail loudly on names that differ only by case — they collide on macOS/Windows (case-insensitive).
function assertNoCaseCollision(rels) {
  const seen = new Map();
  for (const r of rels) {
    const k = r.toLowerCase();
    if (seen.has(k) && seen.get(k) !== r)
      throw new Error(`case-insensitive filename collision: "${seen.get(k)}" vs "${r}"`);
    seen.set(k, r);
  }
}

async function treeHash(dir) {
  const rels = await listTree(dir);
  assertNoCaseCollision(rels);
  const h = crypto.createHash("sha256");
  for (const r of rels) {
    const bytes = await fs.readFile(path.join(dir, fromPosix(r)));
    h.update(r).update("\0").update(TEXT_RE.test(r) ? canon(bytes) : bytes).update("\0");
  }
  return "sha256:" + h.digest("hex");
}

// Copy a directory as a REAL tree (never a symlink); replaces the destination.
async function copyTree(src, dst) {
  await fs.rm(dst, { recursive: true, force: true });
  await fs.mkdir(dst, { recursive: true });
  const rec = async (s, d) => {
    for (const e of await fs.readdir(s, { withFileTypes: true })) {
      if (e.isSymbolicLink() || isRuntimeArtifact(e.name)) continue;
      const sp = path.join(s, e.name);
      const dp = path.join(d, e.name);
      if (e.isDirectory()) {
        await fs.mkdir(dp, { recursive: true });
        await rec(sp, dp);
      } else {
        await fs.copyFile(sp, dp);
      }
    }
  };
  await rec(src, dst);
}

async function readCoreVersion(from) {
  const pkg = await readIfExists(path.join(from, "package.json"));
  if (!pkg) return "unknown";
  try {
    return JSON.parse(pkg).version || "unknown";
  } catch {
    return "unknown";
  }
}

// ─── wire: project the core into a vault, guided entirely by PROJECTIONS ─────────────────────
async function wire({ from = CORE_ROOT, to = process.cwd(), dryRun = false, writeLock = true } = {}) {
  from = path.resolve(from);
  to = path.resolve(to);
  const source = from.startsWith(to + path.sep) ? "submodule" : "npm";
  const version = await readCoreVersion(from);
  const projections = {};
  const written = [];

  for (const p of PROJECTIONS) {
    const dst = path.join(to, fromPosix(p.to));
    if (p.kind === "tree") {
      const srcDir = path.join(from, p.from);
      if (!dryRun) {
        await copyTree(srcDir, dst);
        if (p.mark) await fs.writeFile(path.join(dst, p.mark), "");
      }
      projections[p.to] = await treeHash(dryRun ? srcDir : dst);
      written.push(p.to + "/");
    } else if (p.kind === "file") {
      const bytes = await fs.readFile(path.join(from, p.from));
      if (!dryRun) {
        await fs.mkdir(path.dirname(dst), { recursive: true });
        await fs.writeFile(dst, bytes);
      }
      projections[p.to] = fileHash(p.to, bytes);
      written.push(p.to);
    } else if (p.kind === "config") {
      const content = CONFIG_SURFACES[p.to](await readIfExists(dst));
      if (!dryRun) {
        await fs.mkdir(path.dirname(dst), { recursive: true });
        await fs.writeFile(dst, content);
      }
      projections[p.to] = fileHash(p.to, Buffer.from(content));
      written.push(p.to);
    }
  }

  const lock = {
    core: "@axi25/core",
    source,
    version,
    wiredAt: new Date().toISOString(),
    projections,
  };
  if (writeLock && !dryRun)
    await fs.writeFile(path.join(to, ".axi25-lock.json"), JSON.stringify(lock, null, 2) + "\n");
  return { source, version, written, lock };
}

async function vaultTargetHash(to, p) {
  if (p.kind === "tree") return treeHash(path.join(to, fromPosix(p.to)));
  return fileHash(p.to, await fs.readFile(path.join(to, fromPosix(p.to))));
}

// ─── verify: the guard. vault must match the lock; if the core source is in-tree, it too. ────
async function verify({ to = process.cwd(), from } = {}) {
  to = path.resolve(to);
  const fails = [];
  const raw = await readIfExists(path.join(to, ".axi25-lock.json"));
  if (!raw) return { ok: false, fails: ["no .axi25-lock.json — run `axi25 wire`"] };
  let lock;
  try {
    lock = JSON.parse(raw);
  } catch {
    return { ok: false, fails: [".axi25-lock.json is not valid JSON"] };
  }

  // If from wasn't passed but a populated submodule exists, use it for the staleness check.
  if (!from && (await exists(path.join(to, ".axi25", "package.json")))) from = path.join(to, ".axi25");

  for (const p of PROJECTIONS) {
    const want = lock.projections[p.to];
    if (!want) {
      fails.push(`${p.to}: not in lock (run: axi25 wire)`);
      continue;
    }
    let got;
    try {
      got = await vaultTargetHash(to, p);
    } catch {
      fails.push(`${p.to}: missing in vault (run: axi25 wire)`);
      continue;
    }
    if (got !== want) fails.push(`${p.to}: hand-edited — differs from lock (change upstream, then wire)`);

    // staleness: core source moved but wire wasn't re-run (only checkable for copied projections)
    if (from && p.kind !== "config") {
      const srcHash =
        p.kind === "tree"
          ? await treeHash(path.join(from, p.from))
          : fileHash(p.to, await fs.readFile(path.join(from, p.from)));
      if (srcHash !== want) fails.push(`${p.to}: core changed but not wired (run: axi25 wire)`);
    }
  }
  return { ok: fails.length === 0, fails, lock };
}

// ─── scaffolding ────────────────────────────────────────────────────────────────────────────
async function ensureSkeleton(root) {
  for (const dir of DIRS) {
    const abs = path.join(root, fromPosix(dir));
    await fs.mkdir(abs, { recursive: true });
    const keep = path.join(abs, ".keep");
    if (!(await exists(keep))) await fs.writeFile(keep, "");
  }
  for (const [rel, content] of Object.entries(ANCHORS)) {
    const abs = path.join(root, fromPosix(rel));
    await fs.mkdir(path.dirname(abs), { recursive: true });
    if (!(await exists(abs))) await fs.writeFile(abs, content);
  }
}

// ─── environment probe (cross-OS; honours PATHEXT on Windows) ────────────────────────────────
async function onPath(name) {
  const dirs = (process.env.PATH || "").split(path.delimiter).filter(Boolean);
  const exts = process.platform === "win32" ? (process.env.PATHEXT || ".EXE;.CMD;.BAT").split(";") : [""];
  for (const d of dirs) {
    for (const ext of exts) {
      if (await exists(path.join(d, name + ext))) return true;
      if (await exists(path.join(d, name + ext.toLowerCase()))) return true;
    }
  }
  return false;
}

// ─── output helpers ──────────────────────────────────────────────────────────────────────────
const log = (m) => process.stdout.write(`  ${m}\n`);
const ok = (m) => log(`\x1b[32m✓\x1b[0m ${m}`);
const warn = (m) => log(`\x1b[33m!\x1b[0m ${m}`);
const bad = (m) => log(`\x1b[31m✗\x1b[0m ${m}`);

// ─── commands ────────────────────────────────────────────────────────────────────────────────
async function cmdInit(dir) {
  const root = path.resolve(dir || ".");
  log("");
  log(`AXI25 — scaffolding a vault into ${root}`);
  log("=".repeat(30));
  await ensureSkeleton(root);
  ok("Folder tree + anchor files ready");
  const r = await wire({ to: root });
  ok(`Wired the ${r.source} core (v${r.version}) — ${r.written.length} projections`);
  log("");
  ok("Done. Open the folder in Claude Code / Codex / OpenCode / Pi and type: onboarding");
  log("");
}

async function cmdWire(dir, from) {
  const root = path.resolve(dir || ".");
  log("");
  await ensureSkeleton(root);
  const r = await wire({ to: root, from: from || CORE_ROOT });
  for (const w of r.written) ok(`projected ${w}`);
  ok(`Wired the ${r.source} core (v${r.version}). Lock: .axi25-lock.json`);
  log("");
}

async function cmdVerify(dir, from) {
  const root = path.resolve(dir || ".");
  log("");
  log("AXI25 — verify projections");
  log("=".repeat(30));
  const r = await verify({ to: root, from });
  if (r.ok) {
    ok("All projections match the lock.");
    log("");
    return;
  }
  for (const f of r.fails) bad(f);
  process.stderr.write(`\n  FAILED: ${r.fails.length} check(s)\n`);
  process.exit(1);
}

async function cmdDoctor(dir) {
  const root = path.resolve(dir || ".");
  log("");
  log("AXI25 — environment check");
  log("=".repeat(30));
  const probe = ["claude", "codex", "opencode", "pi", "node", "git"];
  const has = {};
  for (const c of probe) has[c] = await onPath(c);
  const mark = (b) => (b ? "\x1b[32m✓\x1b[0m" : "\x1b[33m—\x1b[0m");
  for (const c of probe) log(`${mark(has[c])} ${c}`);

  const lockRaw = await readIfExists(path.join(root, ".axi25-lock.json"));
  if (lockRaw) {
    try {
      const lock = JSON.parse(lockRaw);
      const core = await readCoreVersion(CORE_ROOT);
      log("");
      if (lock.version === core) ok(`Vault is on core v${lock.version} (current).`);
      else warn(`Vault is on core v${lock.version}; this CLI ships v${core} — run: axi25 wire`);
    } catch {
      warn(".axi25-lock.json is unreadable — run: axi25 wire");
    }
  }

  const agents = ["claude", "codex", "opencode", "pi"].filter((a) => has[a]);
  log("");
  if (agents.length) ok(`Ready with: ${agents.join(", ")}. In the vault, type: onboarding`);
  else warn("No agent CLI on PATH — install one (Claude Code / Codex / OpenCode / Pi).");
  if (!has.node) warn("Node.js is required — https://nodejs.org");
  if (!has.git) log("Tip: install git for backup/version history and submodule-mode core.");
  log("");
}

function help() {
  process.stdout.write(`
axi25 — harness-agnostic vault core (Claude Code · Codex · OpenCode · Pi)

  npx @axi25/core init   [dir]   Scaffold a fresh vault and wire the core
  npx @axi25/core wire   [dir]   Project the core into a vault
  npx @axi25/core update [dir]   npm-mode alias for wire
  npx @axi25/core verify [dir]   Assert projections match the lockfile (CI guard)
  npx @axi25/core doctor [dir]   Check environment + core freshness
  npx @axi25/core --help

The runtime is Node (zero deps). No symlinks; hashes are canonicalized so verify is
byte-identical on Linux, macOS and Windows.
`);
}

const [cmd, arg] = process.argv.slice(2);
try {
  if (cmd === "init") await cmdInit(arg);
  else if (cmd === "wire") await cmdWire(arg);
  else if (cmd === "update") await cmdWire(arg); // npm-mode alias
  else if (cmd === "verify") await cmdVerify(arg);
  else if (cmd === "doctor" || cmd === "check") await cmdDoctor(arg);
  else help();
} catch (err) {
  process.stderr.write(`\n  Error: ${err.message}\n`);
  process.exit(1);
}
