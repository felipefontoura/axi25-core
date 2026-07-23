# Security Policy

## Reporting a vulnerability

Please **do not** open a public issue for security problems.

Report vulnerabilities privately via <https://felipefontoura.com/contact/> (subject: `axi25-core security`), or via
GitHub's [private security advisory](https://github.com/felipefontoura/axi25-core/security/advisories/new)
feature. We aim to acknowledge within 72 hours and to provide a remediation timeline after triage.

Please include: a description, reproduction steps, affected version, and impact.

## Supported versions

Security fixes target the latest published `2.x` release. Older majors are not maintained.

## Scope & things to know

AXI25 Core is a projection/scaffolding tool plus Agent Skills. A few properties are relevant to
security review:

- **Zero runtime dependencies** and **no network access** in the core CLI (`bin/axi25.mjs`) — it only
  reads/writes the local filesystem and never executes downloaded code.
- **No symlinks** are ever created; projections are real file copies.
- **Skills may run code and call external APIs.** The `axi25-source` skill, when set up, runs a Python
  engine that sends media to the **OpenRouter API** and reads an `OPENROUTER_API_KEY` from a local
  `.env`. Secrets live only in that gitignored `.env`; they are never committed or projected. Review
  `skills/axi25-source/` before enabling it, and treat its `.env` as sensitive.
- Report anything that could cause the tool to **write outside the target vault**, **execute untrusted
  code**, or **leak a secret** into a committed/projected file — those are the highest-severity classes.
