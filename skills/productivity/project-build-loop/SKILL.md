---
name: project-build-loop
description: "Run or install a disk-backed project lifecycle workflow (the build-side counterpart to obsidian-study-loop) for cybersecurity/networking labs and coding projects. Use when the user wants to start, bootstrap, plan, track, or resume a project under ~/Documents/development/projects, run a gated discovery interview, generate a roadmap and numbered tasks, work a task with focused task briefs plus observations notes and per-task steps ledgers, classify a project's archetype and dual-use sensitivity tier, run multi-model consults on project artifacts, or hand a sanitized write-up to publication. The conductor owns all lifecycle state, git checkpoints, and gates; it routes execution to existing domain skills and treats every consult as advisory. User-facing task prompts must translate project terms into concrete inputs, examples, safe placeholders, and evidence-resolved default status. Do not trigger for study/tutoring sessions (use obsidian-study-loop) or for one-off coding edits with no project lifecycle."
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
- **Notes/format:** `task-steps-ledger` (per-task method, issue/fix,
  persistence, validation, and evidence ledger), `knowledge-capture-obsidian`,
  `portable-markdown` (formatting authority), `humanizer` (prose pass on
  publication only), `mind-map-obsidian`.
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
- **Topology:** `eve-ng-topology` both ways — `.unl` → diagram, and (forward)
  topology spec + node catalog → importable EVE-NG Pro `.unl`
  (`scripts/generate_unl.py`). For user-importable lab templates, keep reusable
  artifacts in `topology/`: `canvas-layout-spec.json` for exact node/network
  placement, `decoration-spec.json` for EVE canvas zones/labels via
  `scripts/decorate_unl.py`, optional `design-spec.json` for Excalidraw, the
  generated `.unl`, and a root-level `.unl` import zip from
  `scripts/package_unl_zip.py`. Keep `build-log/task-*` files as lifecycle/audit
  notes, not competing topology sources. **Scaffold, don't configure:** the
  conductor may scaffold lab structure (nodes, images, wiring, layout) to save
  manual node-dragging, but device config is embedded verbatim and left faithful
  to observed state — technical config changes are the user's hands-on lab work,
  surfaced as `! TODO`/advisories, never auto-applied. A generated `.unl` is
  unverified until import-validated on the EVE-NG server.

Helper skills never override the safety rules here.

## Conventions

- **Default root:** `~/Documents/development/projects/<category>/<project-slug>/`.
- **Categories:** `networking-and-cybersecurity`, `software-development`
  (extensible). Use **neutral slugs** — never encode sensitivity in a path.
- **Root resolution:** if `cwd` already has `.git` or a `project.json`, offer to
  use it; otherwise create under `projects/<category>/<slug>`.
- **Git:** local private init, **no remote** by default.
- **External references registry:** Authoritative external domain sources
  (vendor docs, RFCs, CIS benchmarks, official guides, tool docs) go in one
  project-level file, `references/external-references.md` — one row per source:
  **Topic**, **Source** (canonical name), **URL**, **Type**, **Retrieved** (ISO
  date), **Used-by-task**, **Validation note**. The registry is advisory and is
  never closure proof. Additions are secret-scanned, allowlist-staged, and
  logged as `reference_added`. At publication it becomes a sanitized citations
  list, never raw build context.



### Task surface consolidation

Avoid one summary file per task. The default project surface is
`build-log/tasks.md`: a sequential board with all roadmap tasks, current status,
blockers, next inputs, and close conditions. Keep observations in
`build-log/observations.md` and create per-task `task-N.N.steps.md` ledgers only
when there is real method, troubleshooting, persistence, validation, or evidence
to preserve. Existing `task-N.N.md` files may remain as historical summaries, but
do not create new per-task summary files unless the user explicitly asks or a
single task is large enough to justify an exception.

### Markdown hygiene gate

`portable-markdown` is the formatting authority for project notes. The conductor
must run `scripts/markdown_gate.sh` on Markdown files touched in the current
lifecycle phase before checkpointing, consulting, or publishing. The gate wraps
`portable-markdown/scripts/lifecycle-lint.sh` and checks both portability and
lifecycle house style: unambiguous task status, routed-work clarity, table row
shape, heading levels, and oversized action surfaces.

Scope the gate to touched files unless the user explicitly requests a cleanup
pass. Observations notes may remain rough while exploring; gate them when they
are promoted into a task note, sent to consult, or prepared for publish. A gate
error blocks the lifecycle transition; warnings should be logged and cleaned up
when they affect the user-facing action surface.

### Evidence retention

`evidence/` is gitignored; the authoritative manifest is tracked at
`build-log/artifact-manifest.json` (schema `references/schemas/artifact-manifest.json`,
v1.1). The conductor retains evidence **automatically but relevance-gated**: keep an
artifact only when it answers the active task's checklist, resolves a `pending` default,
or bears on a success criterion — never hoard noise.

Source modes, recorded per artifact: `command` (conductor-produced output), `file`
(user gives a path on disk → copy the bytes and hash; `retained_original: true`), and
`chat-paste`. **Image-bytes boundary:** the conductor cannot recover the raw bytes of a
chat-pasted screenshot. It transcribes the visible command/output into a sanitized text
artifact under `evidence/task-N.N/`, hashes that, and records `retained_original: false`,
`retained_format: transcribed-text`. For byte fidelity the user pastes a file path and
the conductor copies the original.

Sanitize before any tracked write, not blanket: raw RFC1918/RFC4193 lab values may stay
in the gitignored evidence file, but real public IPs/IPv6, identity-bearing hostnames,
and anything that travels into a tracked artifact (manifest, task note, steps ledger,
publish) must be replaced with RFC 5737 / RFC 3849 placeholders. Each manifest entry
carries `redaction_status`. Run `scripts/secret_scan.sh` on the manifest before staging;
it is tracked and must be clean even though its artifacts are not. After each capture,
report one line per artifact — `path | sha256[:12] | relevance` — and let the user keep,
expand, or discard it. Log `evidence_captured` (and `evidence_dropped` on removal).

### Advisory capture and routing

When the conductor raises an observation within project scope, capture it as a
**structured advisory in the task's "What You Need To Do" surface**, not as throwaway
chat prose. Required fields: **Why** (reasoning), **When/Where** (trigger + evidence
pointer), **Steps**, and **Status** (`blocking` | `deferred` | `noted`). Mirror it in
`task.json` `advisories[]`.

- `blocking` — must be resolved before close; promote it to a real checklist item (it is
  then no longer just an advisory).
- `deferred` — routed to the future task where it becomes actionable via `route_to_task`;
  it surfaces in that task's "What You Need To Do" when the task opens, carrying the same
  evidence pointer. Do not duplicate it into the future task before that task exists.
- `noted` — kept for the audit trail; no required action.

An advisory never closes or gates a task by itself. If an advisory reveals the task is
adopting a new capability flag (`mitm_proxy`, `traffic_decryption`, `exploit_poc`,
`malware_sample`, live targets), set `promotes_capability_flag` and take the Phase 5
reclassify path before continuing — the advisory is the trigger that makes the policy
change visible, not the policy change itself. Log `advisory_recorded`.

### Tooling & software setup

A network/config design is incomplete until the **tools it depends on** are
named. Maintain a per-project **tool bill of materials** in `references/tooling.md`
— one row per tool: name, purpose, install method, pinned version, source, and a
supply-chain note. Discovery's tooling-supply-chain answers (intake §H) seed it;
the roadmap derives each hands-on task's subset into `task.json` `tools[]`; the
task brief surfaces a **Tools & setup** block before the configuration steps.

- **Scaffold, not configure.** The conductor *proposes* install/setup steps
  (`apt install …`, key generation, where to download a provider config) as TODO;
  it never installs or configures for the user.
- **Pin versions** for the Phase 7 reproducibility bundle; **vet the supply
  chain** (trusted repo, checksum/signature) per the safety rule before use.
- **Secrets stay out:** provider configs, keys, and tokens are obtained by the
  user and kept in `.vault/` — list the *tool* and *where to get it*, never the
  secret material.

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
- **How to answer:** state whether the user should answer all items in one
  combined response or whether you are asking one blocking question. If there are
  multiple numbered items, explicitly say each numbered item is a separate input
  inside one response.
- **Actual values vs placeholders:** tell the user which values are safe and
  useful to provide as actual lab values, which values must stay as placeholders,
  and when `unsure` is acceptable. Actual private lab values are useful for
  RFC1918/RFC4193 subnets, EVE-NG network names, VM/node labels, interface names,
  and non-secret version numbers. Placeholders are required for real public IPs,
  personal URLs/profiles, hostnames tied to identity, VPN account/provider
  details, credentials, keys, tokens, private config blobs, or anything the user
  does not want stored in the project log.
- **What I need from you:** a short, numbered list or table of specific inputs.
  For each input, include the expected form (`actual lab value`, `placeholder`,
  or `unsure`) and an example such as `KALI_eth0 -> LAB_LAN`,
  `LAB_LAN_SUBNET=10.10.10.0/24`, `UBUNTU_WAN_PUBLIC_IP=<REAL_PUBLIC_IP>`, or
  `SELF_PROFILE_URL=<SELF_PROFILE_URL>`. Say "answer `unsure` and I will propose
  a conservative default" when appropriate.
- **Tools & setup:** for any hands-on task, list the **software/tools the task
  needs before configuration can start** — package/binary name, what it is for,
  how to install it (e.g. `apt install wireguard wireguard-tools`), where to
  obtain non-repo artifacts (e.g. the VPN provider's WireGuard config from their
  portal), the version to pin for reproducibility, and a one-line supply-chain
  note (trusted repo / verify checksum). This is **proposed setup, not done for
  the user** (scaffold, not configure) — present it as TODO steps the user runs
  and confirms. Do not enumerate a network design without first naming the tools
  it depends on.
- **Do-not-send guardrail:** when relevant, state what not to paste, such as
  secrets, tokens, private keys, real public IPs, credentials, or personal links.
- **Steps ledger reminder:** when a task involves hands-on setup,
  troubleshooting, persistence files, mappings, screenshots, or validation
  commands, tell the user those methods will be captured in
  `build-log/task-<id>.steps.md` and that proposed defaults are guidance until
  evidence exists.
- **Default resolution by evidence:** do not force the user to explicitly say
  accept or reject every proposed default. If later observed evidence in the
  steps ledger matches a proposed default and no newer input contradicts it,
  mark that default `accepted`. If observed evidence contradicts it, mark it
  `rejected`. If evidence is absent or ambiguous, keep it `pending`. Default
  resolution may update the task checklist and observations note, but it never
  closes the task by itself.

Avoid presenting bare project-management labels such as "document topology",
"define scope", "capture evidence", or "validate egress" without unpacking what
those labels mean for the current project. Do not ask for mixed networking
inputs as an ambiguous paragraph; group them into named sections such as
interfaces, addressing, allowed paths, blocked paths, bootstrap choices, and
evidence.

Example topology prompt shape:

```text
How to answer: Reply once with the six sections below. Each numbered section is
a separate input. Use actual lab-only values for private RFC1918/RFC4193 subnets
and VM interface names. Use placeholders for real public IPs, VPN details,
personal links, secrets, or anything unknown. Write `unsure` where you want me to
propose a default.

1. Interface map (actual lab labels preferred):
   - Example: KALI_eth0 -> LAB_LAN; UBUNTU_eth0 -> LAB_LAN; UBUNTU_eth1 -> pnet0
2. Lab addressing (actual private lab subnets preferred, placeholders allowed):
   - Example: LAB_LAN_SUBNET=10.10.10.0/24; UBUNTU_LAN_GW=10.10.10.1; KALI_LAN_IP=10.10.10.10
3. External/VPN details (placeholders only):
   - Example: VPN_ENDPOINT_IP=<VPN_ENDPOINT_IP>; UBUNTU_WAN_PUBLIC_IP=<REAL_PUBLIC_IP>
4. Allowed paths:
   - Example: Kali -> Ubuntu LAN -> wg0 -> VPN -> internet
5. Blocked paths:
   - Example: Kali -> pnet0 direct; Kali -> ISP DNS; Ubuntu WAN non-WireGuard when wg0 is down
6. Evidence to capture:
   - Example: ip route output, firewall rules, DNS leak check, public IP check, lab-only PCAP names
```

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
- Use atomic writes. Validate `project.json` against the documented shape in
  `references/schemas/` before every state transition — those files are
  annotated **examples** (they show field shapes and enum options as literal
  strings), not machine JSON Schema; validate structurally, do not feed them to
  a JSON Schema validator. Tracked state uses **relative** paths; absolute paths
  live only in gitignored local state (cross-machine safety).

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
evidence that will prove those controls work." For each hands-on task also
**derive its tool bill of materials** (`task.json` `tools[]`, sourced from
`references/tooling.md`): the software/packages it needs, install method, and
where to obtain non-repo artifacts — so a build task never starts without naming
the tools it depends on. See the Tooling & software setup convention.

### Phase 5 — Task loop

For "work on task N.N":

1. **Per-action gate** (`scripts/policy_check.sh`): re-validate the tier against
   the task's declared capability flags; pass the gate's proof inputs
   (`--authorized`, `--scoped`, `--isolated` for T2+ tooling; `--approval yes`
   for git-remote/publish; `--consult-kind planning|artifact` for consults).
   The gate reads tier and `publish_policy` from `project.json` and treats any
   unconfirmed `classification.status` as at least T3. If a task introduces
   `packet_capture` / `active_scan` / `mitm_proxy` / `traffic_decryption` /
   `exploit_poc` / `malware_sample` / `credential_material` / live targets,
   **reclassify** before routing (a rerun may keep the tier — see
   `dual-use-rating.md`). Adding an external reference never changes
   `dual_use_tier` or gates; if a referenced technique leads the task to adopt a
   new capability, reclassify the task, not the reference.
2. **Baseline/snapshot** the relevant state (git status, env snapshot).
3. **Execute** by routing to the archetype's domain skills. Each returns a
   structured report: changed files, commands run, risks, tests, blockers.
4. **Capture + hash** evidence per the Evidence-retention convention:
   relevance-gated, into gitignored `evidence/task-N.N/`, with a sanitized entry in
   the tracked manifest at `build-log/artifact-manifest.json`. Chat-pasted screenshots
   are retained as transcribed text only — the original image bytes are not recoverable
   from a paste.
5. **Task artifacts**:
   - Keep the primary user-facing task surface in one sequential board:
     `build-log/tasks.md`. This is the low-noise view of current status,
     blocked/next/done items, accepted/pending defaults, routed advisories, and
     close conditions. Do not create a new `task-N.N.md` summary by default.
   - Keep working observations in one general note: `build-log/observations.md`.
     Use it for assumptions, defaults before resolution, current-state review
     notes, issue context, candidate decisions, non-final analysis, and
     rationale. Create a task-specific observations file only when the general
     file would become unreadable.
   - Create or update the required method ledger at
     `build-log/task-N.N.steps.md` using `task-steps-ledger` only when hands-on
     setup, troubleshooting, logical-to-topology mapping, persistence files,
     validation commands, screenshots, PCAPs, issue reports, or fixes appear.
   - Do not bury reproducibility details in `tasks.md` or observations. The
     steps ledger must capture method, diagnostics, issue/fix rows, persistence
     files, validation checks, evidence pointers, and closure checklist state.
   - Cross-reference defaults to observed step evidence. Mark each proposed
     default `accepted`, `rejected`, or `pending` based on the latest evidence:
     accepted when evidence matches, rejected when evidence contradicts, pending
     when evidence is missing or ambiguous. The user may still override a
     default explicitly, but no separate accept/reject reply is required when
     evidence resolves it.
   - When a task relies on an authoritative external source, record it once in
     the project's `references/external-references.md` registry; the task note
     or `task-N.N.steps.md` carries only a pointer plus the advisory caveat. Do
     not duplicate the registry table into a task file.
   - Capture in-scope advisories as structured items in the task note's "What You
     Need To Do" surface (Why / When-Where / Steps / Status) and mirror them in
     `task.json` `advisories[]`; route deferred advisories to the target task. See
     the Advisory capture and routing convention.
6. **Closure gate:** Do not mark a task `done` merely because proposed defaults
   were accepted or candidate commands were written. A task closes only after
   the user explicitly confirms completion and the steps ledger contains
   observed validation/evidence rows or documented limitations. An auto-retained
   chat-paste satisfies the evidence requirement only when the steps ledger and
   `checkpoint.limitations[]` record that the original image bytes were not
   retained. Open advisories do not block closure unless promoted to a checklist item.
7. **Markdown hygiene gate**: run `scripts/markdown_gate.sh` on touched
   `build-log/tasks.md`, `build-log/observations.md`, any touched
   `build-log/task-*.steps.md`, `references/*.md`, and publish-candidate
   Markdown. Fix errors before checkpoint; warnings may remain only when they
   are historical observations, not the current user-facing action surface.
8. **Checkpoint**: before/after git status, exit codes, limitations, rollback
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
- External references are supply-chain context: prefer canonical/official
  sources, record the retrieval date, and never run commands copied from a
  reference without lab validation. A reference is context, not evidence.
- All notes/publication in portable GFM per `portable-markdown` (five standard
  alerts, HTML `<!-- -->` markers). No Obsidian-only syntax. Run the Markdown
  hygiene gate on touched lifecycle Markdown before checkpoint, consult, and
  publish handoff.

## Bundled resources

- `scripts/bootstrap_project.sh` — safe, idempotent, dry-run-first root/project
  creation.
- `scripts/secret_scan.sh` — fail-closed secret + IPv4 scan gate (secrets always;
  real IPv4 in `--publish` mode). IPv6, hostnames, EXIF, and timestamps remain
  manual-review items per `dual-use-rating.md`.
- `scripts/policy_check.sh` — fail-closed pre-action tier/gate validator.
- `scripts/policy_selftest.sh` — regression matrix asserting `policy_check.sh`
  matches the `dual-use-rating.md` fixtures; run after editing either.
- `scripts/markdown_gate.sh` — wraps portable-markdown lifecycle lint for touched project Markdown.
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
