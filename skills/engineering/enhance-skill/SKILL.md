---
name: enhance-skill
description: "Deconstruct an existing skill, find its gaps, and strengthen it security-first: tighten triggers, fill missing workflow/error/edge-case coverage, add helpful references or examples, and trim bloat or redundancy. Looks for opportunities to add capability AND to reduce surface area. Trigger when the user wants to improve, harden, extend, refactor, or fill gaps in a skill (their own or an imported one). Do not trigger for authoring a brand-new skill from scratch (that is skill creation) or for auditing only (use vet-skill)."
# --- provenance ---
category: engineering
source: self-authored (this repository)
author: agent-skills-repository
license: same-as-repo
retrieved: 2026-06-13
---

# Enhance Skill

Take an existing skill and make it measurably better without making it more
dangerous. Every enhancement is weighed against the security cost of adding it;
when in doubt, the smaller, safer skill wins. A skill that modifies other skills
is itself a powerful capability — so this workflow re-audits its own output.

Related meta-skills: [[vet-skill]] (audit before and after), [[name-skill]]
(rename if the improved scope changes what it should be called).

## Prime directives

1. **Security first, always.** No enhancement may add network egress, `eval`/
   `exec`, shell-out, side-loaded dependencies, or invisible content. If a
   capability can only be added unsafely, don't add it.
2. **Net-positive or don't ship.** A change must add real capability or remove
   real bloat. Cosmetic churn that risks regressions is not an improvement.
3. **Preserve provenance & intent.** Keep the original `source`/`author`/`license`
   header. Don't silently change what the skill is *for*; widen or sharpen scope
   only with the user's agreement.
4. **Reversible & reviewable.** Commit the skill in its current state first, so
   every enhancement is a clean, revertible diff.

## Workflow

### 1) Deconstruct
Read the whole skill and map its parts:
- **Frontmatter** — `name`, and especially the `description`/trigger (when it
  fires and when it must NOT).
- **Body** — overview, workflow steps, decision points, output contract.
- **Assets** — `references/`, `scripts/`, templates. Note runtime deps and any
  external commands.
Write a one-paragraph model of what the skill does and how, in your own words.

### 2) Gap analysis
Look for what's missing or weak, in priority order:
- **Security gaps** — unsafe example code, missing input-validation guidance,
  secrets handling, over-broad triggers that fire on sensitive contexts.
- **Trigger precision** — does it fire when it should and stay quiet when it
  shouldn't? Add explicit negative triggers ("Do not trigger for…").
- **Coverage gaps** — unhandled edge cases, error/failure paths, missing steps,
  undocumented assumptions, absent output format.
- **Usability gaps** — no examples, unclear invocation, paths that don't match
  this repo's layout, missing "requirements" section for deps.
- **Reference completeness** — workflow cites a file that doesn't exist, or a
  needed reference is absent.

### 3) Opportunity scan (add AND subtract)
- **Add capability** where it's high-value and safe: a worked example, a decision
  tree, a negative-trigger, a quick-start, a small helper reference.
- **Reduce surface area** where it's bloated: dead steps, duplicated prose,
  unused references, an over-long description, needless dependencies. Trimming is
  as valuable as adding — less surface = less risk and better triggering.
Rank candidate changes by (value × safety) ÷ regression-risk. Propose the top few.

### 4) Confirm direction with the user
Summarize the gaps found and the changes you propose (adds and cuts). Get
agreement before editing — especially for any scope change or dependency.

### 5) Implement carefully
- Make focused edits; keep each enhancement coherent.
- Match the skill's existing voice, structure, and naming.
- If you add a script or reference, it must be self-contained and dependency-light.
- Fix in-body paths to match this repo's actual layout while you're there.

### 6) Re-audit (mandatory) and re-test
- Run **vet-skill** (`skills/engineering/vet-skill/scripts/audit.sh <skill-dir>`)
  on the enhanced skill and eyeball every match. A clean-enough verdict is a
  release gate, not optional.
- If the skill ships scripts, re-check them (syntax compile, static danger scan)
  exactly as on import.
- Confirm `name` still fits; if scope shifted, run [[name-skill]] and keep
  directory + frontmatter + `REGISTRY.md` in sync.

### 7) Record what changed
Update `REGISTRY.md` if the name/scope changed. Commit with a message that lists
what was added and what was removed, so the enhancement is auditable later.

## Done checklist
- [ ] Original committed before edits (revertible baseline).
- [ ] Each change is net-positive capability or net-reduction in surface.
- [ ] No new network/exec/shell/side-load/invisible content introduced.
- [ ] vet-skill re-run and matches triaged.
- [ ] Shipped scripts re-scanned and compile clean.
- [ ] Provenance header intact; name/registry consistent.
