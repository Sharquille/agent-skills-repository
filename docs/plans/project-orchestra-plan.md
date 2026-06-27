# Project Orchestra — Design Plan (v1)

> Status: **plan only** — no skills built, no `projects/` tree created.
> Date: 2026-06-27 · Author: Sharquille Andrew (with Claude)
> Method: drafted by Claude, pressure-tested via `consult-orchestrator`
> (Codex/gpt-5.5 engineering angle + Kimi K2.7 domain angle), then verified
> against the real repo and synthesized.

## 1. Purpose

A disk-backed **project lifecycle companion** — the build-side counterpart to
`obsidian-study-loop`. It bootstraps a project, runs a governance-complete
discovery interview, generates a gated roadmap and numbered tasks, drives a
task-by-task execution loop with in-task issue reporting and inlined build-log
notes, routes work to existing domain skills, runs multi-model consults at
checkpoints, and publishes an elegant write-up to a Cloudflare static site.

Primary domains: cybersecurity/networking labs (heavy EVE-NG, then production)
and coding projects.

**Design stance (from the consult):** this is a *security-and-evidence pipeline
first, automation second*. The two risks both consultants flagged hardest were
**secret/evidence leakage** and **skill sprawl** — the architecture below is
shaped around avoiding both.

## 2. Conventions

- **Default root:** `~/Documents/development/projects/<category>/<project-slug>/`
  (this tree does **not** exist yet; install phase creates it).
- **Categories:** `networking-and-cybersecurity`, `software-development`
  (extensible).
- **Root resolution:** if `cwd` is already a project (has `.git` or a project
  marker), offer to use it; otherwise create under `projects/<category>/<slug>`.
- **Git:** local **private** init by default, **no remote**. Publication crosses
  a separate public boundary.

## 3. Skills to CREATE (5 — deliberately lean)

| Skill | Role | Notes |
|---|---|---|
| **`project-build-loop`** | The conductor. Sole owner of lifecycle state, git checkpoints, task loop, and gates. | Absorbs the originally-proposed `project-scaffold` and `project-discovery` as bundled scripts/references — they are safety-critical and low-freedom, so they belong inside the conductor, not as standalone skills. |
| **`project-consult-panel`** | Thin preset over `consult-orchestrator` + the tuned consult wrappers. | Justified as its own skill only because it **adds an artifact redaction/scrubber + manifest**. Roles are **capability-based, not hard-coded model names** (maps to Kimi K2.7 = code, MiMo v2.5 = prose, Codex = impl/diff review, Claude = conductor). |
| **`eve-ng-topology`** | Parse EVE-NG **`.unl` (XML) as source of truth** → `topology.json` → emit Mermaid + Graphviz DOT→SVG. | The genuinely novel capability; no existing skill covers it. PNG is a thumbnail only. Excalidraw/LaTeX deferred to a later version. |
| **`project-publish`** | Consume the **sanitized publish manifest** → **Astro + Tailwind + MDX** page bundle for Cloudflare Pages. | Separate skill because it crosses the public-site boundary. Reuses `site-architecture`, `modern-web-ui`, `design-tokens`, `ui-styling`, `portable-markdown`, `humanizer`. |
| **`undo-project-build-loop`** | Rollback companion. | Shares the conductor's manifest/checkpoint machinery — **no separate state model**. |

### Bundled inside `project-build-loop` (not separate skills)

- `scripts/bootstrap_project.sh` — deterministic, **safe** root creation:
  slugify the inferred title; reject `..`, absolute paths, and symlinks;
  `realpath` the target and require it stay under the approved base; fail unless
  the directory is empty or already carries a project marker; print a **dry-run
  write plan** before the first write; idempotent with a created-files manifest.
- `scripts/secret_scan.sh` — secret/PII scan run before staging, committing,
  consulting, and publishing.
- `assets/gitignore-baseline` — strong `.gitignore` (`.env*`, keys, PCAPs, raw
  configs, captures, `evidence/`, `.vault/`, EVE-NG exports).
- `references/intake-questions.md` — the governance-complete question bank.
- `references/safety-policy.md` — authorized scope, destructive-command gates,
  secret handling, public/private artifact rules.
- `references/schemas/` — `project.json`, `task.json`, `artifact-manifest.json`,
  `event-log.jsonl` schemas, validated before every state transition.

## 4. Skills to REUSE (orchestra members)

- **Research:** `literature-review`, `study-research-queries`
- **Notes/format:** `knowledge-capture-obsidian`, `portable-markdown`,
  `humanizer`, `mind-map-obsidian`
- **Security governance:** `security-threat-model`, `build-security-policy`,
  `security-and-hardening` (already ships a secret-scan/`.gitignore` baseline),
  `agent-repo-security`, `security-scan`, `security-ownership-map`
- **Cyber domain:** `analyzing-{indicators-of-compromise,cyber-kill-chain,
  threat-actor-ttps-with-mitre-attack,linux-system-artifacts,email-headers-*}`,
  `building-detection-rules-with-sigma`, `configuring-suricata-for-network-monitoring`,
  `performing-{network-packet-capture-analysis,network-traffic-analysis-with-tshark,
  network-traffic-analysis-with-zeek,dns-enumeration-and-zone-transfer}`,
  `scanning-network-with-nmap-advanced`, `building-incident-response-playbook`
- **Networking:** `configuring-network-segmentation-with-vlans`,
  `configuring-pfsense-firewall-rules`, `homelab-{vlan-segmentation,network-readiness}`,
  `cisco-ios-patterns`, `network-config-validation`, `network-bgp-diagnostics`,
  `network-interface-health`
- **Web/presentation:** `site-architecture`, `modern-web-ui`, `design-tokens`,
  `ui-styling`
- **Consult + authoring:** `consult-orchestrator`, `codex-consult`,
  `opencode-consult`; `skill-creator`, `name-skill`, `vet-skill`, `enhance-skill`

## 5. Directory & safety model

```
~/Documents/development/projects/
  _index/last-active.json                 # global: ONLY the "last active" pointer
  <category>/                             # networking-and-cybersecurity, software-development, …
    <project-slug>/
      .git/  .gitignore                   # local private, NO remote by default
      project.json  event-log.jsonl       # tracked state (RELATIVE paths) + append-only audit
      build-log/task-1.1.md …             # internal: raw per-task working notes
      topology/  (.unl → topology.json → *.svg)
      evidence/                           # gitignored; hashed artifact manifest
      .vault/                             # gitignored; secrets class
      publish/                            # PUBLIC sanitized artifacts only → feeds the site
      .project/lock                       # local-only: host+pid lock, ABSOLUTE paths
```

- **Artifact classes:** `secret · private · internal · public`. Everything
  defaults to private; only `publish/` is public.
- **State model:** per-project `project.json` (tracked, relative paths) +
  `.project/` local lock/abs-paths + append-only `event-log.jsonl`. The global
  index holds only "last active." Atomic writes, lockfile with host+pid, stale-
  lock recovery. This replaces the study-loop's single-pointer model, which is
  too weak for long-lived, possibly-parallel projects.
- **Secrets:** never `git add .`; stage an allowlist. Secret-scan before stage/
  commit/consult/publish. Publication reads only sanitized artifacts.
- **Filesystem safety:** all root creation goes through the one bootstrap script
  with the guards in §3.

## 6. Lifecycle (gate-driven)

| Phase | Gate / action |
|---|---|
| **0 Install** | Create `projects/` tree, category folders, `_index`, `PROJECT-PROTOCOL.md`, agent pointer files. One-time. |
| **1 Intake + bootstrap** | Resolve root; infer title + category (confirm); **dry-run write plan**; bootstrap; local git init; `.gitignore`; schemas. |
| **2 Discovery interview** | objectives · **authorization/scope ownership** · **isolation/egress + kill-switch** · environment (EVE-NG Community/Pro, images, snapshots / production rollback) · tooling · **evidence capture + hashing + retention** · **redaction policy** · success criteria · **decommission plan** · publish intent. |
| **3 Roadmap + tasks** | Mandatory gates: authorize+classify → baseline+snapshot+hashes → build/harden → deploy w/ version locks → execute → analyze/validate → redact+repro-bundle → publish-approval → decommission. Suggested paths → user selects. |
| **4 Task loop** | Per task: authorize → snapshot/baseline → isolation check → execute (domain skill returns a **structured report**: changed files, commands, risks, tests, blockers) → capture evidence + hash → inline build-log note under the task → checkpoint (before/after git status, exit codes, limitations, rollback point). Kill-switch on unsafe egress. **Conductor owns all state; domain skills only operate within the project root and report back.** |
| **5 Consult gates** | Capability-based roles; redacted/allowlisted artifacts only; sequential + locked (opencode shares one SQLite DB → concurrent runs hit "database is locked", confirmed in practice); provenance (model, prompt hash, artifact hash, timeout, result path); advisory-only. |
| **6 Completion + publish** | build-log → automated redaction pass → **manual review gate** → reproducibility bundle (tool/version locks, bootstrap + destroy scripts) → publish manifest → Astro page bundle → deploy approval. |
| **7 Undo** | Shares manifest/checkpoint machinery. |

## 7. Two-layer notes

- **Build log** (`build-log/`, internal): chronological raw record per task —
  steps, commands, decisions, dead-ends, issues + fixes, limitations.
- **Publication** (`publish/` → Astro, public): a curated narrative **generated
  from** the build log at completion. Publication never reads raw build logs
  directly — only sanitized, allowlisted artifacts.

## 8. EVE-NG / topology pipeline

1. Treat the EVE-NG **`.unl` file (XML) as the single source of truth**, not the
   HTML/PNG export (those are not diffable, editable, or automatable).
2. Parse `.unl` → structured `topology.json` (nodes, interfaces, networks,
   coordinates); annotate with roles, addresses, icons.
3. Generate: **Mermaid** (logical, version-controlled) and **Graphviz DOT → SVG**
   (precise, vendor icons) for the web. Keep PNG as a thumbnail only.
4. Embed SVG in the site; optionally wrap in a Cytoscape.js/D3 viewer for
   pan/zoom in MDX.
5. **Verify the parser against a real export first** — `.unl` schema differs
   between EVE-NG Community and Pro.

## 9. Publication: Astro + Tailwind + MDX (chosen)

Cloudflare Pages via Astro's static output. MDX components for "gravitational"
technical write-ups: `TopoViewer` (pan/zoom SVG), `CommandBlock`, `IOCCallout`,
`EvidenceFigure`. Per-project Open Graph images. Diagrams shipped as optimized
SVG. Accessibility: alt text, captions, keyboard-navigable diagrams.

> Trade-off accepted: more upfront design effort than Hugo+Congo, in exchange for
> full design control and interactive topology. Runs as a separate pipeline from
> any existing Hugo site.

## 10. Consult integration

Reuse `consult-orchestrator` + the tuned `consult-opencode.sh` / `consult-codex.sh`
wrappers (sealed, timeout-bounded, provider-pinned, `--title` set to suppress the
auto-title side-call). `project-consult-panel` adds the redaction/manifest layer.
Roles by capability: code correctness, prose, implementation/diff review,
security review, synthesis.

## 11. Rejected / deferred

- **~14 standalone governance skills** (authorization-gate, evidence-custody,
  redaction, reproducibility-engine, …). Real needs, wrong shape: they become
  **gates + references inside the conductor** plus reuse of the security skills.
- Standalone `project-scaffold` / `project-discovery` (folded into conductor).
- Broad `topology-studio` (narrowed to `eve-ng-topology`; Excalidraw/LaTeX later).

## 12. Verify-at-build (weak/unconfirmed)

- Astro Cloudflare adapter specifics and MDX component ergonomics.
- EVE-NG `.unl` schema differences (Community vs Pro) — validate the parser
  against a real export before relying on it.

## 13. Provenance

- **Codex (gpt-5.5, read-only):** root-creation safety, secrets/git strategy,
  per-project state vs single pointer, conductor-owned task loop, capability-based
  consult roles, skill-merge guidance.
- **Kimi K2.7 (read-only, sealed):** governance gaps in the interview (authorization,
  isolation, evidence custody, redaction, decommission), `.vault`/`.publish`
  split, per-task safety gate + kill-switch, EVE-NG `.unl`-as-source pipeline,
  publication-stack comparison.
- **Claude (conductor):** verified claims against the repo, rejected the skill
  sprawl, synthesized this plan, owns all writes.

## 14. Next actions

1. (chosen) Save this plan — done.
2. Draft `project-build-loop` SKILL.md + `bootstrap_project.sh` + `secret_scan.sh`
   + schemas via `skill-creator`.
3. Prototype `eve-ng-topology` against a real `.unl` export.
4. Stand up the Astro publication skeleton for `project-publish`.
5. Build `project-consult-panel` (redaction layer) and `undo-project-build-loop`
   on the conductor's machinery.

---

# 15. Project classification & dual-use rating (keystone)

> Added 2026-06-27 after a second `consult-orchestrator` round (Codex + Kimi).
> **Refines §5 (placement) and §6 (lifecycle).** This is the layer that lets the
> conductor infer correct tooling and handling *from the project type* — the
> piece the first pass missed.

## 15.1 Why

Tooling, placement, and especially publication must be driven by **what kind of
project it is** and **how dual-use it is**, not chosen ad hoc. Worked contrast:

- **OSINT anonymity chain** (Kali → WireGuard → Mullvad → *own, authorized*
  target): defensive/privacy research → **low-moderate** tier. But the *methods*
  are still dual-use, so the **publication** of tradecraft is rated higher than
  the activity.
- **MITM / interception tooling** (capture → EVE-NG lab → usable for real-world
  troubleshooting *and* for attacks): **high dual-use** → default private,
  weaponizable detail redacted, defensive-framing-only write-up, mandatory
  security-review consult.

## 15.2 Core model (deterministic, not vibes)

Both consultants agreed the v0 "4-axis 0–3 → tier" rubric is too fuzzy to enforce.
Final shape:

1. **Archetype routes; capability flags rate.** Keep them separate.
   - `archetype` (primary/secondary) selects the **default skill bundle** and
     placement defaults. It is *routing*, never policy.
   - `capability_flags` (a controlled enum) drive the **risk tier** via
     deterministic rules. Proposed enum: `passive_recon`, `active_scan`,
     `packet_capture`, `traffic_decryption`, `mitm_proxy`, `exploit_poc`,
     `malware_sample`, `credential_material`, `production_target`,
     `third_party_target`, `internet_egress`.
2. **Authorization is a GATE, not a score.** A separate `authorization` object
   (owner, scope, target list, dates, allowed/excluded actions, evidence path,
   egress rules, kill-switch) must read **authorized + scoped + isolated** or the
   action is **no-go**. Strong authorization *permits* work; it never lowers a
   capability tier.
3. **Dual-use risk and data sensitivity are two axes.** A PHI app is high-
   sensitivity / low-offensive; a MITM lab is offensive-sensitive even with
   synthetic data. Track `dual_use_tier` and `data_classes` independently; the
   stricter of the two sets the `artifact_class_floor`.
4. **Decision-tree tiers** (capability-flag triggers, not point sums):
   - **T0** informational / docs / normal app, no security-sensitive capability.
   - **T1** defensive or owned-environment work, no attack-enabling deliverable.
   - **T2** dual-use but bounded to lab / owned target / defensive telemetry.
   - **T3** usable interception, exploitation, scanning, malware handling,
     credential-adjacent, or live-target capability **even with authorization**.
   - **T4** missing/unclear authorization for live targets, credential theft,
     persistence/evasion, destructive actions, public-target exploitation,
     bypass guidance, or exfiltration.
   - Split the old `traffic-interception` archetype: **passive capture → T1**,
     **active MITM positioning → T3**, **+ credential/session capture or cert
     forgery → T4**.
5. **Unknown = restrictive.** Unknown target ownership, egress, data class, or
   publish intent applies the **higher** tier and blocks risky actions until
   resolved. A provisional `T1-T2` is fine during discovery, but `project.json`
   stores one confirmed tier or `review_required`, and enforces the higher tier
   while unresolved.

## 15.3 `project.json` classification block (result, not policy)

```json
"classification": {
  "policy_version": "1.0",
  "status": "provisional | confirmed | review_required",
  "archetype": { "primary": "...", "secondary": "..." },
  "capability_flags": ["packet_capture", "..."],
  "dual_use_tier": "T0..T4",
  "data_classes": ["pii", "credentials", "..."],
  "artifact_class_floor": "secret|private|internal|public",
  "required_gates": ["authorization", "isolation", "redaction"],
  "satisfied_gates": ["..."],
  "publish_policy": "no-publish | defensive-only | full",
  "git_policy": "local-only | private-remote-approved | blocked",
  "rationale": { "rule_ids": ["..."], "evidence_refs": ["..."] },
  "override": { "reason": "...", "reviewer": "..." }
}
```

Policy itself lives in `references/project-archetypes.md` (taxonomy + examples)
and `references/dual-use-rating.md` (tier rules, capability-flag triggers, the
gate table, publish profiles, and **golden-example fixtures**: own-target OSINT,
passive lab capture, MITM router, authorized pentest, malware sandbox, PII app,
hardening-only). The LLM **proposes** the classification; deterministic policy
data **validates** it before any execution.

## 15.4 Tier → gate table (fail-closed, per-action)

Gating is **per action**, not only per project — a task that introduces
`mitm_proxy` / `traffic_decryption` / `exploit_poc` re-validates the tier before
the conductor routes to a domain skill.

| Tier | Tooling | Git | Consult | Publish |
|---|---|---|---|---|
| T0/T1 | normal | local; remote after scan+approval | optional | after scan + approval |
| T2 | authorization + isolation re-checked | private/sanitized remote, explicit approval | redaction manifest required | **defensive/troubleshooting narrative only** |
| T3 | explicit authorization + isolation **proof** before offensive tooling | **no remote** by default | **security-review consult required**; allowlisted sanitized artifacts only | default **no-publish**; exception needs security review + manual approval + redaction diff + publish manifest |
| T4 | **block** active execution/tooling | **block** | planning/scoping analysis only | **never** |

**Reclassification triggers:** if a later task adds packet capture, live targets,
credentials, malware, exploit code, or public-publish intent, classification is
**invalidated and rerun**. Upward tier changes are automatic; **downward** changes
require explicit human rationale + an `event-log.jsonl` entry.

## 15.5 Publication is gated by controls, not disclaimers

A dual-use disclaimer is boilerplate that runs *after* the real controls pass — it
is **not** itself a control. The actual controls:

- **Allowlisted publish manifest** + forbidden-content rules + redaction review +
  a hard pre-publish gate.
- **Redact:** exploit payloads / one-liners, ready-to-use control-bypass configs,
  real hostnames/IPs/domains (use **RFC 5737** IPv4 and **RFC 3849** IPv6
  documentation ranges), certs/keys/tokens/credentials, PII/org-identifying data,
  full payload PCAPs (publish only sanitized/truncated/synthetic), precise
  topology, screenshot EXIF/metadata, exact timestamps.
- **Required defensive framing (purple-team narrative):** state authorization +
  isolation; a **Detection** section (IOCs, Sigma/Suricata rules, log sources,
  alert logic); a **Mitigation** section (segmentation, TLS/MACsec, 802.1X, cert
  pinning, hardening); structure as **attack → detect → harden**, methodology not
  weaponized tooling.
- **Refuse public publication when:** no written authorization evidence; real/
  identifiable data present; unpatched vuln without coordinated disclosure;
  export-control/legal says no; content mainly lowers the attack barrier with
  little detection value; NDA/confidentiality applies; or any active MITM/session
  capture against a non-isolated target.

## 15.6 Placement, portfolio, and revocation (revises §5)

- **No "restricted" folder names** — they leak project intent through paths. Use
  **neutral slugs**; keep the tier in **private metadata** (`project.json` +
  local index), never in the path.
- **Two portfolio indexes:** a **private** local index groups all projects by
  archetype/tier/status; a **public** portfolio index reads **only approved
  publish manifests** and never reveals unpublished T3/T4 project names.
- **Audience classes** (separate from artifact classes): `internal-only`,
  `client-confidential`, `community-shared`, `public`.
- **Revocation/embargo:** a mechanism to pull or embargo a published post if risk
  changes; plus a **spill/spillage IR** mini-runbook (lab leaks into production,
  or real traffic gets captured) and a **retention/destruction** schedule for
  authorization, captures, and logs.
- **Tool supply-chain vetting:** EVE-NG images, GitHub tools, and container
  images are vetted before use (they can be malicious or exfiltrate).

## 15.7 New archetypes to seed the taxonomy

Beyond the v0 list, seed: vulnerability-research/exploit-dev, reverse-engineering,
active-directory/identity-lab, cloud-security-lab, container/k8s-security,
wireless/RF, ICS/OT/SCADA, social-engineering/phishing-sim, purple-team,
supply-chain/SCA, mobile-security, crypto/PKI, threat-intel-production.

## 15.8 Net effect on the skill set (still 5 skills)

This stays **conductor-owned** — no new skill. It adds to `project-build-loop`:
`references/project-archetypes.md`, `references/dual-use-rating.md`, the
`classification` + `authorization` schema blocks, and a `scripts/policy_check`
pre-action validator (fail-closed). `project-consult-panel`'s redaction layer and
`project-publish`'s pre-publish gate consume the tier and publish policy.
