---
name: axi25-doctor
description: >
  Environment setup & repair for AXI25 — the harness detects what's installed,
  explains what's missing, and (with the user's consent) installs it FOR them,
  transparently. Use when the user says "doctor", "check my setup", "install
  dependencies", "set up my environment", "something's missing", "install
  node/python/git", "fix my install", or when ANY other skill hits a missing tool
  (e.g. git, node, markdownlint). The mission: make AXI25 usable from day zero —
  the user should never be left to fight a terminal alone. Cross-platform: Linux,
  macOS, Windows. Read-only detection by default; installs ONLY with explicit
  consent, always showing the exact command first.
---

# Doctor — Environment Setup & Repair

Your job: get the user from "just downloaded a zip" to "working AXI25" without making
them fight the terminal. Detect what's there, explain what's missing in plain language,
and — with a clear yes — install it for them, showing every command you run.

**Voice**: Respond in the language the user is speaking (see `90-system/references/user-profile.md`).

## Golden rules

1. **Detection is free; installation needs consent.** Never install, upgrade, or run `sudo`
   without the user's explicit "yes", and always show the exact command first.
2. **Be transparent.** Print the command, run it, show the result. No hidden magic.
3. **Prefer the least invasive path.** Official installer or the user's existing package
   manager over ad-hoc scripts. Never pipe-to-shell from an untrusted URL.
4. **Don't over-install.** AXI25 itself needs almost nothing (see below). Only install what
   the user's chosen path actually requires. When in doubt, ask.
5. **One thing at a time, gently.** Explain why each dependency matters; let the user opt out
   of any of them and still use the core system.

## What AXI25 actually needs

| Component | Needed for | Required? |
|---|---|---|
| A running AI agent (Claude Code / Codex / OpenCode / Pi) | operating the vault at all | **yes** (this is already running if you're reading this) |
| A text editor / Obsidian | reading & editing notes | recommended (Obsidian for the friendly path) |
| **git** | version history + backup of your vault | strongly recommended |
| **Node.js + npm** | installing the AI-agent CLIs and the Obsidian AXI25 wrapper | only for those paths |
| Python / uv, ffmpeg, ML models | NOT used in this edition (reserved for Pro add-on skills) | no |

The core vault is plain Markdown — it runs with just an agent and an editor. Everything else
is about the *harness* and *backups*, not the knowledge system.

## Flow

### 1. Detect the OS and package manager

```bash
uname -s                 # Linux / Darwin (macOS)
# Windows: you'll be in PowerShell — check $PSVersionTable / winget
```
Then detect an available package manager (first that exists):

- macOS: `brew`
- Linux: `apt-get` / `dnf` / `pacman` / `zypper`
- Windows: `winget` / `choco` / `scoop`

If none exists on macOS/Windows, offer to install one (Homebrew on macOS; winget ships with
modern Windows) — with consent.

### 2. Check what's present

Run quiet checks and build a small status table for the user:

```bash
command -v git node npm python3 claude codex opencode 2>/dev/null
git --version; node --version; npm --version
```

Present it warmly:

> Here's your setup:
>
> - ✅ git 2.45
> - ✅ Node 20.11
> - ❌ Claude Code CLI — not installed
>
> Want me to install Claude Code for you? I'll run `npm install -g @anthropic-ai/claude-code`.

### 3. Install missing pieces — with consent, transparently

For each missing item the user's path needs, propose the exact command for their OS/manager,
then run it on a yes. Reference commands (adapt to the detected manager):

**git**

- macOS: `brew install git` (or it ships with Xcode CLT: `xcode-select --install`)
- Debian/Ubuntu: `sudo apt-get update && sudo apt-get install -y git`
- Fedora: `sudo dnf install -y git` · Arch: `sudo pacman -S --noconfirm git`
- Windows: `winget install --id Git.Git -e`

**Node.js + npm** (for the agent CLIs / AXI25)

- macOS: `brew install node`
- Debian/Ubuntu: `sudo apt-get install -y nodejs npm` (or nvm for a current version)
- Fedora: `sudo dnf install -y nodejs` · Arch: `sudo pacman -S --noconfirm nodejs npm`
- Windows: `winget install --id OpenJS.NodeJS.LTS -e`
- No-sudo alternative (any OS): install `nvm` and `nvm install --lts`.

**The AI agent CLI** (only the one the user chose)

- Claude Code: `npm install -g @anthropic-ai/claude-code`, then `claude` to sign in
- OpenAI Codex: `npm install -g @openai/codex` (or `brew install codex`), then `codex`
- OpenCode: see https://opencode.ai (guide the user to the official installer)
- Pi.dev: see https://pi.dev

**Obsidian** (friendly path): guide the download from https://obsidian.md (GUI app — you
can't install it silently everywhere; walk them through it). Then the AXI25 plugin is
installed via BRAT inside Obsidian (see `SETUP.md`).

After each install, **verify**: re-run `command -v <tool>` / `<tool> --version` and confirm.

### 4. Offer to initialize git (backup)

If git is present but the vault isn't a repo yet, offer:

```bash
git init && git add -A && git commit -m "AXI25 — initial vault"
```

Explain: this gives them local, private version history — their undo button and backup. Never
push anywhere without asking.

### 5. Hand back

Summarize what's now installed and what's next (usually: run `onboarding`). Leave one clear
next step.

## When another skill calls you

If a skill needs a tool that's missing (e.g. `axi25-lint` wants `markdownlint-cli2`, which
runs via `npx` and needs Node), pause that skill, run this doctor flow for just that tool,
then resume. Don't fail silently — guide the fix.

## Safety

- Show every command before running it. Get a yes for anything that writes, installs, or uses `sudo`.
- Never run remote scripts you can't show the user.
- If the user declines a dependency, respect it — explain what they lose and continue with what works.
- On Windows, prefer `winget`; if PowerShell blocks a script, tell them to run it with
  `-ExecutionPolicy Bypass` for that one command rather than changing global policy.
