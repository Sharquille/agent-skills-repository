# PROJECT-PROTOCOL.md

This file lives at the root of each project created by `project-build-loop`. It
is the on-disk handoff so any agent opened inside this project can continue the
work. The conductor (the `project-build-loop` skill) owns all state changes.

## State files

- `project.json` — tracked project state (schema_version, id, phase,
  `classification`, `authorization`, tasks). Relative paths only. Tasks may carry
  `advisories[]` — in-scope observations (Why / When-Where / Steps / Status) routed to
  the task where they become actionable.
- `event-log.jsonl` — append-only audit of every transition, gate, and consult.
- `.project/` — local-only (gitignored): lock (host+pid), absolute paths,
  scratch. Never committed.

## Directories

- `build-log/tasks.md` — primary sequential task board: current status,
  blockers, next inputs, routed follow-up, and close conditions.
- `build-log/observations.md` — working observations, assumptions, candidate
  decisions, and rationale. Internal class.
- `build-log/task-N.N.steps.md` — per-task method/evidence ledger only when a
  task has hands-on setup, troubleshooting, persistence, validation, or evidence.
- `evidence/` — gitignored raw captures, each hashed at write time. The authoritative
  manifest is tracked at `build-log/artifact-manifest.json` (schema
  `references/schemas/artifact-manifest.json`, v1.1) with `source`, `relevance`,
  `retained_original`, `retained_format`, and `redaction_status`. The manifest is
  tracked; the artifacts are not.
- `.vault/` — gitignored secrets.
- `topology/` — `.unl` source → `topology.json` → generated SVG/Mermaid.
- `publish/` — sanitized PUBLIC artifacts only; feeds `project-publish` (Astro).
- `references/` — project-local reference material; `external-references.md` is
  the governed registry of authoritative external domain sources (advisory), and
  `tooling.md` is the tool bill of materials (software/packages, install, version,
  source, supply-chain note) that hands-on tasks depend on.

## Lifecycle (phases)

`intake → discovery → classify → roadmap → task-loop → consult → publish`.
See the `project-build-loop` SKILL for the full phase definitions and gates.

## Non-negotiables

- Local private git, no remote by default. Never `git add .`.
- Run secret scan before stage/commit/consult/publish (fail-closed).
- Authorization is a gate; default everything private; unknown = restrictive.
- Publication reads only sanitized `publish/` artifacts.
- `references/external-references.md` is advisory only — secret-scanned and
  allowlist-staged like any tracked artifact; never closure proof.
- All notes in portable GFM (five standard alerts, HTML `<!-- -->` markers).
- Markdown hygiene gate: before checkpoint, consult, or publish handoff, run the
  project-build-loop Markdown gate on touched `.md` files and fix errors.
- Avoid new per-task summary files by default. Use `build-log/tasks.md` for the
  readable task board and create steps ledgers only when evidence/method needs it.

## Resuming

Read `project.json` `phase` and the last `event-log.jsonl` entries, then continue
from there. Do not clear state on resume.
