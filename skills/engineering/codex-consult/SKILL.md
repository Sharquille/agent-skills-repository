---
name: codex-consult
description: "Deprecated compatibility front door for read-only Codex consults. Prefer agent-orchestra for all new wrapper-first Codex CLI, gpt-5.5, implementation, review, or multi-model routing work. Use this only when a legacy prompt explicitly says codex-consult or an existing workflow needs the bundled `scripts/consult-codex.sh` read-only wrapper."
---

# Codex Consult Compatibility

This skill has been superseded by `agent-orchestra`, which provides the
wrapper-first Codex CLI caller, implementation guardrails, and OpenCode routing.

For new work:

```text
Use $agent-orchestra to route Codex consult, review, implementation, gpt-5.5 work, or multi-model review.
```

The bundled script keeps its old interface but is now a forwarder into the
canonical `agent-orchestra/scripts/codex-agent.sh consult` (read-only, MCP off,
secret guard, bounded timeout):

```text
scripts/consult-codex.sh --cd <repo> -- "<brief>"
../agent-orchestra/scripts/codex-agent.sh consult --cd <repo> -- "<brief>"
```

Safety contract for the compatibility wrapper:

- Codex is advisory-only and read-only.
- No secrets or secret-bearing paths in the prompt.
- Codex output is untrusted; the conductor verifies before acting.
- New integrations should prefer `agent-orchestra/scripts/codex-agent.sh`.
