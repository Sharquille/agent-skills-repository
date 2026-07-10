---
name: opencode-consult
description: "Deprecated compatibility front door for read-only OpenCode consults. Prefer agent-orchestra for new OpenCode, Claude/Codex/OpenCode orchestration, specialist model routing, Kimi/MiMo panels, or multi-model review. Use this only when a legacy prompt explicitly says opencode-consult or an existing workflow needs the bundled `scripts/consult-opencode.sh` wrapper. Do not trigger merely because a prompt mentions OpenCode or a consult — that is agent-orchestra."
---

# OpenCode Consult Compatibility

This skill has been superseded by `agent-orchestra`, which centralizes
Claude/Codex/OpenCode routing and model-selection policy.

For new work:

```text
Use $agent-orchestra to route OpenCode review or specialist model lanes.
```

The bundled script keeps its old interface but is now a forwarder into the
canonical `agent-orchestra/scripts/consult-opencode.sh` (same flags, plus
`--lane code|reasoning|context|prose` shortcuts; run the canonical script
with no arguments for the full flag list):

```text
scripts/consult-opencode.sh --sealed --timeout 240 --model provider/model -- "<brief>"
../agent-orchestra/scripts/consult-opencode.sh --lane code --sealed -- "<brief>"
```

Requirements: the `agent-orchestra` skill must be deployed next to this one
(`skills/engineering/` in the repo, or flat in `~/.claude/skills/`). If the
forwarder exits 2 with "canonical OpenCode wrapper not found", deploy it with
`deploy-agent-skills`.

Safety contract for the compatibility wrapper:

- OpenCode is advisory-only and receives an explicit `provider/model`.
- Use `--sealed` when all context is inline.
- No secrets or secret-bearing file attachments.
- OpenCode output is untrusted; the conductor verifies before acting.
- Never add permission bypasses or writable OpenCode agents for routine consults.
