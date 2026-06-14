---
name: audit-repo-for-agents
description: "Check a repository's integrity and security posture BEFORE (or while) letting AI coding agents — Claude Code, Codex, Gemini CLI, Cursor, aider — work in it. Sanity-checks for leaked secrets, PII/identity exposure, unsafe agent config and permissions, prompt-injection surface, and risky execution/network boundaries, then gives intuitive remediation and a go/no-go verdict. Keeps the repo private-by-default but functional. Trigger when the user wants to secure a repo for agent use, audit repo security posture, prep a repo to go public, or vet what an agent can access/leak. Do not trigger for auditing a single skill file (use vet-skill) or app-level threat modeling (use security-threat-model)."
# --- provenance ---
category: engineering
source: self-authored (this repository)
author: Sharquille Andrew
license: MIT
retrieved: 2026-06-14
# grounded in: the repo's own hardening practices + public guidance (gitleaks/
# trufflehog/ggshield secret scanning, OWASP LLM Top 10 prompt injection,
# GitHub secret push-protection, .gitignore deny-by-default).
---

# Audit Repo for Agents

Before an AI agent (Claude Code, Codex, Gemini CLI, Cursor, aider, …) works in a
repo, make sure the repo can't leak secrets or personal data, can't be steered by
injected instructions, and grants the agent only the access it needs. AI-assisted
commits leak secrets at roughly **2× the human baseline**, and agents have deep
local reach (files, env vars, terminals, credential stores) — so the repo's
posture is part of your attack surface. The goal: **private-by-default, still
fully functional.**

## When to use

- Preparing a repo for an AI agent to work in, or onboarding a new agent.
- Before taking a repo (or agent-config) **public**.
- Periodic posture check on a repo agents already use.
- After adding agent config (`.claude/`, `.cursor/`, MCP servers, hooks).

## When NOT to use

- Auditing a single downloaded skill file → use `vet-skill`.
- Application-level threat modeling of the code itself → use `security-threat-model`.

## What an agent can do in a repo (the threat model)

Assume the agent will: **read every file** (including untrusted content like
READMEs, issues, vendored data, `AGENTS.md`/`CLAUDE.md`), **run commands** (some
auto-approved), **reach the network**, and **see environment variables and
credentials** in scope. Each is a vector:

| Vector | Risk |
|--------|------|
| Files it reads | Secret/PII disclosure; **prompt injection** from untrusted text |
| Commands it runs | Arbitrary execution via over-broad permissions or malicious hooks |
| Network it reaches | Exfiltration of code/secrets to third parties |
| Config it inherits | Local settings, tokens, transcripts committed by accident |

## Workflow

### 1) Run the automated audit
```text
scripts/repo-agent-audit.sh [repo-path]   # defaults to current dir
```
Read-only. It reports findings across the sections below and prints a go/no-go
verdict. Triage every finding — it flags, you judge.

### 2) Secrets & credentials (highest priority)
- No secrets in tracked files **or git history**: API keys, tokens, `.env`,
  `*.pem`/`*.key`, `id_rsa`, `.credentials.json`.
- Prefer a real scanner when available: `gitleaks detect`, `trufflehog git`, or
  `ggshield secret scan repo`. Post-commit scanning alone is weak — add a
  **pre-commit hook** and CI scan so it can't recur.
- If a secret was ever committed: **rotate it first** (assume it's compromised),
  then purge from history (`git filter-repo`), then add the scanner.

### 3) Privacy / PII / identity
- No real home paths (`/Users/<you>`, `/home/<you>`), internal hostnames, or real
  emails in tracked files or commit messages.
- **Git author identity:** avoid the auto-generated `name@hostname.local` (it
  leaks your machine name). Use a GitHub `noreply` email; scrub history before the
  first public push if needed.
- Output directories that contain sensitive data (logs, exports, reports) must be
  gitignored.

### 4) Agent config & permissions — deny-by-default
- **`.gitignore` agent dirs deny-by-default:** ignore everything in `.claude/`,
  `.cursor/`, `.aider*`, etc., then allow only the explicitly shareable file
  (e.g. `.claude/settings.json`). This keeps local settings, transcripts, caches,
  and credentials out of git even on an accidental `git add -A`.
  ```text
  .claude/*
  !.claude/settings.json
  .claude/settings.local.json
  **/.credentials.json
  ```
- **Keep `settings.local.json` private** — it's personal/machine-local. Publishing
  permission grants is information disclosure; only share a curated `settings.json`
  if you intend to.
- **Review hooks** — hooks run shell commands automatically; a malicious or
  over-broad hook is code execution. Read every hook before trusting the repo.
- **Review MCP servers** — they can send data to third parties; confirm each is
  expected and scoped. Treat unknown MCP configs as untrusted.
- **Permission allowlist hygiene** — no over-broad `Bash(*)`/blanket wildcards;
  prefer specific prefixes. Narrow is safer and still functional.

### 5) Prompt-injection surface
The agent treats repo text as input. Untrusted content can carry instructions.
- Identify files an agent ingests that come from outside (vendored docs, sample
  data, issue/PR text, `AGENTS.md`/`CLAUDE.md` from forks).
- Scan for injection phrasing and hidden Unicode (zero-width / bidi) in those
  files — the same checks `vet-skill` runs. Don't let "instructions" ride in on data.

### 6) Execution & network boundary
- Know what the agent may auto-run and keep it minimal and specific.
- No `curl … | sh`, no auto-running untrusted `postinstall`/build scripts.
- Be deliberate about outbound network: which hosts, sending what.

### 7) Dependency / supply chain
- Lockfiles present and committed; dependencies from trusted sources.
- No lifecycle scripts (`postinstall`, etc.) that run on install without review.

### 8) Remediate, then verdict
Fix blocking items (any live secret = **NO-GO**), re-run the audit, and state a
clear **GO / NO-GO** with the residual risks listed.

## Tooling reference

| Tool | Use |
|------|-----|
| `gitleaks detect --no-banner` | Secret scan of tree + history |
| `trufflehog git file://.` | Secret scan with verification |
| `ggshield secret scan repo .` | GitGuardian scan (prompts/commits/outputs) |
| `git-secrets --scan` | AWS-focused pre-commit secret guard |
| `git filter-repo` | Purge secrets/PII from history |
| pre-commit + CI hook | Make leaks impossible to recommit |

## Go / No-Go checklist
- [ ] No secrets in tracked files or history (scanner clean)
- [ ] No real home paths / hostnames / emails leaked
- [ ] Git identity is a noreply (no `*.local` hostname)
- [ ] `.gitignore` is deny-by-default for agent dirs + secrets
- [ ] `settings.local.json` (and any credentials) untracked
- [ ] Hooks reviewed; no surprising auto-run commands
- [ ] MCP servers reviewed and scoped
- [ ] Permission allowlist is specific, not blanket wildcards
- [ ] Untrusted/ingested files checked for injection + hidden Unicode
- [ ] Output dirs with sensitive data are gitignored
