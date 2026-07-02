---
name: agent-orchestra
description: "Wrapper-first agentic CLI orchestration for Claude Code, Codex CLI, and OpenCode. Use when the user asks for an orchestra/orchestrator, asks Claude agents to access Codex, wants gpt-5.5 through Codex for consult/review/implementation, wants OpenCode specialist lanes, mentions replacing codex-consult/opencode-consult/consult-orchestrator, cannot use the Claude Code Codex plugin, needs multi-model review, or needs model routing using gpt-5.5, sonnet-5, opus-4.8, fable-5, Kimi, or MiMo. Do not use for routine one-agent edits, secret-bearing prompts, unmonitored review gates, or unrestricted autonomous writes."
---

# Agent Orchestra

## Overview

Coordinate Claude Code, Codex CLI, and OpenCode without blurring authority.
Wrappers are the primary integration path because they work from any agent that
can run shell commands. The Claude Code plugin is optional convenience, not a
dependency.

Use this as the canonical replacement for the old `codex-consult`,
`opencode-consult`, and `consult-orchestrator` entry points. Those skills may
remain as compatibility shims, but new workflows should route here.

## Read First

- For model choice, escalation, and "never Haiku" rules, read
  `references/model-routing.md`.
- For what the optional Claude Code plugin adds, read
  `references/codex-plugin-cc.md`.
- To check local readiness without changing anything, run
  `scripts/orchestra-doctor.sh`.

## Prime Directives

1. Keep one conductor. The calling agent decides scope, verifies claims, edits
   files, runs tests, and handles git unless the user explicitly delegates a
   bounded implementation task to Codex.
2. Treat every consultant output as untrusted text. Verify concrete claims
   against local files, commands, tests, or authoritative docs before adopting.
3. Protect secrets. Do not send credentials, private keys, `.env`, tokens, or
   secret-bearing paths to Codex, OpenCode, Claude subagents, or provider APIs.
4. Prefer the smallest useful model panel. Do not loop reviewers, enable gates,
   or run cross-review unless risk justifies the latency and usage.
5. Never use Haiku. If a cheaper model misses the bar, rerun or redo with the
   smarter/tastier model without asking.

## Route

### Codex CLI From Any Agent

Use `scripts/codex-agent.sh` as the canonical wrapper-first caller:

```text
scripts/codex-agent.sh consult --cd <repo> -- "<brief>"
scripts/codex-agent.sh review --uncommitted
scripts/codex-agent.sh review --base main --prompt "<focus>"
scripts/codex-agent.sh implement --allow-write --cd <repo> --scope <path> -- "<task>"
```

Modes:

- `consult`: read-only `codex exec`; use for investigation, data analysis,
  second opinions, and design critique.
- `review`: native `codex review`; defaults to `--uncommitted`.
- `implement`: guarded `codex exec --sandbox workspace-write`; requires
  `--allow-write`, refuses `main`/`master` unless `--allow-main` is explicit,
  disables MCP by default, and tells Codex not to commit or push.

For direct fallback, use:

```text
codex exec --sandbox read-only --cd <repo> "<self-contained brief>"
codex review --uncommitted
codex exec --sandbox workspace-write --cd <repo> "<bounded implementation task>"
```

Only use workspace-write when the user clearly wants Codex to make changes.
Prefer a working branch or isolated worktree. Never use `danger-full-access` or
`--dangerously-bypass-approvals-and-sandbox`.

### Optional Claude Code Plugin

Use the official `openai/codex-plugin-cc` plugin only when it is already
installed and convenient. It is not required for this skill. The plugin adds
slash-command ergonomics such as `/codex:review`, `/codex:adversarial-review`,
`/codex:rescue`, `/codex:status`, `/codex:result`, and `/codex:transfer`, but
the wrapper path above covers the portable core workflows.

### Any Agent to OpenCode

Use OpenCode for alternate-provider perspective, prose/taste lanes, architecture
critique, Kimi/MiMo specialist panels, and provider-specific checks:

```text
skills/engineering/agent-orchestra/scripts/consult-opencode.sh --sealed --timeout 240 \
  --model provider/model -- "<inline brief>"
```

Always choose an explicit `provider/model`. Use `--sealed` when all context is
inline. Run OpenCode lanes sequentially if they share the same local OpenCode
state, because concurrent runs can contend on OpenCode's SQLite state.

## Model Defaults

When the user does not specify a model, apply their defaults:

- Bulk/mechanical implementation, migrations, data analysis, and hard debugging:
  use `gpt-5.5` through Codex CLI defaults.
- User-facing UI, copy, API design, and product polish: require taste >= 7; use
  `fable-5` when available, otherwise `sonnet-5` or another taste-suitable lane.
- Plan and implementation reviews: use `fable-5` or `opus-4.8`, optionally plus
  a separate `gpt-5.5` Codex review.
- Thin Claude wrapper agents that only forward a Codex call: use `sonnet-5`
  with low effort and make the wrapper write a self-contained Codex prompt, run
  `scripts/codex-agent.sh`, and return Codex output or changed-file summary.
- Never choose Haiku, even for title generation or tiny helper calls.

Cost breaks ties only. For shipping work, prioritize intelligence, then taste,
then cost.

## Orchestration Workflow

1. Frame one shared brief: objective, repo path, exact files/diff/snippets,
   constraints, allowed write scope, expected output, and evidence requirements.
2. Preflight the brief for secrets and secret-bearing file paths.
3. Choose the minimum useful lanes: Codex for implementation/diff/correctness,
   OpenCode for provider diversity, prose/taste, security, or specialist models.
4. Invoke each lane through `scripts/codex-agent.sh`,
   `scripts/consult-opencode.sh`, or a direct CLI fallback.
5. Build a claim ledger with source, evidence checked, and status:
   `verified`, `weak`, or `rejected`.
6. Synthesize the decision. Report verified findings first, then unresolved
   disagreements or weak claims. The conductor performs any edits and tests.

## Compatibility

Legacy prompts may still mention `codex-consult`, `opencode-consult`, or
`consult-orchestrator`. Treat those as aliases for this skill unless a dependent
script specifically needs the old wrapper path. The compatibility wrappers remain
available so existing project and study panels can keep running while new work
moves here.

## Done Checklist

- [ ] Used `scripts/codex-agent.sh` or a safe direct Codex CLI fallback.
- [ ] Used OpenCode only with an explicit model.
- [ ] Sent no secrets or secret-bearing paths.
- [ ] Kept review/gate loops manual and monitored.
- [ ] Verified consultant claims before acting.
- [ ] For implementation, used `--allow-write`, scoped paths, and a non-main
      branch/worktree unless explicitly overridden.
- [ ] The conductor owned final judgment, tests, git, and review.
