---
name: project-build-loop
description: "Run or install a disk-backed project lifecycle workflow (the build-side counterpart to obsidian-study-loop) for cybersecurity/networking labs and coding projects. Use when the user wants to start, bootstrap, plan, track, or resume a project under ~/Documents/development/projects, run a gated discovery interview, generate a roadmap and numbered tasks, work a task with inline build-log notes and issue reports, classify a project's archetype and dual-use sensitivity tier, run multi-model consults on project artifacts, or hand a sanitized write-up to publication. The conductor owns all lifecycle state, git checkpoints, and gates; it routes execution to existing domain skills and treats every consult as advisory. User-facing task prompts must translate project terms into concrete inputs, examples, and safe placeholders. Do not trigger for study/tutoring sessions (use obsidian-study-loop) or for one-off coding edits with no project lifecycle."
# --- provenance ---
category: productivity
source: self-authored; design in docs/plans/project-orchestra-plan.md, pressure-tested via consult-orchestrator (Codex + Kimi)
author: Sharquille Andrew
license: MIT
retrieved: 2026-06-27
---

# Project Build Loop

The conductor for a disk-backed **project lifecycle**: bootstrap → discovery →
classify → roadmap → task loop → consult → publish → undo. It is the build-side
sibling of `obsidian-study-loop`. The conductor is the **sole owner** of lifecycle
state, git checkpoints, logs, gates, and classification. Domain skills only
execute within the resolved project root and **return structured reports**;
consults are **advisory only**. The conductor performs every write, git action,
and gate decision.

> Full design rationale: `docs/plans/project-orchestra-plan.md` in this repo.

## Prime directives

1. **Conductor owns state.** Only this skill writes `project.json`,
   `event-log.jsonl`, checkpoints, and git history. Reused skills operate inside
   the project root and report back; they never own lifecycle state.
2. **Fail closed.** If classification is missing, stale, downgraded without
   rationale, or inconsistent with the requested action, block the action.
3. **Authorization is a gate, not a score.** No live-target or offensive tooling
   runs without `authorized + scoped + isolated`. Strong authorization permits
   work; it never lowers a dual-use tier.
4. **Default private.** Local git, no remote. Everything is `private` until a
   pre-publish gate promotes a sanitized artifact to `public`.
5. **Unknown = restrictive.** Unknown ownership, egress, data class, or publish
   intent applies the higher tier and blocks risky actions until resolved.
6. **Consults are advisory and sealed.** Route only redacted/allowlisted
   artifacts; verify every claim before acting.

## Helper skill routing

The conductor orchestrates; it does not re-implement domain work. Route to:

- **Research:** `literature-review`, `study-research-queries`.
- **Notes/format:** `knowledge-capture-obsidian`, `portable-markdown` (formatting
  authority), `humanizer` (prose pass on publication only), `mind-map-obsidian`.
- **Security governance:** `security-threat-model`, `build-security-policy`,
  `security-and-hardening` (secret-scan / `.gitignore` baseline), `security-scan`,
  `agent-repo-security`, `security-ownership-map`.
- **Cyber domain:** the `analyzing-*`, `performing-*`, `building-*`,
  `configuring-*`, `scanning-*` skills as the archetype profile dictates.
- **Networking:** `configuring-network-segmentation-with-vlans`,
  `configuring-pfsense-firewall-rules`, `homelab-*`, `cisco-ios-patterns`,
  `network-config-validation`, `network-bgp-diagnostics`.
- **Naming:** `project-name-consult` (Kimi for domain accuracy, MiMo for
  portfolio readability) — called during Phase 1 intake before bootstrap.
- **Consult:** `consult-orchestrator`, `codex-consult`, `opencode-consult` (via
  `project-consult-panel` once built).
- **Publish:** `project-publish` (Astro), reusing `site-architecture`,
  `modern-web-ui`, `design-tokens`, `ui-styling`.
- **Topology:** `eve-ng-topology` for `.unl` → diagram.

Helper skills never override the safety rules here.

## Conventions

- **Default root:** `~/Documents/development/projects/<category>/<project-slug>/`.
- **Categories:** `networking-and-cybersecurity`, `software-development`
  (extensible). Use **neutral slugs** — never encode sensitivity in a path.
- **Root resolution:** if `cwd` already has `.git` or a `project.json`, offer to
  use it; otherwise create under `projects/<category>/<slug>`.
- **Git:** local private init, **no remote** by default.

## User-facing clarity

Lifecycle terms are internal shorthand. When presenting a task, asking discovery
questions, or requesting missing inputs, translate the shorthand into the
concrete pieces the user needs to provide.

For every task prompt, include:

- **Task label:** `N.N: <title>`.
- **Plain meaning:** one sentence beginning with "This means..." that names the
  actual objects involved, such as devices, interfaces, subnets, files, commands,
  screenshots, logs, policies, or validation evidence.
- **Why it matters:** one sentence tying the task to the project's safety,
  function, or evidence gate.
- **What I need from you:** a short, numbered list of specific inputs. Use
  examples and placeholders (`KALI_LAN`, `DEBIAN_WAN`, `SELF_PROFILE_URL`) and
  say "answer `unsure` and I will propose a default" when appropriate.
- **Do-not-send guardrail:** when relevant, state what not to paste, such as
  secrets, tokens, private keys, real public IPs, credentials, or personal links.

Avoid presenting bare project-management labels such as "document topology",
"define scope", "capture evidence", or "validate egress" without unpacking what
those labels mean for the current project.

## Global invocation

This skill is globally available and may be called from any directory. Resolve
the target project before writing:

1. If `cwd` contains `project.json`, treat it as the active project.
2. Else read `~/Documents/development/projects/_index/last-active.json`.
3. Else this is a new project — go to Phase 1.

Never assume an arbitrary `cwd` is the project root just because the skill was
invoked there.

## State model

- **Global:** `projects/_index/last-active.json` holds **only** the last-active
  pointer and a private portfolio index (archetype/tier/status). It never names
  unpublished T3/T4 projects in any public artifact.
- **Per-project (tracked, relative paths):** `project.json` (schema in
  `references/schemas/project.json`) + append-only `event-log.jsonl`.
- **Per-project (local only, gitignored):** `.project/lock` (host+pid, stale-lock
  recovery), absolute paths, secrets.
- Use atomic writes. Validate `project.json` against the schema before every
  state transition. Tracked state uses **relative** paths; absolute paths live
  only in gitignored local state (cross-machine safety).

## Lifecycle

### Phase 0 — Install the orchestra (one-time)

Create `~/Documents/development/projects/` with category subfolders and
`_index/last-active.json` (`{ "last_active": null }`). Idempotent; never
overwrite. Use `scripts/bootstrap_project.sh --install-root` for the safe,
dry-run-first creation.

### Phase 1 — Intake & safe bootstrap

1. Collect a short project description. Route to `project-name-consult` (Kimi +
   MiMo) for a domain-accurate, portfolio-ready title and category; present a
   ranked shortlist; confirm the user's choice before any write. Fall back to the
   conductor's own inference if the models are unavailable.
2. Run `scripts/bootstrap_project.sh` (see its header). It slugifies the title,
   rejects `..`/absolute/symlink targets, `realpath`-guards the path under the
   approved base, refuses a non-empty dir lacking a project marker, prints a
   **dry-run write plan**, and on approval creates the tree, `git init` (local,
   no remote), the `.gitignore` baseline (`assets/gitignore-baseline`), and seed
   `project.json` / `event-log.jsonl`.
3. Log creation to `event-log.jsonl`; set the global last-active pointer.

### Phase 2 — Discovery interview

Walk `references/intake-questions.md` (governance-complete). Capture objectives,
**authorization** (owner, scope, target list, allowed/excluded actions, evidence
path, egress rules, kill-switch), **isolation/egress**, environment (EVE-NG
Community/Pro, images, snapshots / production rollback), tooling, **evidence
capture + hashing + retention**, **redaction policy**, success criteria,
**decommission plan**, audience, and publish intent. Treat unknowns as
restrictive. Ask in plain language: define each term before asking for it, show
safe examples, and let the user answer "unsure" when the conductor can propose a
reasonable default.

### Phase 3 — Classify

Apply `references/dual-use-rating.md` and `references/project-archetypes.md`:

- Propose `archetype` (primary/secondary) → selects the default skill bundle and
  placement defaults (routing only, never policy).
- Derive `capability_flags` and the **decision-tree** `dual_use_tier` (T0–T4).
- Record `data_classes`, `artifact_class_floor`, `publish_policy`, `git_policy`.
- The LLM **proposes**; `scripts/policy_check.sh` **validates** before any risky
  action. Write the `classification` block to `project.json` (status
  `provisional`/`confirmed`/`review_required`). While unresolved, enforce the
  higher tier.

### Phase 4 — Roadmap & gated tasks

Generate a roadmap and numbered tasks (1.1, 1.2…) with **mandatory gates**:
authorize+classify → baseline+snapshot+hashes → build/harden → deploy with
version locks → execute → analyze/validate → redact+repro-bundle →
publish-approval → decommission. Offer suggested paths; the user selects; finalize
tasks into `references/schemas/task.json` shape. Each task title must be paired
with a plain-language expansion, a reason the task exists, and the exact user
inputs needed to start it. Example: `1.1: Document topology, trust boundaries,
and traffic policy` should be presented as "map devices, interfaces, EVE-NG
networks, IP subnets, allowed traffic paths, blocked traffic paths, and the
evidence that will prove those controls work."

### Phase 5 — Task loop

For "work on task N.N":

1. **Per-action gate** (`scripts/policy_check.sh`): re-validate the tier against
   the task's declared capability flags; confirm authorization + isolation for
   T2+. If a task introduces `mitm_proxy` / `traffic_decryption` / `exploit_poc`
   / `malware_sample` / live targets, **reclassify** before routing.
2. **Baseline/snapshot** the relevant state (git status, env snapshot).
3. **Execute** by routing to the archetype's domain skills. Each returns a
   structured report: changed files, commands run, risks, tests, blockers.
4. **Capture + hash** evidence into `evidence/` (gitignored) with a manifest.
5. **Inline note** the practical steps, decisions, issues + fixes, and limitations
   under that task in `build-log/task-N.N.md`. In-task issue reports are inlined
   here, not scattered.
6. **Checkpoint**: before/after git status, exit codes, limitations, rollback
   point; append to `event-log.jsonl`. **Kill-switch** on unexpected egress or
   live-malware beaconing.

The conductor records every checkpoint; domain skills never checkpoint.

### Phase 6 — Consult gates

Use `project-consult-panel` (capability-based roles → your Kimi/MiMo/Codex/Claude
models). Send **only** redacted/allowlisted artifacts. Sequential + locked
(opencode shares one SQLite DB → concurrent runs hit "database is locked").
Record provenance: model, prompt hash, artifact hash, timeout status, result
path. **T2+** requires a redaction manifest; **T3+** requires a security-review
consult. Advisory only — verify before acting.

### Phase 7 — Completion & publish handoff

Compile `build-log/` → automated redaction pass → **manual review gate** →
reproducibility bundle (tool/version locks, bootstrap + destroy scripts) →
publish manifest → hand to `project-publish` (Astro). Publication reads **only**
sanitized `publish/` artifacts, never raw build logs. Follow the publication-gate
rules in `references/dual-use-rating.md` §publication. A disclaimer is boilerplate
*after* controls pass, not a control.

### Undo / rollback

`undo-project-build-loop` shares this skill's manifest/checkpoint machinery. It
never invents deletion steps; it reverses recorded checkpoints.

## Safety rules

- Treat the project tree as precious. Never delete or overwrite without asking.
- Never `git add .`; stage an allowlist. Run `scripts/secret_scan.sh` before
  staging, committing, consulting, and publishing.
- Keep `project.json` schema-valid; one confirmed tier or `review_required`.
- Reclassify upward automatically; downward only with human rationale + an
  `event-log.jsonl` entry.
- Never encode sensitivity in a path or public index. Default everything private.
- Never paste secrets, credentials, real IPs/hosts, keys, or payload PCAPs into a
  consult or a publication. Use RFC 5737 / RFC 3849 documentation ranges in
  write-ups.
- Vet tool supply chain (EVE-NG images, GitHub tools, containers) before use.
- All notes/publication in portable GFM per `portable-markdown` (five standard
  alerts, HTML `<!-- -->` markers). No Obsidian-only syntax.

## Bundled resources

- `scripts/bootstrap_project.sh` — safe, idempotent, dry-run-first root/project
  creation.
- `scripts/secret_scan.sh` — secret/PII scan gate.
- `scripts/policy_check.sh` — fail-closed pre-action tier/gate validator.
- `assets/gitignore-baseline` — strong `.gitignore`.
- `references/intake-questions.md` — governance-complete discovery bank.
- `references/project-archetypes.md` — archetype taxonomy + default profiles.
- `references/dual-use-rating.md` — capability flags, tier decision tree, gate
  table, publication rules, golden-example fixtures.
- `references/safety-policy.md` — authorized scope, destructive-command gates,
  artifact rules.
- `references/project-protocol-template.md` — the `PROJECT-PROTOCOL.md` written
  into a project on bootstrap.
- `references/schemas/` — `project.json`, `task.json`, `artifact-manifest.json`,
  `event-log.jsonl` schemas.
