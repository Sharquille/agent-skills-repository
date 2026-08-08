# Native Codex Subagents

Agent Orchestra calls its Luna critic and Sol overview stages explicitly, so
the guarded pipeline does not depend on Codex's native subagent defaults.
Native Codex sessions can still use Luna/max automatically for any subagents
they spawn by adding this user preference to `~/.codex/config.toml`:

```text
[agents]
enabled = true
max_concurrent_threads_per_session = 100
default_subagent_model = "gpt-5.6-luna"
default_subagent_reasoning_effort = "max"
```

The concurrency value is a ceiling, not a target. Agent Orchestra continues to
use the smallest useful panel and never launches duplicate/self-review stages.
New Codex CLI or desktop sessions must reload the config; an already-running
session may retain its previous model allowlist. Runtime availability still
wins over configuration, so a client can reject Luna even when the preference
is valid. In that case, the direct `codex-agent.sh --model gpt-5.6-luna`
critique route remains separate and should report its own invocation failure.

Use `scripts/orchestra-doctor.sh --models` to inspect the configured native
subagent defaults passively. The doctor never spends model quota and therefore
cannot prove that a subagent invocation will succeed.
