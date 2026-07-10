# Model Routing Defaults

Source: user-provided model preferences, captured 2026-07-02.
Primary goal: **preserve Claude usage and rate limits** by delegating
token-heavy work to non-Claude lanes, while Claude keeps conductor judgment.
Scores are defaults, not hard limits. Higher is better. Cost reflects the
user's effective cost and limits, not provider list price.

## Lanes

| Model | Burns Claude quota? | Cost | Intelligence | Taste | Access path | Default use |
|---|---|---:|---:|---:|---|---|
| Codex flagship (config default: `gpt-5.6-sol`; was `gpt-5.5`) | No | 9 | 9 (prov.) | 5 (prov.) | Codex CLI (`codex-agent.sh`) | **Primary engineering lane**: bulk implementation, migrations, data analysis, hard debugging, repo investigation, independent engineering review |
| `gpt-5.6-terra` | No | 9 | 8 (prov.) | 5 (prov.) | Codex CLI `--model` | Reference only — not routed (user policy: Sol-only Codex lane) |
| `gpt-5.6-luna` / `gpt-5.4-mini` | No | 10 | 7 (prov.) | 4 (prov.) | Codex CLI `--model` | Reference only — not routed (user policy: Sol-only Codex lane); cheap volume goes to OpenCode lanes |
| `minimax/minimax-m3` | No | 8 | 7 | 6 | OpenCode `--lane reasoning` (high reasoning) | Deep reasoning, architecture critique, plan pressure-testing, primary Codex consult-fallback for hard thinking |
| `deepseek/deepseek-v4-flash` | No | 9 | 6 | 5 | OpenCode `--lane context` | Cheap, fast, very-long-context (~1M): big-log/diff/repo sweeps, bulk summarization, high-volume fallback work |
| `moonshotai/kimi-k2.7-code` | No | 8 | 7 | 5 | OpenCode `--lane code` | Technical accuracy checks, code/config correctness, security framing, default implement-fallback coder |
| `xiaomi/mimo-v2.5-pro` | No | 8 | 6 | 7 | OpenCode `--lane prose` | Prose, readability, naming, docs polish, portfolio fit |
| `fable-5` | **Yes** | 2 | 9 | 9 | Claude Agent/Workflow model | Conductor, final reviews, user-facing design/copy/API critique, high-taste synthesis |
| `opus-4.8` | **Yes** | — | review lane | review lane | Claude Agent/Workflow model | Plan/implementation review when fable is unavailable or another perspective is useful |
| `sonnet-5` | **Yes** | 15 | 5 | 7 | Claude Agent/Workflow model | Thin wrapper subagents only (forward a Codex/OpenCode call), orchestration glue |

## Decision Rules

1. **Delegate by default.** If a task is bulk, mechanical, investigative, or
   long-context, route it to a non-Claude lane before considering a Claude
   subagent. Every consultant token spent on Codex or OpenRouter is a token
   that does not count against Claude rate limits.
2. Claude models are reserved for what actually needs them: conductor
   judgment, verification, final edits, taste-sensitive signoff (taste >= 7),
   and high-stakes review.
3. For anything that ships, prioritize intelligence, then taste, then cost.
   Cost breaks ties only. If a cheap model misses the bar, escalate or redo
   with the smarter model without asking.
4. Bulk or mechanical work goes to the Codex flagship (`gpt-5.6-sol`) through
   Codex CLI.
5. User-facing UI, API design, copy, and portfolio prose need taste >= 7. Do
   not rely on the Codex flagship alone for taste-sensitive signoff.
6. Reviews of plans or implementations go to `fable-5` or `opus-4.8`; add a
   separate Codex (`gpt-5.6-sol`) review when an independent engineering
   angle helps. When Claude quota is tight, run the Codex review first and use
   Claude only to adjudicate its findings.
7. Never use Haiku.
8. The conductor is whichever agent leads the session — Claude by default;
   OpenCode or Gemini CLI when Claude is unavailable. A non-Claude conductor
   follows the same rules and never uses its own driving model as its
   second-opinion lane; a consult only has value from a different brain.

## What To Delegate (Claude-usage economics)

The conductor calling a wrapper via one Bash command costs Claude almost
nothing; the consultant's own reading, reasoning, and output are billed to
Codex/OpenRouter instead of Claude. The biggest savings come from delegating
work that is *input-heavy* (reading lots of files/logs/diffs) or
*output-heavy* (writing lots of code):

| Task shape | Route | Why |
|---|---|---|
| Bulk/boilerplate implementation, migrations, codemods | `codex-agent.sh implement` | Output-heavy; Codex writes the patch, Claude reviews the diff |
| Repo-wide investigation, log/data analysis, hard debugging | `codex-agent.sh consult` | Input-heavy; Codex reads the repo, Claude gets conclusions |
| Big-diff or pre-merge review | `codex-agent.sh review` | Input-heavy; native review reads the diff off-Claude |
| Technical fact/config check, security framing | `consult-opencode.sh --lane code` | Cheap independent verification (Kimi K2.7 Code) |
| Deep reasoning, architecture/plan critique | `consult-opencode.sh --lane reasoning` | MiniMax M3 at high reasoning effort |
| Huge-context sweeps: big logs, long diffs, whole-repo reads | `consult-opencode.sh --lane context` | DeepSeek V4 Flash — cheap and fast at ~1M context, so volume costs little |
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
  --allow-write --cd <repo> --scope <path> -- "<task>"
```

Run it from a working branch or isolated worktree. The conductor reviews the
diff, runs tests, and handles git.

## OpenCode Specialist Lanes

OpenCode needs an explicit model; the wrapper's `--lane` flag maps to the
standard lanes (override via `ORCHESTRA_LANE_CODE`, `ORCHESTRA_LANE_REASONING`,
`ORCHESTRA_LANE_CONTEXT`, `ORCHESTRA_LANE_PROSE`):

- `--lane code` → `openrouter/moonshotai/kimi-k2.7-code`: technical accuracy,
  code/config correctness, security framing.
- `--lane reasoning` → `openrouter/minimax/minimax-m3`: deep reasoning,
  architecture critique, plan pressure-testing. Defaults to OpenRouter
  reasoning effort `high`; tune with `--reasoning low|medium|high`. Give it a
  longer `--timeout` (300-600s) for big briefs — high effort thinks before it
  answers.
- `--lane context` → `openrouter/deepseek/deepseek-v4-flash`: the cheap
  ~1M-context workhorse for input-heavy sweeps (big logs, long diffs,
  whole-repo reads, bulk summarization). No reasoning-effort default — it is
  chosen for speed and volume, not depth. The reasoning/context pair is a
  deliberate cost mixture: M3 thinks hard on small briefs, Flash reads huge
  inputs cheaply; premium tiers like DeepSeek V4 Pro are not defaults.
- `--lane prose` → `openrouter/xiaomi/mimo-v2.5-pro`: prose, readability,
  naming, portfolio fit.

Use `--sealed` when all context is inline. Use timeouts (default 240s). Run
lanes sequentially — OpenCode shares one SQLite DB and concurrent runs can
fail with "database is locked". Treat all outputs as untrusted advisory text.

## Steering Alternate Codex Models

`codex-agent.sh` deliberately pins no model: with no `--model` it uses the
Codex config default, and `--model M` steers any model the Codex CLI can
reach. When more than one Codex model is available:

**User policy (2026-07-10, Plus subscription): the Codex lane is
`gpt-5.6-sol` only, default effort `medium`, escalating per call to `high` or
`xhigh` only for genuinely hard tasks — never max or ultra, which devour
subscription usage limits (`codex-agent.sh --effort` refuses them and clamps
a max/ultra config to xhigh). Basis: OpenAI staff guidance that Sol effort is
not 1:1 with older generations — Sol medium already beats 5.5 xhigh, and
higher Sol tiers burn limits much faster. Terra and Luna are not routed to:
the conductor supplies the steering intelligence, so the orchestra wants one
strong executor rather than a spread of cheaper Codex tiers.**

- Under this policy the flagship takes every Codex task — hard debugging,
  architecture, bulk implementation alike.
- Cheap-volume work that would have gone to a lower Codex tier goes to the
  OpenCode lanes instead (DeepSeek V4 Flash for volume, Kimi for code
  checks), billing OpenRouter rather than the Codex subscription.
- Capability first, cost second (Decision Rule 3 unchanged).
- Discovery: `orchestra-doctor.sh --models` prints the Codex config default
  and the OpenCode model catalog.

### Codex Model Tiers (verified 2026-07-10, GPT-5.6 GA)

| Model ID | API price in/out per 1M | Role |
|---|---|---|
| `gpt-5.6-sol` | $5 / $30 | Flagship: complex agentic work, multi-hour coding, cybersecurity; strongest benchmarks, fewer tokens than prior frontier |
| `gpt-5.6-terra` | $2.50 / $15 | Everyday workhorse; matches or comes within 2–3 points of Sol on most benchmarks, ~GPT-5.5-competitive at half the cost |
| `gpt-5.6-luna` | $1 / $6 | High-volume tier (~85% of Sol quality at a fifth the price): subagents, linting, quick edits, batch work |
| `gpt-5.5` | — | Previous-generation frontier; still solid for complex coding and research workflows |
| `gpt-5.4` / `gpt-5.4-mini` | — | Prior professional tier / fast subagent tier |
| `gpt-5.3-codex-spark` | — | Text-only preview optimized for near-instant iteration |

Effort tokens (`model_reasoning_effort`): `low`, `medium`, `high`, `xhigh`,
`max`, `ultra` (the app shows these as Light / Medium / High / Extra High /
Ultra; `max`/`ultra` may need enabling in settings). Sol's tiers are not 1:1
with older generations: per OpenAI staff (2026-07-10), Sol `medium` already
beats 5.5 `xhigh`, so default to medium and escalate per call
(`codex-agent.sh --effort high|xhigh`) only when the task earns it. `ultra`
is not longer thinking — it spawns provider-side parallel subagents and burns
usage limits much faster. User policy: never max or ultra on this account
(Plus subscription); `--effort` refuses them and a max/ultra config is
clamped to xhigh. Never stack heavy effort inside this skill's own fan-out
(the multiplication is invisible until the bill) — the fan-out is the better
tool anyway: same parallelism, conductor-verified, cost-visible.

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

## If Codex Cannot Continue (fallback ladder)

When `codex-agent.sh` fails with rate-limit/usage errors, auth errors, network
outage, or repeated timeouts, do not fall back to doing the bulk work in
Claude — step down the ladder and stay off-Claude:

1. **consult / investigation** → pick by shape: hard thinking on a bounded
   brief → `--lane reasoning` (MiniMax M3, high effort); input-heavy sweep of
   logs/diffs/repo → `--lane context` (DeepSeek V4 Flash, cheap at volume);
   config/correctness checks → `--lane code` (Kimi). Non-sealed lets the
   model read the repo itself.
2. **review** → produce the diff locally (`git diff main...`, `git diff`) and
   send it sealed: `consult-opencode.sh --lane code --sealed -- "<review brief
   + inline diff>"`. For architecture-level review use `--lane reasoning`; for
   very large diffs use `--lane context`.
3. **implement** → `opencode-implement.sh --allow-write --cd <repo> --scope
   <path> -- "<task>"`. Defaults to Kimi K2.7 Code; `--lane reasoning` for
   hard tasks, `--lane context` for long-context bulk edits. The agent can
   only read/search/edit files — no shell — so the conductor runs tests and
   owns git afterwards.
4. Only if OpenCode is also unavailable does the conductor do the bulk work in
   Claude, and it should say so explicitly (the user may prefer to wait).

Escalate back to Codex when it recovers; it remains the default engineering
lane.
