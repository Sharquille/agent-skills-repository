---
name: task-steps-ledger
description: "Create and maintain per-task method ledgers for project-build-loop tasks. Use when a project task needs durable step-by-step setup notes, troubleshooting methods, logical-to-topology mappings, persistence files, commands run, issues and fixes, validation checks, evidence pointers, or closure criteria that should not be buried in a narrative build log. The ledger is private by default, portable Markdown, and never replaces the conductor-owned project state or append-only event log."
category: productivity
source: self-authored (this repository)
author: Sharquille Andrew
license: MIT
retrieved: 2026-06-28
---

# Task Steps Ledger

A task-scoped ledger for the practical work that makes a project reproducible:
the commands used, mappings discovered, files changed for persistence, issues
hit, fixes applied, validation checks, and evidence pointers. It is designed for
`project-build-loop`, but can be reused by any disk-backed project workflow that
needs real setup/troubleshooting steps preserved without turning the main build
log into a long transcript.

## Operating rules

1. **Conductor still owns state.** This skill writes task method artifacts only.
   It never changes `project.json`, `event-log.jsonl`, task status, git state, or
   lifecycle gates unless the calling conductor explicitly performs those steps.
2. **One ledger per task.** Use `build-log/task-<task-id>.steps.md`, for example
   `build-log/task-1.1.steps.md`. For a phase-wide rollup, use
   `build-log/task-1.steps.md` and link back to the exact subtask ledgers.
3. **Append-friendly, not append-only.** Correct mistakes plainly when needed,
   but preserve meaningful history as dated entries instead of rewriting away
   solved problems. Event-log history remains append-only and conductor-owned.
4. **Private by default.** Do not include secrets, credentials, keys, tokens,
   private config blobs, raw payload captures, personal profile links, or real
   public IPs. Use placeholders and evidence manifests for sensitive material.
5. **Evidence pointers, not evidence dumps.** The ledger may include short,
   sanitized command output when useful. Full screenshots, PCAPs, configs, and
   raw logs belong in private evidence paths with hashes.
6. **Completion requires proof.** A task is not done merely because defaults were
   accepted or commands were proposed. Closure needs explicit user confirmation
   plus validation/evidence rows that show what was actually observed.

## When to create or update a ledger

Create or update the ledger whenever any of these appear:

- Logical-to-topology mapping, such as Linux NIC names to EVE-NG node links.
- Diagnostic commands used to understand the environment.
- Persistence files edited, such as netplan, systemd, firewall, router config,
  compose files, or application config.
- Troubleshooting issue, root cause, fix, or workaround.
- Validation commands or screenshots that prove the state.
- A proposed default is accepted as guidance but not yet proven.

## Required file shape

Use portable GitHub-Flavored Markdown only. No Obsidian-only callouts or hidden
syntax. Keep sections in this order unless the task clearly does not need one.

```markdown
# Task <task-id>: Steps Ledger

<!-- task-steps-ledger:task-<task-id> -->

## Status

Status: in progress

## Purpose

One or two sentences explaining what this ledger preserves and why it matters.

## Logical To Topology Map

| Logical role | Observed OS or device name | Topology link | Evidence | Status |
|---|---|---|---|---|
| `<role>` | `<observed name>` | `<node/link>` | `<command or evidence pointer>` | `observed` |

## Method Ledger

| Step | Action | Command or file | Result | Follow-up |
|---:|---|---|---|---|
| 1 | `<what was done>` | `<command/path>` | `<sanitized result>` | `<next action>` |

## Persistence Ledger

| File or setting | Change | Why it persists | Validation | Status |
|---|---|---|---|---|
| `<path>` | `<summary>` | `<reason>` | `<check>` | `pending` |

## Issues And Fixes

| Issue | Diagnostic method | Root cause | Fix or decision | Status |
|---|---|---|---|---|
| `<issue>` | `<command/check>` | `<cause>` | `<fix>` | `open` |

## Validation And Evidence

| Check | Command or probe | Expected | Observed | Evidence pointer | Status |
|---|---|---|---|---|---|
| `<check>` | `<command>` | `<expected>` | `<observed>` | `<path/hash or screenshot note>` | `pending` |

## Closure Gate

- [ ] User explicitly says this task is ready to close.
- [ ] Validation rows show observed results, not only proposed defaults.
- [ ] Evidence pointers exist or limitations explain why evidence is absent.
- [ ] Secret scan passed for the ledger and referenced text artifacts.
- [ ] Remaining open issues were moved to the next task or documented as limits.
```

## Writing guidance

- Put exact commands in backticks or fenced `text` blocks when they are safe to
  store. Redact provider details and sensitive hostnames before writing.
- For screenshots, record what the screenshot proves and the capture path if it
  is safe. Do not transcribe hidden secrets from screenshots.
- For config files, record the path and sanitized setting summary. Do not paste
  full configs when they include certificates, serial numbers, keys, tokens, or
  account identifiers.
- For networking labs, always capture the mapping from topology labels to OS
  names. Example: `Ubuntu_eth1 -> ens3 -> LAB_LAN`.
- When user language is ambiguous, record the interpretation as an assumption and
  mark it `pending confirmation`.

## Closure checklist

Before a conductor marks a task done, confirm the ledger answers:

- What did we actually do?
- Which commands or files made the change persistent?
- What issue did we hit, how did we diagnose it, and what fixed it?
- What did we observe after the change?
- Where is the evidence, and is it safe to retain?
- Did the user explicitly approve task closure?
