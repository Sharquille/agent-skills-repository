# Task-Local Roles and Risk-Gated Plans

Use this reference only when temporary role separation clarifies a complex
task, the user requests plan approval, or material risk justifies a gate. Roles
are prompt responsibilities for one task. They are not agents, accounts,
wrapper modes, saved routes, provider configuration, or credential stores.
The existing wrappers remain the entire integration surface.

The conductor may perform any role directly. When a role is delegated, choose
its lane from `model-routing.md` for that call; never create a persistent
role-to-model mapping. Keep task-local plan and finding state in the active
scratch/run ledger, not in personal configuration.

## Role Contracts

| Role | Required output | Must not |
|---|---|---|
| Planner | Immutable `Plan P<n>` with goal, scope and non-goals, assumptions, work units and dependencies, acceptance evidence, rollback, risk/gate status, and changes from the prior version | Implement, approve its own plan, or close findings |
| Advisor | Independent critique with evidence-backed candidate findings and blocker severity | Write files, approve implementation, self-resolve findings, or see another reviewer's rationale before its own review |
| Designer | Bounded UX, API, content, interaction, information-architecture, or design-system handoff with constraints, alternatives, and decision rationale | Treat preference as approval, implement, or expand scope |
| Researcher | Read-only evidence packet with source/location, observation, confidence or uncertainty, and implications | Turn weak evidence into a decision, implement, or approve |
| Executor | Bounded patch against one accepted plan version, tests/evidence, unverified assumptions, and residual risks | Start before a selected gate clears, expand scope, review its own work, close findings, commit, or push |

Only an Executor may receive `codex-agent.sh implement` or
`opencode-implement.sh`. Planner, Advisor, Designer, and Researcher calls stay
read-only unless the user explicitly delegates a bounded design-artifact edit.

In the unified selector, `worker` is the Executor stage, `critiquer` is an
independent Advisor stage, and `overviewer` is the conductor's final
verification/adjudication stage. These labels describe one task pipeline; they
still do not create persistent agents or role-to-model configuration.

## When To Select a Plan Gate

Use the gate when the user asks for plan approval or the task has material:

- security, privacy, authentication, authorization, or secret-handling risk;
- irreversible operations, persistent-data conversion, or difficult rollback;
- external side effects or breaking public contracts;
- broad, cross-component, or poorly understood blast radius; or
- uncertainty that makes implementation cheaper to prevent than to repair.

Do not gate routine edits merely to add ceremony. Once selected, the gate is
fail-closed for that task unless the user explicitly changes direction. The
Executor wrapper call must carry `--plan-record <file>`; an ungated low-risk
call must instead say `--no-plan-gate`, making the choice explicit at the
write boundary.

## Bounded Approval Protocol

The conductor owns the canonical plan, plan version, finding IDs, round count,
and final decision. Planner and Advisor never contact one another directly.

1. Create `Plan P1` from verified repository facts and the role contract.
2. Send that exact version to an independent Advisor in a fresh read-only call.
   Include acceptance criteria and evidence, but not the Planner's private
   rationale or another reviewer's draft.
3. The conductor records material findings as monotonic task-local IDs:
   `F-001`, `F-002`, and so on. IDs are never reused or renumbered.
4. If blocking findings exist, create `Plan P<n+1>`. State the disposition of
   every open finding and the semantic change from `P<n>`.
5. Re-review once. Two orthogonal Advisors, when blast radius justifies them,
   still count as one round and OpenCode lanes remain sequential.
6. Stop after at most two review rounds. Do not retry automatically. The
   conductor either accepts the exact current version, re-scopes, defers, or
   asks the user to adjudicate.
7. Release Executor work only after the conductor manually records the accepted
   `P<n>` and verifies every blocking finding's disposition.

The wrapper-facing acceptance record is deliberately small and must be a
regular, non-symlink file no larger than 64 KiB:

```text
plan: P2
status: accepted
independent-review: complete
blocking-findings: none
```

Use `blocking-findings: resolved` when the accepted revision closes recorded
blockers. The detailed plan and finding ledger remain task-local evidence; the
wrapper reads this summary but does not send its contents to the Executor.

Finding states are:

- `open` — not yet addressed;
- `addressed` — the plan claims a concrete resolution, awaiting verification;
- `verified-closed` — the conductor verified the resolution;
- `accepted-risk` — explicitly accepted by the conductor/user with rationale;
- `superseded` — made irrelevant by a verified scope or design change.

Missing, timed-out, malformed, same-brain, or weak independent review is not
approval. A material change to scope, assumptions, interfaces, or acceptance
evidence invalidates approval and requires a new plan version. If round two
still has an unresolved blocker, halt before implementation.

## Compact Task Packet

Use this shape for a delegated role:

```text
Role: <Planner|Advisor|Designer|Researcher|Executor>
Objective: <one bounded result>
Canonical input: <Plan Pn, diff, files, or evidence>
Constraints and non-goals: <exact limits>
Allowed scope: <read or write paths>
Required evidence: <tests, source locations, or acceptance checks>
Required output: <the role contract above>
Forbidden: <writes, approval, scope expansion, secrets, commits, pushes>
```

Role output is untrusted. The conductor verifies concrete claims, records
finding dispositions, and owns the accept/reject decision.
