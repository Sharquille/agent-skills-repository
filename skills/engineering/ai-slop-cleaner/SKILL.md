---
name: ai-slop-cleaner
description: "Clean AI-generated code slop — dead code, duplication, needless abstractions, boundary leaks, weak tests — without drifting scope or changing behavior. A bounded, regression-safe cleanup pass: lock behavior with tests first, plan, classify smells, run one smell-focused pass at a time, then quality-gate. Trigger on 'deslop', 'anti-slop', 'remove dead code', 'simplify wrappers', or cleanup/refactor of code that feels bloated or over-abstracted. Do not trigger for new features, broad redesigns, or generic refactors with no simplification intent."
# --- provenance ---
category: engineering
source: https://skillrepo.dev/skills/Yeachan-Heo/ai-slop-cleaner
author: Yeachan Heo (adapted — genericized from the oh-my-claudecode/Ralph ecosystem to standalone)
license: MIT
retrieved: 2026-06-14
modified-by: Sharquille Andrew (enhancements/adaptation — MIT, see provenance note)
---

# AI Slop Cleaner

Clean AI-generated code slop without drifting scope or changing intended behavior.
This is a bounded cleanup workflow for code that works but feels bloated,
repetitive, weakly tested, or over-abstracted. Prefer deletion over addition;
keep diffs small, reversible, and smell-focused.

[`anti-slop-standard`](../anti-slop-standard/SKILL.md) defines what slop is and is in
force whenever anything is written. This skill is its remediation arm: it exists for
code that was written before the standard applied, or that got past it. The standard
names the rules; this workflow removes the violations safely.

The cleanup pass must preserve behavior, meaning, technical terminology, public
interfaces, and required wording. A word or pattern named by the standard is a review
signal, not proof that the implementation is defective.

## When to use

- The user says **deslop**, **anti-slop**, or **AI slop**.
- Cleaning up code that feels noisy, repetitive, or overly abstract.
- Prior work left duplicate logic, dead code, wrapper layers, boundary leaks, or weak regression coverage.
- The user wants a reviewer-only anti-slop pass (`--review`).
- The goal is simplification and cleanup, **not** new feature delivery.

## When NOT to use

- The task is mainly a new feature build or product change.
- The user wants a broad redesign instead of an incremental cleanup pass.
- A generic refactor with no simplification / anti-slop intent.
- Behavior is too unclear to protect with tests or a concrete verification plan.

## Execution posture

- Preserve behavior unless the user explicitly asks for behavior changes.
- Lock behavior with focused regression tests first whenever practical.
- Write a cleanup plan before editing code.
- Prefer deletion over addition.
- Reuse existing utilities and patterns before introducing new ones.
- Avoid new dependencies unless the user explicitly requests them.
- Keep diffs small, reversible, and smell-focused.
- Stay concise and evidence-dense: inspect, edit, verify, report.

## Scope control

Bound the pass to an explicit file list or changed-file scope when the safe
cleanup surface is already known. Preserve the same regression-safe workflow even
for a short file list, and **do not silently expand** a changed-file scope into
broader cleanup unless the user explicitly asks.

## Review mode (`--review`)

`--review` is a reviewer-only pass after cleanup is drafted, preserving
writer/reviewer separation. The same pass must not both write and self-approve
high-impact cleanup.

In review mode:
- Do **not** start by editing files.
- Review the cleanup plan, changed files, and regression coverage.
- Check specifically for: leftover dead code or unused exports; duplicate logic
  that should have been consolidated; needless wrappers/abstractions that still
  blur boundaries; missing or weak tests for preserved behavior; cleanup that
  changed behavior without intent.
- Produce a reviewer verdict with required follow-ups, and hand needed changes
  back to a separate writer pass instead of fixing-and-approving in one step.

## Workflow

### 1. Protect current behavior first
- Identify what must stay the same.
- Add or run the narrowest regression tests needed before editing.
- If tests can't come first, record the verification plan explicitly before touching code.

### 2. Write a cleanup plan before code
- Bound the pass to the requested files or feature area.
- List the concrete smells to remove.
- Order the work from safest deletion to riskier consolidation.

### 3. Classify the slop before editing
Each category is a violation of one rule in [`anti-slop-standard`](../anti-slop-standard/SKILL.md); read it for the definitions and tests, and record findings under these names.

| Category | Rule it violates |
|---|---|
| **Duplication** | Write it once |
| **Dead code** | Write only what is reached |
| **Needless abstraction** | Write the direct thing |
| **Boundary violations** | Write it where it belongs |
| **Missing tests** | Lock behavior as you write it |

### 4. Run one smell-focused pass at a time
- Pass 1: Dead code deletion
- Pass 2: Duplicate removal
- Pass 3: Naming and error-handling cleanup
- Pass 4: Test reinforcement

Re-run targeted verification after each pass. Do not bundle unrelated refactors into the same edit set.

### 5. Run the quality gates
- Keep regression tests green.
- Run the relevant lint, typecheck, and unit/integration tests for the touched area.
- Run existing static or security checks when available.
- If a gate fails, fix the issue or back out the risky cleanup instead of forcing it through.

### 6. Close with an evidence-dense report
Always report: **changed files**, **simplifications**, **behavior lock / verification run**, and **remaining risks**.

## Usage

```
ai-slop-cleaner <target>
ai-slop-cleaner <target> --review
ai-slop-cleaner <file-a> <file-b> <file-c>
```

## Good fits

- "deslop this module: too many wrappers, duplicate helpers, and dead code"
- "cleanup the AI slop in src/auth and tighten boundaries without changing behavior"

## Bad fits

- "refactor auth to support SSO" (new feature)
- "clean up formatting" (not slop cleanup)
