---
name: run-large-code-changes
description: "Control large, behavior-preserving codebase changes with evidence-backed phases and bounded agent work. Use for multi-component ports, language or framework rewrites, migrations, high-volume codemods, or compiler/test-failure campaigns where ordinary review cannot cover the change and at least one credible executable oracle exists. Coordinates preservation contracts, semantic-delta analysis, representative pilots, inventory-backed work queues supplemented by diagnostics, isolated writers, independent reviewers, fixers, and progressive validation gates. Do not use for routine features, a single-module refactor, greenfield work, cleanup-only passes, secret-bearing delegation, unattended autonomous loops, or changes with no credible way to verify preserved behavior."
---

# Run Large Code Changes

Control changes too large for ordinary line-by-line review by making correctness
evidence, not agent throughput, the unit of progress. Preserve behavior first;
defer idiomatic cleanup and redesign until equivalence is green.

Use `agent-orchestra` for lane/model routing and bounded delegation. This skill
owns the change protocol. If `project-build-loop` is active, it retains project
state, policy, and lifecycle authority.

## Roles and authority

- **Conductor:** define the contract, own queues and shared files, set barriers,
  adjudicate reviews, run integration gates, and own git and release decisions.
- **Writer:** change one bounded unit. Never approve or integrate its own work.
- **Reviewer:** work read-only in a separate context. Try to falsify equivalence
  and report evidence; do not implement fixes.
- **Fixer:** apply only conductor-accepted findings. Use a separate context for
  high-risk work; the conductor may apply small mechanical corrections.

Start with one independent reviewer. Add a second, orthogonal review only for
high blast radius or semantic risk: memory/lifetime/FFI boundaries, concurrency,
security, persistent-data conversion, public compatibility, or cross-component
ownership. Reviewer count is risk-based, never a fixed ritual.

## 1. Qualify the change

Before creating agents or artifacts:

1. State whether the objective is behavioral preservation, intentional change,
   or both. Separate the two into different phases whenever possible.
2. Name the executable oracle: existing tests, differential/golden fixtures,
   compiler or static diagnostics, deterministic probes, benchmarks, or
   production canary signals. If no credible oracle exists, strengthen it before
   scaling or keep the work human-led and small.
3. Decide incremental migration versus coordinated cutover from evidence:
   stable seams, compatibility-bridge cost, rollback options, integration risk,
   and the ability to keep both paths correct. Never make a universal big-bang
   or incremental rule.
4. Fan out only when at least three non-overlapping units exist. Otherwise use
   the same contracts and gates serially; parallelism would add coordination risk.
5. Set disk, memory, process, I/O, and timeout budgets. Reduce concurrency when
   isolated worktrees or validation cannot fit with cleanup headroom.

## 2. Freeze the preservation contract

Create one task-local `CHANGE_CONTRACT.md`. Split it only if it becomes hard to
navigate; more files are not stronger governance. For a port, rewrite, migration,
or codemod, also create `SOURCE_INVENTORY.tsv`: long per-unit state is easier to
reconcile as rows than prose. Record:

- objective, scope, non-goals, source and target boundaries;
- behavior, public APIs, architecture boundaries, performance/resource bounds,
  and compatibility that must remain unchanged;
- intentional deltas, each with approval and a dedicated test or probe;
- baseline commands, environments, observed results, pass/fail/skip counts, and
  known failures;
- a pattern map for repeated source-to-target transformations;
- for every in-scope source unit: stable ID, source path/component, expected
  target or action, ownership boundary, dependencies, status, contract version,
  and an approved rationale for any exclusion;
- a semantic-delta ledger for constructs that look similar but differ in side
  effects, error behavior, overflow, evaluation order, ownership, lifetime,
  concurrency, layout, or release/debug behavior;
- phase gates, rollback boundary, queue unit, shared-file owners, and forbidden
  completion tactics.

Independently review the contract before implementation. Version it. Every work
unit and review result must record which contract version it used.

### Artifact budget

Default to a small fixed set of low-noise surfaces:

- `CHANGE_CONTRACT.md` for pattern maps, semantic deltas, budgets, gates, shared
  ownership, decisions, and rollback;
- `SOURCE_INVENTORY.tsv` only when source coverage must be enumerated;
- `RUN_LEDGER.tsv` for queue snapshot IDs, work units, contract versions,
  reviewers, evidence pointers, and separate status columns: `execution_status`
  (`queued|running|returned|failed`), `review_status`
  (`pending|verified|weak|rejected`), and `integration_status`
  (`pending|ready|integrated|rejected`);
- one `evidence/` directory for raw baselines, diagnostics, and gate output;
- `CLOSEOUT.md` for the final comparison and residual risks.

Create another artifact only when a distinct machine consumer, independent
owner, or navigation limit requires it, and record that reason in the contract.
Do not create one summary file per phase, platform, reviewer, map, or decision.

## 3. Establish the baseline

- Run the oracle against the unchanged system and retain raw results.
- Verify tests actually executed; record test, assertion, skip, quarantine, and
  platform counts where available.
- Prefer an implementation-independent suite. Add differential or golden tests
  for behavior coupled to the old implementation.
- Capture compatibility, performance, memory, binary/artifact size, and other
  resource baselines when they are part of the contract.
- Preserve known failures explicitly so agents cannot claim them as progress or
  silently move the goalposts.

Tests are evidence, not proof. Missing coverage remains a named risk even when
the suite is green.

## 4. Pilot before scale

Choose a small set that includes a typical unit, a boundary case, and the
highest-risk semantic pattern—not merely the easiest files. Run the full
writer -> reviewer -> fixer -> conductor-gate loop.

Scale only when the pilot proves:

- the contract and pattern map answer the writers' real decisions;
- reviewers find seeded or naturally occurring discrepancies with evidence;
- the target behavior matches the baseline for the pilot scope;
- queue units integrate without overlapping ownership;
- validation cost and workspace isolation fit the resource budget.

If the pilot fails, repair the contract or workflow and repeat it. Do not solve
pilot defects with undocumented one-off instructions.

## 5. Build a frozen work queue from authoritative inputs

For ports, rewrites, migrations, and codemods, the source inventory is the
coverage authority. Diagnostics cannot enumerate code that was never translated.
For a pure failure campaign, the diagnostic may be the inventory.

At each phase barrier, the conductor reconciles unresolved inventory rows, runs
the authoritative diagnostic once, stores the raw output, normalizes duplicate
or cascading failures, and assigns stable work IDs grouped by ownership boundary
or likely root cause. Diagnostics supplement the inventory; they never replace
source-coverage accounting.

- Freeze that snapshot for the wave; workers never mutate the authoritative
  queue directly.
- Give each unit one owner and an exact file/module scope. Shared files remain
  conductor-owned or run as a serialized unit.
- Put the contract version, inputs, scope, do-not-touch list, allowed commands,
  expected evidence, and exit criteria in every brief.
- Use one isolated worktree per parallel writer. Writers do not stash, reset,
  commit, push, merge, or run slow whole-repository commands.
- At the barrier, integrate accepted units, rerun the authoritative diagnostic,
  reconcile every source row, and generate a new queue. Worker-reported
  completion is never the phase state.

## 6. Run writer, reviewer, and fixer loops

For every work unit:

1. The writer produces a bounded diff and focused validation evidence.
2. The reviewer receives the diff, relevant original/target code or behavior,
   contract version, semantic-delta rows, and oracle expectations—but not the
   writer's rationale. Independence removes author bias; it must not remove the
   acceptance criteria.
3. The reviewer tries to find behavioral drift, invariant violations, fake
   completion, boundary damage, and missing tests. Every finding cites a hunk,
   contract clause, source behavior, or reproducible probe.
4. The conductor marks findings `verified`, `weak`, or `rejected`. No majority
   vote and no automatic application.
5. The fixer applies verified findings. The conductor reruns focused checks and
   records the unit's `integration_status` as `ready` or `rejected` in the run
   ledger.

When using two reviewers, give them different lenses rather than duplicate
prompts—for example semantic equivalence and lifecycle/concurrency safety.

## 7. Advance through evidence gates

Use only applicable gates, in this order, and record why any gate is omitted:

1. contract and baseline reviewed;
2. representative pilot passed;
3. source inventory reconciled: every unit mapped, intentionally excluded, or
   rejected with evidence; mechanical structure/coverage complete;
4. static checks and compilation complete without stubs;
5. link/start/basic invocation works;
6. targeted capability and differential tests pass;
7. full local suite passes with no new skips, deletions, or weakened assertions;
8. CI/platform matrix passes and the conductor verifies tests ran;
9. compatibility, performance, and resource bounds pass;
10. canary/staged rollout and post-change hardening pass when relevant.

The conductor runs expensive whole-system checks at barriers. Do not multiply
them across workers or infer behavioral correctness from compilation.

## 8. Repair the generating process

When a defect class repeats:

1. stop the affected wave;
2. add the defect and its detection method to the semantic-delta ledger or
   reviewer rubric;
3. version the contract, brief, validator, or queue rule that caused the miss;
4. rescan every unit produced under the older version;
5. regenerate the affected queue and resume only after the new pilot/check passes.

Fix the individual defect and the process that replicated it. A live prompt edit
without a back-scan leaves mixed-policy output and is not a repair.

## Reject false progress

Reject or explicitly justify every instance of:

- stubs, dummy returns, placeholder constants, `TODO`-as-implementation, or
  unsupported fallbacks;
- deleted/skipped tests, relaxed assertions, swallowed errors, broad suppressions,
  or behavior drift renamed as cleanup;
- speculative abstractions or idiomatic refactors during the preservation phase;
- self-review, compile-only completion, or comments that rationalize an unproven
  workaround instead of supplying evidence;
- agent count, lines changed, commits per minute, token volume, or elapsed time as
  a correctness metric.

A long comment is a review trigger, not automatic proof the code is wrong.

## Required closeout

Deliver an evidence-dense report containing:

- contract version and preserved/intentional deltas;
- baseline versus final oracle results, including skip/delete/count changes;
- source-inventory reconciliation, work-queue snapshots, and run-ledger status;
- verified/rejected review findings and workflow versions affected;
- phase-gate evidence, performance/resource comparisons, and platform coverage;
- known regressions, coverage gaps, rollback state, and remaining risks.

Do not declare completion while a required gate, back-scan, or known blocker is
open.
