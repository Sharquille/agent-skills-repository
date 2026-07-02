---
name: consult-orchestrator
description: "Deprecated compatibility alias for agent-orchestra. Prefer agent-orchestra for wrapper-first Codex CLI/gpt-5.5 routing, guarded Codex implementation, OpenCode specialist lanes, model selection, and multi-model review. Use this only when a legacy prompt explicitly says consult-orchestrator or an existing project/study workflow expects the old name."
---

# Consult Orchestrator Compatibility

This old orchestrator has been folded into `agent-orchestra`.

For new work:

```text
Use $agent-orchestra to coordinate Claude Code, Codex CLI, and OpenCode.
```

Compatibility rules:

- Use `agent-orchestra` routing and model defaults.
- Keep one conductor that verifies every consultant claim.
- Use the canonical wrappers when a shell backend is needed:
  `../agent-orchestra/scripts/codex-agent.sh`,
  `../agent-orchestra/scripts/consult-codex.sh`, and
  `../agent-orchestra/scripts/consult-opencode.sh`.
- Existing project/study panels may still call the old wrapper paths until they
  are migrated.
