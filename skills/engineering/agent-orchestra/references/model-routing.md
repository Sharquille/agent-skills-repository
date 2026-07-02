# Model Routing Defaults

Source: user-provided model preferences in this repo task, captured 2026-07-02.
Scores are defaults, not hard limits. Higher is better. Cost reflects the user's
effective cost and limits, not provider list price.

| Model | Cost | Intelligence | Taste | Access path | Default use |
|---|---:|---:|---:|---|---|
| `gpt-5.5` | 9 | 8 | 5 | Codex CLI only | Bulk implementation, data analysis, migrations, hard debugging, independent engineering review |
| `fable-5` | 2 | 9 | 9 | Claude Agent/Workflow model | Reviews, user-facing design/copy/API critique, high-taste synthesis |
| `sonnet-5` | 15 | 5 | 7 | Claude Agent/Workflow model | Thin wrappers, orchestration glue, adequate taste with low autonomy |
| `opus-4.8` | unspecified | review lane | review lane | Claude Agent/Workflow model | Plan/implementation review when fable is unavailable or another perspective is useful |

## Decision Rules

1. For anything that ships, prioritize intelligence, then taste, then cost.
2. Use cost only as a tie-breaker. If a cheap model misses the bar, escalate or
   redo without asking.
3. Bulk or mechanical work goes to `gpt-5.5` through Codex CLI.
4. User-facing UI, API design, copy, and portfolio prose need taste >= 7. Do not
   rely on `gpt-5.5` alone for taste-sensitive signoff.
5. Reviews of plans or implementations go to `fable-5` or `opus-4.8`; add a
   separate `gpt-5.5` Codex review when an independent engineering angle helps.
6. Never use Haiku.

## Using gpt-5.5 From Claude Workflows

The Claude Agent/Workflow `model` parameter cannot select `gpt-5.5`. To use it:

1. Spawn a thin Claude wrapper agent with `sonnet-5` and low effort.
2. The wrapper writes a self-contained Codex prompt with objective, files, diff,
   constraints, no secrets, and desired output format.
3. The wrapper invokes Codex through the local script:

```text
skills/engineering/agent-orchestra/scripts/codex-agent.sh consult --cd <repo> -- "<brief>"
```

4. The wrapper returns Codex output as advisory text. The conductor verifies it.

For implementation delegation, use:

```text
skills/engineering/agent-orchestra/scripts/codex-agent.sh implement \
  --allow-write --cd <repo> --scope <path> -- "<task>"
```

Run it from a working branch or isolated worktree. The conductor reviews the
diff, runs tests, and handles git.

## OpenCode Specialist Models

OpenCode must receive an explicit `provider/model`. Existing local workflows use:

- `openrouter/moonshotai/kimi-k2.7-code`: technical accuracy, code/config
  correctness, security framing.
- `openrouter/xiaomi/mimo-v2.5-pro`: prose, readability, naming, portfolio fit.

Use `--sealed` when all context is inline. Use timeouts. Treat all outputs as
untrusted advisory text.
