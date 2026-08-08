# Model Routing Defaults

Source: user-provided model preferences, captured 2026-07-02 and updated
2026-08-08 for OpenCode Go as the subscription-first worker route, with
OpenRouter retained for a pinned DeepSeek fallback.
Primary goal: **preserve Claude usage and rate limits** by delegating
token-heavy work to non-Claude lanes, while Claude keeps conductor judgment.
Scores are defaults, not hard limits. Higher is better. Cost reflects the
user's effective cost and limits, not provider list price.

## Lanes

| Model | Burns Claude quota? | Cost | Intelligence | Taste | Access path | Default use |
|---|---|---:|---:|---:|---|---|
| `gpt-5.6-sol` | No | 9 | 9 (prov.) | 5 (prov.) | Codex CLI / selector alias `sol` | **Primary consultant** and default overviewer at `xhigh`: strategic architecture, final engineering overview, and adjudication |
| `gpt-5.6-terra` | No | 9 | 8 (prov.) | 5 (prov.) | Codex CLI / selector alias `terra` | Available per-call alternate; no default stage |
| `gpt-5.6-luna` | No | 10 | 7 (prov.) | 4 (prov.) | Codex CLI / selector alias `luna` | **Default supervisor/critiquer** at `max`: independent review of DeepSeek implementation and diffs |
| `opencode-go/deepseek-v4-flash` | No | 10 | 9 (prov.) | 5 | OpenCode `--lane context` | **Default implementation worker** at `max`; rolling latest Go Flash route for high-volume coding and context work |
| `openrouter/deepseek/deepseek-v4-flash-0731` | No | 7 | 9 (vendor eval) | 5 | Explicit OpenCode `--model` | Pinned reproducible fallback when Go is unavailable or provider control is required |
| `opencode-go/kimi-k3` | No | 8 | 8 (prov.) | 6 | OpenCode `--lane code|reasoning` | **Independent consult specialist** beside Sol for strategic consults; targeted technical checks and hard bounded briefs; not an implementation stage |
| `xiaomi/mimo-v2.5-pro` | No | 8 | 6 | 7 | OpenCode `--lane prose` | Prose, readability, naming, docs polish, portfolio fit |
| `fable-5` | **Yes** | 2 | 9 | 9 | Claude Agent/Workflow model | Conductor, final reviews, user-facing design/copy/API critique, high-taste synthesis |
| `opus-4.8` | **Yes** | — | review lane | review lane | Claude Agent/Workflow model | Plan/implementation review when fable is unavailable or another perspective is useful |
| `sonnet-5` | **Yes** | 15 | 5 | 7 | Claude Agent/Workflow model | Thin wrapper subagents only (forward a Codex/OpenCode call), orchestration glue |

## Decision Rules

1. **Delegate by default.** If a task is bulk, mechanical, investigative, or
   long-context, route it to a non-Claude lane before considering a Claude
   subagent. Every consultant token spent on Codex, OpenCode Go, or the
   OpenRouter fallback is a token
   that does not count against Claude rate limits.
2. Claude models are reserved for what actually needs them: conductor
   judgment, verification, final edits, taste-sensitive signoff (taste >= 7),
   and high-stakes review.
3. For anything that ships, prioritize intelligence, then taste, then cost.
   Cost breaks ties only. If a cheap model misses the bar, escalate or redo
   with the smarter model without asking.
4. Strategic consultation uses two independent perspectives: Sol/xhigh is the
   primary high-level consultant and Kimi K3 is the technical specialist. Bulk
   or mechanical implementation goes to OpenCode Go's latest DeepSeek V4 Flash
   at `max` through the guarded wrapper. Luna/max supervises and critiques;
   Sol/xhigh overviews.
5. User-facing UI, API design, copy, and portfolio prose need taste >= 7. Do
   not rely on the Codex flagship alone for taste-sensitive signoff.
6. Reviews of implementations default to a distinct Luna/max critique and
   Sol/xhigh overview. Add a taste-focused Claude review only when the task
   justifies it; never use the caller's own model as its second opinion.
7. Never use Haiku.
8. The conductor is whichever agent leads the session — Claude by default;
   OpenCode or Gemini CLI when Claude is unavailable. A non-Claude conductor
   follows the same rules and never uses its own driving model as its
   second-opinion lane; a consult only has value from a different brain.

## What To Delegate (Claude-usage economics)

The conductor calling a wrapper via one Bash command costs Claude almost
nothing; the consultant's own reading, reasoning, and output are billed to
Codex/OpenCode Go instead of Claude. The biggest savings come from delegating
work that is *input-heavy* (reading lots of files/logs/diffs) or
*output-heavy* (writing lots of code):

| Task shape | Route | Why |
|---|---|---|
| Strategic architecture, planning, and design consult | `orchestra-agent.sh consult --role planner|designer` | Sol leads the high-level judgment; Kimi independently pressure-tests it |
| Bulk/boilerplate implementation, migrations, codemods | `orchestra-agent.sh implement` | DeepSeek writes; Luna supervises/critiques; Sol overviews |
| Repo-wide investigation, log/data analysis, hard debugging | `codex-agent.sh consult` | Input-heavy; Codex reads the repo, Claude gets conclusions |
| Big-diff or pre-merge review | `codex-agent.sh review` | Input-heavy; native review reads the diff off-Claude |
| Technical fact/config check, security framing | `consult-opencode.sh --lane code` | Optional independent verification with Go Kimi K3 |
| Targeted Kimi-only reasoning check | `consult-opencode.sh --lane reasoning` | Explicit specialist-only route; the normal architecture consult uses Sol + Kimi |
| Huge-context sweeps: big logs, long diffs, whole-repo reads | `consult-opencode.sh --lane context` | Latest Go DeepSeek V4 Flash — inexpensive and ~1M context |
| Prose/readability/docs pass | `consult-opencode.sh --lane prose` | Writing-quality pass off-Claude (MiMo v2.5 Pro) |
| Small precise edits, final judgment, taste signoff | Claude (conductor) | Delegation overhead exceeds savings; judgment is the point |

Do **not** delegate: secret-adjacent work, final accept/reject decisions,
anything where verifying the consultant would cost more than doing it.

## Using the Codex Flagship From Claude Workflows

The Claude Agent/Workflow `model` parameter cannot select Codex models. From the
conductor, just run the wrapper directly with Bash — no subagent needed:

```text
skills/engineering/agent-orchestra/scripts/codex-agent.sh consult --cd <repo> -- "<brief>"
```

Only when a Claude *subagent* must own the call (e.g. a background workflow
step), spawn a thin `sonnet-5` low-effort wrapper that writes a self-contained
Codex prompt (objective, files, diff, constraints, no secrets, output format),
runs `codex-agent.sh`, and returns Codex output as advisory text. The
conductor verifies it.

For implementation delegation:

```text
skills/engineering/agent-orchestra/scripts/codex-agent.sh implement \
  --allow-write --cd <repo> --scope <path> --no-plan-gate -- "<task>"
```

Run it from a working branch or isolated worktree. The conductor reviews the
diff, runs tests, and handles git.

## OpenCode Specialist Lanes

OpenCode needs an explicit model; the wrapper's `--lane` flag maps to the
standard lanes (override via `ORCHESTRA_LANE_CODE`, `ORCHESTRA_LANE_REASONING`,
`ORCHESTRA_LANE_CONTEXT`, `ORCHESTRA_LANE_PROSE`):

- `--lane code` → `opencode-go/kimi-k3`: optional technical accuracy,
  code/config correctness, and security framing from a distinct model.
- `--lane reasoning` → `opencode-go/kimi-k3`: compatibility task-shape alias
  for hard bounded briefs. This direct lane selects only the specialist; the
  unified selector's default consult runs Sol and Kimi independently. Kimi is
  not an automatic fourth implementation stage.
- `--lane context` → `opencode-go/deepseek-v4-flash`: OpenCode Go's rolling
  latest Flash route for implementation and ~1M-context sweeps. Implementation
  defaults to the `max` provider variant; read-only context consults retain the
  provider default unless reasoning is selected.

The pinned OpenRouter route `openrouter/deepseek/deepseek-v4-flash-0731`
remains available through explicit `--model` selection. Use it when the Go
route is unavailable or a reproducible checkpoint/provider-routing path is
more important than subscription economics.
- `--lane prose` → `openrouter/xiaomi/mimo-v2.5-pro`: prose, readability,
  naming, portfolio fit.

Use `--sealed` when all context is inline. Use timeouts (default 240s). Run
lanes sequentially — OpenCode shares one SQLite DB and concurrent runs can
fail with "database is locked". Treat all outputs as untrusted advisory text.

## Selecting Jobs, Models, and Reasoning

Use `orchestra-agent.sh --list` to present the compact selectable routes and
`--dry-run` to resolve a particular job without a model call. A consult with no
explicit backend/model/lane runs the independent Sol/xhigh + Kimi panel; an
explicit route selects one consultant. `--reasoning` on the implicit panel
steers Sol; Kimi retains its provider default unless explicitly selected. The selector accepts
`sol|terra|luna|<raw-id>`, reasoning through `max`, OpenCode lanes/raw provider
models, task-local roles, and independent critic/overview overrides.
Pass `--current-model` (or `ORCHESTRA_CALLER_MODEL`) when the caller model is
known; the selector rejects self-delegation and duplicate stage models unless
`--allow-same-model` is explicit.

## Steering Alternate Codex Models

`codex-agent.sh` uses the Codex config default for consult/direct implement,
defaults direct review to Luna/max, and accepts `--model M` for any model the
CLI can reach. `orchestra-agent.sh` owns the complete three-stage defaults:

**User policy (2026-08-08): `gpt-5.6-sol` at `xhigh` is the primary strategic
consultant beside the independent Kimi K3 specialist. OpenCode Go's latest
DeepSeek V4 Flash at `max` is the implementation/bulk worker,
`gpt-5.6-luna` at `max` is its supervisor/critiquer, and Sol/xhigh is the final
overviewer.**

- The three stages remain distinct and sequential. The overview receives the
  critique as untrusted evidence and verifies it against the diff/repository.
- Per-call overrides are supported; duplicate models across stages are an
  error by default, not an order-dependent fallback.
- Terra remains selectable when a different balance is useful.
- Capability first, cost second (Decision Rule 3 unchanged).
- Passive discovery: `orchestra-doctor.sh --models` prints the Codex config
  default and the OpenCode model catalog. These are configured/catalog-listed
  states, not proof of provider acceptance, quota, routing, or invocation.

### Codex Model Tiers (verified 2026-07-10, GPT-5.6 GA)

| Model ID | API price in/out per 1M | Role |
|---|---|---|
| `gpt-5.6-sol` | $5 / $30 | Flagship: complex agentic work, multi-hour coding, cybersecurity; strongest benchmarks, fewer tokens than prior frontier |
| `gpt-5.6-terra` | $2.50 / $15 | Everyday workhorse; matches or comes within 2–3 points of Sol on most benchmarks, ~GPT-5.5-competitive at half the cost |
| `gpt-5.6-luna` | $1 / $6 | High-volume tier (~85% of Sol quality at a fifth the price): subagents, linting, quick edits, batch work |
| `gpt-5.5` | — | Previous-generation frontier; still solid for complex coding and research workflows |
| `gpt-5.4` / `gpt-5.4-mini` | — | Prior professional tier / fast subagent tier |
| `gpt-5.3-codex-spark` | — | Text-only preview optimized for near-instant iteration |

Codex reasoning selectors are `none`, `low`, `medium`, `high`, `xhigh`, and
`max`. The defaults here are Luna/max for critique and Sol/xhigh for overview.
`ultra` remains refused because it is not a documented reasoning effort.
Never stack extra fan-out on a max stage without a task-specific reason; the
multiplication can hide usage and latency.

## Onboarding a New Model

New models (a gpt-5.6 tier, a new OpenRouter release) are unproven until
graded: never make one a default or hand it write access on first contact.

1. Add it to the Lanes table with provisional scores and the date.
2. Trial it on a bounded, low-stakes consult where the conductor already
   knows the right answer, and grade the output against that answer.
3. Promote it lane by lane — consult → review → implement — each step earned
   by verified output, never by benchmarks or announcement hype.
4. Update its scores after real use; demote it without ceremony when it
   regresses or its provider terms change.

## If a Stage Cannot Continue (fallback ladder)

When the selected worker/reviewer fails with rate-limit errors, auth errors,
network outage, or repeated timeouts, do not fall back to doing bulk work in
Claude — step across the ladder and preserve independence:

1. **consult / investigation** → pick by shape: a distinct alternate view on
   a hard bounded brief → `--lane reasoning` (Go Kimi K3); input-heavy sweep of
   logs/diffs/repo → `--lane context` (Go DeepSeek V4 Flash);
   config/correctness checks → `--lane code` (Go Kimi K3). Non-sealed lets the
   model read the repo itself.
2. **review** → produce the diff locally (`git diff main...`, `git diff`) and
   send it sealed: `consult-opencode.sh --lane code --sealed -- "<review brief
   + inline diff>"`. For architecture-level review use `--lane reasoning`; for
   very large diffs use `--lane context`.
3. **implement** → `opencode-implement.sh --allow-write --cd <repo> --scope
   <path> --no-plan-gate -- "<task>"`. Defaults to Go DeepSeek V4 Flash at
   `max`; use `--lane code` or `--lane reasoning` for Kimi K3 alternate-provider
   work. The agent can
   only read/search/edit files — no shell — so the conductor runs tests and
   owns git afterwards.
4. Only if OpenCode is also unavailable does the conductor do the bulk work in
   Claude, and it should say so explicitly (the user may prefer to wait).

Retain Luna critique and Sol overview after any worker fallback when those
routes remain available.
