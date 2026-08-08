---
name: agent-orchestra
description: "Wrapper-only agentic CLI orchestration, conductor-agnostic: whichever agent invokes it (Claude Code by default; OpenCode or Gemini CLI otherwise) is the intelligence and delegates token-heavy work to non-Claude lanes to preserve usage and rate limits, with an OpenCode fallback when Codex is rate-limited or down. Use when the user asks for an orchestra/orchestrator, wants to offload work to save Claude usage or avoid rate limits, asks any agent to access Codex, wants gpt-5.6 through Codex for consult/review/implementation, wants OpenCode specialist lanes (Kimi K3, DeepSeek V4 Flash, MiMo), runs OpenCode as conductor, mentions replacing codex-consult/opencode-consult/consult-orchestrator, wants Codex without a plugin, needs multi-model review, wants parallel lanes with a run ledger, or needs cost-steered model routing (gpt-5.6 Sol/Terra/Luna, sonnet-5, opus-4.8, fable-5). Do not use for routine one-agent edits, secret-bearing prompts, or unrestricted autonomous writes."
---

# Agent Orchestra

## Overview

Coordinate Claude Code, Codex CLI, and OpenCode without blurring authority,
and without plugins — the shell wrappers are the entire integration surface.
The skill is conductor-agnostic: Claude Code conducts by default, but any
agent that can run shell commands (OpenCode, Gemini CLI) conducts the same
way when Claude is unavailable.

The point is Claude-usage economics: Claude subscriptions rate-limit fast when
Claude reads whole repos, writes bulk code, or chews through long diffs.
Delegating that work to the default three-stage pipeline — OpenCode Go's latest
DeepSeek V4 Flash at `max` implements, `gpt-5.6-luna` at `max` critiques, and
`gpt-5.6-sol` at `xhigh`
overviews — plus the other OpenCode specialist lanes
moves the token burn onto Codex/OpenCode Go quota instead, while Claude — the
conductor — spends its limited budget on what actually needs it: scoping,
verification, taste, and final judgment. When a selected stage is
rate-limited, times out, or is down, the remaining distinct lanes provide the
fallback ladder (see "If a Stage Cannot Continue") so bulk work still stays
off-Claude. The OpenCode lanes are
themselves cost-tiered: DeepSeek V4 Flash handles the high-volume work while
Kimi K3 is available only when a distinct alternate specialist is useful.

Use this as the canonical replacement for the old `codex-consult`,
`opencode-consult`, and `consult-orchestrator` entry points. Those skills are
now thin forwarders into this one.

## Read First

- For model choice, delegation economics, and "never Haiku" rules, read
  `references/model-routing.md`.
- To present the selectable jobs/models or resolve a call without spending
  quota, run `scripts/orchestra-agent.sh --list` or use `--dry-run`.
- For task-local role contracts and the optional risk-gated plan review, read
  `references/task-local-roles.md` when the task is complex, high-risk, or
  explicitly requires plan approval.
- To inspect passive local prerequisites (CLI versions, reported credentials,
  configured routes, and catalog membership) without a model call, run
  `scripts/orchestra-doctor.sh`.
- For automation that must fail on degraded local readiness, run
  `scripts/orchestra-doctor.sh --require-ready`. The doctor never makes a model
  call, so it reports live callability as unverified.
- To list Codex configuration and the passive OpenCode catalog, run
  `scripts/orchestra-doctor.sh --models`; catalog membership is not proof of
  provider acceptance, quota, routing, or a successful invocation.

## The Conductor Is the Intelligence, Not a Dispatcher

The conductor is whichever agent invoked this skill — Claude Code by default,
but OpenCode or Gemini CLI conduct the same way when Claude is unavailable
(see "Who Conducts"). The conductor is not an agent-caller that forwards
prompts and pastes back answers: its intelligence is the product of this
system, and the lanes are its hands and eyes. Delegation replaces the
conductor's typing and reading — never its thinking. Concretely, the
conductor:

- **Decomposes** the problem: what sub-tasks exist, what evidence each needs,
  which lane fits each shape, and what "done" looks like — before any call.
- **Writes sharp briefs**: a lazy one-line brief produces consultant garbage
  that costs more to verify than it saved. Objective, exact files/diffs,
  constraints, expected output format, evidence requirements.
- **Cross-examines** what comes back: checks concrete claims against the
  repo, notices what a consultant missed, spots contradictions between lanes,
  and rejects confident-sounding wrong answers.
- **Synthesizes**: when lanes disagree, Claude adjudicates with evidence, not
  majority vote. One coherent solution comes out, not a stapled digest.
- **Keeps the thinking work**: design decisions, subtle bugs where insight
  beats volume, small precise edits, and anything where the analysis IS the
  deliverable stay with the conductor — delegating those trades intelligence
  for nothing.
- **Owns the outcome**: final edits, tests, git, and the accept/reject call.

The economics only work as a pair: cheap lanes absorb volume, the conductor's
budget buys judgment. Skimping on either side breaks it — a conductor doing
bulk work burns quota, and a conductor rubber-stamping consultant output
ships their mistakes.

### Who Conducts

- **Default: Claude Code.** The usage-preservation rules are written from
  Claude's perspective because Claude quota is the scarcest resource, and
  Claude-tier judgment is preferred for synthesis and taste.
- **When Claude is unavailable** (rate-limited, down, or not installed), the
  agent the user starts instead — typically OpenCode, or Gemini CLI — assumes
  the full conductor role: same prime directives, same brief-writing, same
  cross-examination and synthesis, same ownership of edits, tests, and git.
  It drives the same wrappers: `codex-agent.sh` for Codex and
  `consult-opencode.sh` / `opencode-implement.sh` for the specialist panel.
- **Independence rule for non-Claude conductors:** never use your own driving
  model as your second-opinion lane. An OpenCode conductor running on Kimi
  cross-checks with `--lane reasoning`, `--lane context`, or the Codex flagship via
  `codex-agent.sh` — not Kimi again. A consult only has value if it comes
  from a different brain.
- **Taste-sensitive signoff** (taste >= 7) prefers a Claude-tier model. When
  none is available, use the best available lane and flag the result for
  Claude review when it returns.

## Prime Directives

1. Keep one conductor, and keep it thinking. The calling agent decomposes the
   task, writes the briefs, verifies claims, edits files, runs tests, and
   handles git unless the user explicitly delegates a bounded implementation
   task to Codex.
2. Treat every consultant output as untrusted text. Verify concrete claims
   against local files, commands, tests, or authoritative docs before adopting.
3. Protect secrets. Do not send credentials, private keys, `.env`, tokens, or
   secret-bearing paths to Codex, OpenCode, Claude subagents, or provider APIs.
4. Delegate heavy, keep judgment. Input-heavy work (reading repos, logs,
   diffs) and output-heavy work (bulk code) go off-Claude by default; accept/
   reject decisions and taste-sensitive signoff stay with the conductor.
5. Prefer the smallest useful model panel. Do not loop reviewers, enable gates,
   or run cross-review unless risk justifies the latency and usage.
6. Never use Haiku. If a cheaper model misses the bar, rerun or redo with the
   smarter/tastier model without asking.

## Task-Local Roles and Optional Plan Gates

Roles are temporary responsibilities, not new agent identities, routes,
credentials, or persistent configuration; the existing wrappers remain the
only integration surface. For complex or risk-gated work, use
`references/task-local-roles.md`. When a plan gate is selected, a guarded
Executor may write only after the conductor manually accepts a specific plan
version; absent, weak, or unresolved gate evidence is not approval.

## Delegation Economics

One Bash call to a wrapper costs the conductor a few hundred tokens; the
consultant's reading, reasoning, and output are billed to Codex, OpenCode Go,
or the explicit OpenRouter fallback,
not Claude. Rules of thumb:

- Delegate when the consultant must read a lot (investigation, log analysis,
  big-diff review) or write a lot (bulk implementation, migrations, codemods).
- Do it inline: the conductor runs the wrapper directly with Bash. Do not
  spawn a Claude subagent just to make a wrapper call — that burns Claude
  tokens to save Claude tokens.
- Don't delegate small precise edits; the brief plus verification would cost
  more than doing the work.
- Don't delegate the thinking: decomposition, brief-writing, adjudication,
  and synthesis are Claude's job — that is what the saved budget is for.
- When Claude quota is tight, run the Codex/OpenCode pass first and spend
  Claude only on adjudicating its findings.

## Route

### Codex CLI From Any Agent

Use `scripts/orchestra-agent.sh` as the preferred selector and
`scripts/codex-agent.sh` as the hardened direct Codex entry point:

```text
scripts/codex-agent.sh consult --cd <repo> -- "<brief>"
scripts/codex-agent.sh review --uncommitted
scripts/codex-agent.sh review --base main --prompt "<focus>"
scripts/codex-agent.sh implement --allow-write --cd <repo> --scope <path> --no-plan-gate -- "<task>"
scripts/orchestra-agent.sh implement --allow-write --cd <repo> --scope <path> --no-plan-gate -- "<task>"
```

Modes:

- `consult`: read-only `codex exec`; use for investigation, data analysis,
  second opinions, and design critique. MCP off by default; reasoning effort
  floored to high; works on non-git directories.
- `review`: native `codex review`; defaults to Luna at `max` on
  `--uncommitted`; accepts `--cd`. The selector's final overview is a separate
  Sol `xhigh` review.
- `implement`: guarded `codex exec --sandbox workspace-write`; requires
  `--allow-write`, at least one explicit `--scope`, a git repo, and either
  `--plan-record <file>` or `--no-plan-gate`; refuses `main`/`master` unless
  `--allow-main` is explicit, disables MCP, and instructs Codex not to commit
  or push. Scopes are validated literal repository-relative prefixes; scoped
  symlinks, repository symlinks resolving outside the root, and existing
  secret-shaped descendants are refused. The wrapper snapshots HEAD,
  refs/config/reflogs, the index, and every out-of-scope filesystem entry
  (including ignored files and empty directories), tolerates a dirty baseline,
  and fails if any of that state changes.
  It reports violations without reverting anything. Use `--scope .` only for
  explicit whole-repository authority.

All modes are time-bounded (consult 900s, review 1800s, implement 3600s;
override with `--timeout N` or `CODEX_AGENT_TIMEOUT`, 0 disables) so a stalled
call can never hang the conductor.

Only use `implement` when the user clearly wants Codex to make changes. Prefer
a working branch or isolated worktree. The wrapper never uses
`danger-full-access` or `--dangerously-bypass-approvals-and-sandbox`.

Codex selection is per call. Aliases `sol`, `terra`, and `luna` are resolved
by `orchestra-agent.sh`; raw IDs remain available. User defaults are Luna
`max` for critique and Sol `xhigh` for final overview. Direct consult and
direct Codex implementation use config/default model selection unless the
caller passes `--model`.

Effort is steered per call with
`--effort none|low|medium|high|xhigh|max`; explicit selection wins. `ultra`
remains refused because it is not a documented Codex reasoning effort. Never
route work to a model that has not been onboarded and pass the current caller
model with `--current-model` when known so the selector can reject self-review.

### Unified Selection and Default Pipeline

```text
scripts/orchestra-agent.sh --list
scripts/orchestra-agent.sh implement --dry-run --allow-write --scope <path> --no-plan-gate -- "<task>"
scripts/orchestra-agent.sh implement --allow-write --scope <path> --no-plan-gate -- "<task>"
```

The implementation selector runs three independent stages by default:

1. Worker: OpenCode Go / latest DeepSeek V4 Flash / `max` reasoning.
2. Critiquer: Codex / Luna / `max`.
3. Overviewer: Codex / Sol / `xhigh`, with the Luna critique included as
   untrusted evidence to verify.

Override with `--model`, `--reasoning`, `--critic-model`,
`--critic-reasoning`, `--overview-model`, or `--overview-reasoning`.
`--dry-run` prints the resolved topology without calling a provider. The
selector rejects duplicate stage models and a known caller/model collision
unless the user explicitly passes `--allow-same-model`.

When the user asks to choose, run `--list`, present the compact jobs/models/
reasoning choices, and wait for their selection. Do not dump the raw provider
catalog unless requested. When the user does not ask to choose, use the
three-stage defaults without adding a confirmation round trip.

### OpenCode Specialist Lanes From Any Agent

Use OpenCode for alternate-provider perspective and the standard lanes:

```text
scripts/consult-opencode.sh --lane code      --sealed -- "<technical/config/security brief>"
scripts/consult-opencode.sh --lane reasoning --sealed --timeout 480 -- "<deep reasoning / architecture brief>"
scripts/consult-opencode.sh --lane context   -- "<big-log/diff/repo sweep brief>"
scripts/consult-opencode.sh --lane prose     --sealed -- "<writing/readability brief>"
scripts/consult-opencode.sh --model provider/model --sealed --timeout 240 -- "<inline brief>"
```

Lane defaults (override with `ORCHESTRA_LANE_CODE`, `ORCHESTRA_LANE_REASONING`,
`ORCHESTRA_LANE_CONTEXT`, `ORCHESTRA_LANE_PROSE`):

- `code` → `opencode-go/kimi-k3`
- `reasoning` → `opencode-go/kimi-k3` — a compatibility task-shape alias for
  the same alternate specialist. Use Kimi when a distinct non-DeepSeek view is
  needed; do not add it automatically to the default three-stage pipeline.
- `context` → `opencode-go/deepseek-v4-flash` — OpenCode Go's rolling latest
  Flash route and default implementation worker at `max`; inexpensive and
  suited to ~1M-context sweeps. Read-only context consults do not force an
  effort unless selected. Use the pinned OpenRouter 0731 route explicitly
  when reproducibility or provider control matters more than subscription cost.
- `prose` → `openrouter/xiaomi/mimo-v2.5-pro`

Sealed vs non-sealed is a containment choice, not just an ergonomic one. Use
`--sealed` when all context is inline (attach a long brief with `--file`
instead of pasting it). Without `--sealed`, the consultant can read every file
under `--dir` itself — the cheapest way to audit many files, but that includes
untracked files like `.env`; the secret guards only screen the prompt text and
attached filenames, so never point a non-sealed consult at a tree holding
secrets. Run OpenCode lanes sequentially — they share one local SQLite state
and concurrent runs can fail with "database is locked".

Capture wrapper output by redirecting stdout to a file and reading it after
exit (`wrapper ... > out.md 2> err.log`; progress lines go to stderr). Never
pipe a backgrounded wrapper through `tail`/`head` — the pipe can stall the
call at zero bytes. The wrappers' own timeouts already bound a stalled run.

### If a Stage Cannot Continue

OpenCode Go DeepSeek V4 Flash at `max` is the default implementation worker. If that lane
fails — rate-limit/usage errors, auth errors, outage, or repeated timeouts —
pick another OpenCode lane by task shape or explicitly choose a Codex worker;
do not silently pull bulk work back into Claude:

1. `consult` → hard thinking or a distinct alternate view on a bounded brief:
   `--lane reasoning` (Go Kimi K3). Input-heavy sweep of logs/diffs/repo:
   `--lane context` (Go DeepSeek V4 Flash). Config/correctness checks:
   `--lane code` (Kimi). Non-sealed lets the model read the repo itself.
2. `review` → generate the diff locally (`git diff`), send it sealed to
   `--lane code`; `--lane reasoning` for architecture-level review;
   `--lane context` for very large diffs.
3. `implement` → `scripts/opencode-implement.sh --allow-write --cd <repo>
   --scope <path> --no-plan-gate -- "<task>"`. Guarded like Codex implement (git repo
   required, refuses main/master, secret guard, bounded timeout, and the same
   filesystem/index snapshot enforcement), but the
   agent gets file read/search/edit tools only — no shell — so it structurally
   cannot commit, push, or run commands. Defaults to Go DeepSeek V4 Flash at `max`;
   `--lane reasoning` for hard tasks, `--lane context` for long-context bulk
   edits. The conductor reviews the printed working-tree changes, runs tests,
   and owns git.
4. Only when OpenCode is also down does the conductor do bulk work in Claude —
   and it should tell the user, who may prefer to wait.

After fallback implementation, retain independent Luna critique and Sol
overview whenever those Codex routes are available.

## Parallel Fan-Out (Split, Mark, Join)

One conductor does not mean one consultant at a time. When a task decomposes
into genuinely independent sub-tasks, fan them out concurrently — the
conductor stays the single point of alignment and merge.

For a large behavior-preserving port, rewrite, migration, codemod, or failure
campaign, invoke `run-large-code-changes`. It owns the preservation baseline,
pattern and semantic-delta contract, representative pilot, inventory-backed
work queues supplemented by diagnostics, and progressive phase gates. Agent
Orchestra still owns routing, containment, and the final accept/reject decision;
do not duplicate those protocols in worker briefs.

For high-risk fan-out, the writer does not approve its own work. Give a
read-only reviewer a separate context containing the diff, relevant source
behavior, contract, and oracle expectations, but not the writer's rationale.
The conductor verifies findings before a fixer applies them. Start with one
reviewer; use two orthogonal reviews only when blast radius or semantic risk
justifies the extra cost. If a defect class repeats, stop the affected wave,
repair and version the shared brief/contract/rubric, then rescan units produced
under the older version before launching more work. When a plan gate is
selected, apply the independent-review and fail-closed protocol in
`references/task-local-roles.md` before any writer starts.

1. **Split.** Decompose into sub-tasks that do not overlap: if two sub-tasks
   would touch the same files or depend on each other's output, they are not
   independent — merge or serialize them. Write one self-contained brief per
   sub-task.
2. **Mark.** Give every brief the same alignment preamble — global objective,
   interface contracts, naming decisions, and a do-not-touch list — so
   parallel workers cannot drift apart. Record the fan-out in a run ledger
   (one scratch file): sub-task, lane/model, scope, output file,
   `execution_status`, `review_status`, and `integration_status`. Use
   `queued|running|returned|failed`, `pending|verified|weak|rejected`, and
   `pending|ready|integrated|rejected` respectively. The ledger is the marker
   that keeps every delegation accountable at join time.
3. **Launch.** Start each call in the background with stdout redirected to
   its ledger-named output file (never through `tail`/`head`). Concurrency
   rules: parallel Codex calls are fine (separate processes); OpenCode lanes
   stay sequential (shared SQLite state), so at most one OpenCode call
   overlaps the Codex fleet. Parallel `implement` runs must never share a
   working tree — one isolated `git worktree` per writer, no exceptions.
4. **Join and verify.** When all calls exit, read each output file, verify
   claims against the repo exactly as for a single consult, mark each row's
   review status `verified`, `weak`, or `rejected`, and set integration to
   `ready` or `rejected`. Cross-check the seams where
   sub-tasks meet — interfaces, naming, duplicated helpers — that is where
   parallel work drifts.
5. **Route fixes.** For rejected or buggy output, write a fix brief that
   quotes the failure evidence (test output, the wrong hunk, the contradicted
   file) and route it to the lane that fits the failure: the same model for a
   mechanical slip, a stronger reasoning or flagship lane when the approach
   itself was wrong. Re-verify on return. The conductor merges everything
   into one coherent change, marks accepted rows `integrated`, and owns the
   final diff.

Fan-out multiplies consultant tokens, not conductor judgment: it pays off at
roughly three or more independent sub-tasks, and a task that cannot be
cleanly split should stay serial rather than gain a coordination bug.

## Model Defaults

When the user does not specify a model, apply their defaults:

- Bulk/mechanical implementation and migrations: OpenCode Go DeepSeek V4 Flash worker
  at `max`.
- Implementation critique: Luna at `max`. Final overview/adjudication: Sol at
  `xhigh`.
- Repo investigation and hard debugging: select by task shape; use Codex for
  deep engineering judgment or DeepSeek context for volume.
- Technical second opinions and security framing: `--lane code` (Kimi K3).
  Deep reasoning or architecture/plan critique: `--lane reasoning`
  (Go Kimi K3). Huge-context sweeps and bulk summarization:
  `--lane context` (Go DeepSeek V4 Flash). Prose and docs polish: `--lane prose`
  (MiMo v2.5 Pro).
- User-facing UI, copy, API design, and product polish: require taste >= 7;
  use `fable-5` when available, otherwise `sonnet-5` or another taste-suitable
  lane.
- Plan and implementation reviews: default to Luna/max critique followed by
  Sol/xhigh overview; add a taste-focused Claude review only when justified.
- Thin Claude wrapper subagents (only when a subagent must own the call): use
  `sonnet-5` with low effort; the wrapper writes a self-contained Codex prompt,
  runs `scripts/codex-agent.sh`, and returns the output.
- Never choose Haiku, even for title generation or tiny helper calls.

For shipping work, prioritize intelligence, then taste, then cost. Cost breaks
ties — but between equal-fit lanes, prefer the one that does not burn Claude
quota.

## Orchestration Workflow

1. Frame one shared brief: objective, repo path, exact files/diff/snippets,
   constraints, allowed write scope, expected output, and evidence requirements.
   If a plan gate is selected, record this as immutable `Plan P1`.
2. Preflight the brief for secrets and secret-bearing file paths.
3. If the user requests selection, present `orchestra-agent.sh --list` and use
   their job/model/reasoning choices. Otherwise use Go DeepSeek worker → Luna/max
   critique → Sol/xhigh overview. Reject duplicate/caller-identical review
   models rather than silently reducing independence.
4. For a selected plan gate, obtain an independent read-only review, assign
   stable finding IDs, and manually accept one exact plan version before any
   Executor receives write scope. Stop after the bounded protocol; do not treat
   a missing or weak review as approval.
5. Prefer `scripts/orchestra-agent.sh` for selectable jobs and the default
   worker/critique/overview chain. Use the underlying wrappers directly for a
   deliberately single-stage call.
6. Build a claim ledger with source, evidence checked, and status:
   `verified`, `weak`, or `rejected`.
7. Synthesize the decision. Report verified findings first, then unresolved
   disagreements or weak claims. The conductor performs any edits and tests.

## Compatibility

Legacy prompts may still mention `codex-consult`, `opencode-consult`, or
`consult-orchestrator`. Treat those as aliases for this skill. Their bundled
scripts now forward to the canonical wrappers here, so existing project and
study panels keep working with a single underlying implementation.

## Maintainer Verification

After changing a wrapper or readiness rule, run:

```text
bash -n scripts/*.sh tests/test-wrappers.sh
tests/test-wrappers.sh
```

The tests use temporary repositories and fake CLIs. They make no model calls,
spend no provider quota, and verify that scope failures never trigger rollback.

## Done Checklist

- [ ] Delegated input/output-heavy work off-Claude instead of running it in
      Claude or a Claude subagent.
- [ ] Used `scripts/orchestra-agent.sh` or a hardened direct wrapper.
- [ ] Used OpenCode only with an explicit `--lane` or `--model`.
- [ ] Sent no secrets or secret-bearing paths.
- [ ] Kept review/gate loops manual and monitored.
- [ ] If a plan gate was used, recorded the accepted plan version and stable
      finding dispositions; no Executor started with an unresolved gate.
- [ ] Verified consultant claims before acting.
- [ ] For implementation, used `--allow-write`, required scoped paths, an
      explicit `--plan-record` or `--no-plan-gate`, and a non-main
      branch/worktree unless explicitly overridden.
- [ ] For fan-outs, gave every brief the shared alignment preamble, kept one
      writer per worktree, and joined through the run ledger before merging.
- [ ] For high-risk fan-outs, separated writer/reviewer/fixer authority and
      used a risk-based reviewer count rather than a fixed panel.
- [ ] Repaired repeated defect classes in the versioned workflow and rescanned
      outputs produced under the affected version.
- [ ] The conductor owned final judgment, tests, git, and review.
