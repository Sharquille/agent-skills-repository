---
name: agent-orchestra
description: "Wrapper-only agentic CLI orchestration, conductor-agnostic: whichever agent invokes it (Claude Code by default, OpenCode or Gemini CLI when Claude is unavailable) acts as the intelligence and delegates token-heavy work to non-Claude lanes to preserve usage and rate limits, with an OpenCode fallback ladder for when Codex itself is rate-limited or down. Use when the user asks for an orchestra/orchestrator, wants to save Claude usage or avoid rate limits by offloading work, asks any agent to access Codex, wants gpt-5.5 through Codex for consult/review/implementation, wants OpenCode specialist lanes (Kimi K2.7 Code, MiniMax M3, DeepSeek V4 Flash, MiMo), runs OpenCode as the conductor or panel because Claude is unavailable, needs a Codex fallback, mentions replacing codex-consult/opencode-consult/consult-orchestrator, wants Codex without any plugin, needs multi-model review, or needs model routing using gpt-5.5, sonnet-5, opus-4.8, fable-5, Kimi, MiniMax, DeepSeek, or MiMo. Do not use for routine one-agent edits, secret-bearing prompts, unmonitored review gates, or unrestricted autonomous writes."
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
Delegating that work to Codex (`gpt-5.5` — the primary engineering lane) and
OpenCode lanes (Kimi K2.7 Code, MiniMax M3, DeepSeek V4 Flash, MiMo v2.5 Pro)
moves the token burn onto Codex/OpenRouter quota instead, while Claude — the
conductor — spends its limited budget on what actually needs it: scoping,
verification, taste, and final judgment. When Codex itself is rate-limited,
times out, or is down, the OpenCode lanes take over (see "If Codex Cannot
Continue") so bulk work still stays off-Claude. The OpenCode lanes are
themselves cost-tiered: MiniMax M3 thinks hard on small briefs, DeepSeek V4
Flash reads huge inputs cheaply — premium API tiers are not defaults.

Use this as the canonical replacement for the old `codex-consult`,
`opencode-consult`, and `consult-orchestrator` entry points. Those skills are
now thin forwarders into this one.

## Read First

- For model choice, delegation economics, and "never Haiku" rules, read
  `references/model-routing.md`.
- To check local readiness (CLIs, auth, lanes) without changing anything, run
  `scripts/orchestra-doctor.sh`.

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
  cross-checks with `--lane reasoning`, `--lane context`, or `gpt-5.5` via
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

## Delegation Economics

One Bash call to a wrapper costs the conductor a few hundred tokens; the
consultant's reading, reasoning, and output are billed to Codex or OpenRouter,
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

Use `scripts/codex-agent.sh` as the single Codex entry point:

```text
scripts/codex-agent.sh consult --cd <repo> -- "<brief>"
scripts/codex-agent.sh review --uncommitted
scripts/codex-agent.sh review --base main --prompt "<focus>"
scripts/codex-agent.sh implement --allow-write --cd <repo> --scope <path> -- "<task>"
```

Modes:

- `consult`: read-only `codex exec`; use for investigation, data analysis,
  second opinions, and design critique. MCP off by default; reasoning effort
  floored to high; works on non-git directories.
- `review`: native `codex review`; defaults to `--uncommitted`; accepts `--cd`.
- `implement`: guarded `codex exec --sandbox workspace-write`; requires
  `--allow-write`, requires a git repo, refuses `main`/`master` unless
  `--allow-main` is explicit, disables MCP, and instructs Codex not to commit
  or push.

All modes are time-bounded (consult 900s, review 1800s, implement 3600s;
override with `--timeout N` or `CODEX_AGENT_TIMEOUT`, 0 disables) so a stalled
call can never hang the conductor.

Only use `implement` when the user clearly wants Codex to make changes. Prefer
a working branch or isolated worktree. The wrapper never uses
`danger-full-access` or `--dangerously-bypass-approvals-and-sandbox`.

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

- `code` → `openrouter/moonshotai/kimi-k2.7-code`
- `reasoning` → `openrouter/minimax/minimax-m3` — the thinking lane: defaults
  to OpenRouter reasoning effort `high` (`--reasoning low|medium|high` to
  tune). Give it a longer timeout on big briefs; high effort thinks before it
  answers.
- `context` → `openrouter/deepseek/deepseek-v4-flash` — the cheap ~1M-context
  workhorse for input-heavy sweeps (big logs, long diffs, whole-repo reads).
  Chosen for speed and volume, not depth; no reasoning-effort default.
- `prose` → `openrouter/xiaomi/mimo-v2.5-pro`

Use `--sealed` when all context is inline. Run OpenCode lanes sequentially —
they share one local SQLite state and concurrent runs can fail with
"database is locked".

### If Codex Cannot Continue

`gpt-5.5` via Codex is the main implementor and investigator. Only when Codex
fails — rate-limit/usage errors, auth errors, outage, or repeated timeouts —
step down to OpenCode instead of pulling the work back into Claude, and pick
the lane by task shape:

1. `consult` → hard thinking on a bounded brief: `--lane reasoning` (MiniMax
   M3, high effort). Input-heavy sweep of logs/diffs/repo: `--lane context`
   (DeepSeek V4 Flash — cheap at volume). Config/correctness checks:
   `--lane code` (Kimi). Non-sealed lets the model read the repo itself.
2. `review` → generate the diff locally (`git diff`), send it sealed to
   `--lane code`; `--lane reasoning` for architecture-level review;
   `--lane context` for very large diffs.
3. `implement` → `scripts/opencode-implement.sh --allow-write --cd <repo>
   --scope <path> -- "<task>"`. Guarded like Codex implement (git repo
   required, refuses main/master, secret guard, bounded timeout), but the
   agent gets file read/search/edit tools only — no shell — so it structurally
   cannot commit, push, or run commands. Defaults to Kimi K2.7 Code;
   `--lane reasoning` for hard tasks, `--lane context` for long-context bulk
   edits. The conductor reviews the printed working-tree changes, runs tests,
   and owns git.
4. Only when OpenCode is also down does the conductor do bulk work in Claude —
   and it should tell the user, who may prefer to wait.

Return to Codex when it recovers; it stays the default engineering lane.

## Model Defaults

When the user does not specify a model, apply their defaults:

- Bulk/mechanical implementation, migrations, data analysis, repo
  investigation, and hard debugging: `gpt-5.5` through Codex CLI defaults.
- Technical second opinions and security framing: `--lane code` (Kimi K2.7
  Code). Deep reasoning, architecture/plan critique: `--lane reasoning`
  (MiniMax M3, high reasoning). Huge-context sweeps and bulk summarization:
  `--lane context` (DeepSeek V4 Flash). Prose and docs polish: `--lane prose`
  (MiMo v2.5 Pro).
- User-facing UI, copy, API design, and product polish: require taste >= 7;
  use `fable-5` when available, otherwise `sonnet-5` or another taste-suitable
  lane.
- Plan and implementation reviews: `fable-5` or `opus-4.8`, optionally plus a
  separate `gpt-5.5` Codex review.
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
2. Preflight the brief for secrets and secret-bearing file paths.
3. Choose the minimum useful lanes: Codex for implementation/diff/correctness,
   OpenCode lanes for provider diversity, technical checks, reasoning, or prose.
4. Invoke each lane through `scripts/codex-agent.sh` or
   `scripts/consult-opencode.sh` directly with Bash.
5. Build a claim ledger with source, evidence checked, and status:
   `verified`, `weak`, or `rejected`.
6. Synthesize the decision. Report verified findings first, then unresolved
   disagreements or weak claims. The conductor performs any edits and tests.

## Compatibility

Legacy prompts may still mention `codex-consult`, `opencode-consult`, or
`consult-orchestrator`. Treat those as aliases for this skill. Their bundled
scripts now forward to the canonical wrappers here, so existing project and
study panels keep working with a single underlying implementation.

## Done Checklist

- [ ] Delegated input/output-heavy work off-Claude instead of running it in
      Claude or a Claude subagent.
- [ ] Used `scripts/codex-agent.sh` or `scripts/consult-opencode.sh` directly.
- [ ] Used OpenCode only with an explicit `--lane` or `--model`.
- [ ] Sent no secrets or secret-bearing paths.
- [ ] Kept review/gate loops manual and monitored.
- [ ] Verified consultant claims before acting.
- [ ] For implementation, used `--allow-write`, scoped paths, and a non-main
      branch/worktree unless explicitly overridden.
- [ ] The conductor owned final judgment, tests, git, and review.
