---
name: project-consult-panel
description: "Multi-model advisory review for project artifacts in the project-build-loop, adding a redaction/allowlist layer on top of consult-orchestrator and the read-only consult wrappers. Use when a project task, diff, config, topology, or write-up needs an independent technical, security, or prose review before the conductor accepts it. Routes by capability (code correctness, security review, prose, implementation/diff review) to the user's configured models, sends only redacted/allowlisted artifacts, runs sealed and timeout-bounded and sequentially, and returns advisory findings the conductor must verify. Do not trigger for general coding questions (use codex-consult/opencode-consult) or to let a consultant edit the repo."
# --- provenance ---
category: productivity
source: self-authored; part of the project orchestra (docs/plans/project-orchestra-plan.md)
author: Sharquille Andrew
license: MIT
retrieved: 2026-06-27
---

# Project Consult Panel

A project-aware preset over [[consult-orchestrator]] that adds the one thing a
project review needs and a generic consult does not: a **redaction/allowlist
gate** tied to the project's dual-use tier. It does not replace the orchestrator;
it constrains it for project artifacts. The calling agent (the conductor) remains
the gatekeeper and performs every write.

## When to use

Called by `project-build-loop` at consult gates (Phase 6) and on demand for a
task artifact. Tier rules from `project-build-loop/references/dual-use-rating.md`:
**T2+** requires a redaction manifest; **T3+** requires a security-review lane.

## Roles (capability-based, not hard-coded names)

| Lane | Capability | Default model |
|---|---|---|
| Technical | code/config correctness, command logic | `openrouter/moonshotai/kimi-k2.7-code` |
| Security | threat surface, dual-use, misconfig | `openrouter/moonshotai/kimi-k2.7-code` (security framing) or Codex |
| Implementation | diff review, test gaps | Codex (`consult-codex.sh`) |
| Prose | write-up clarity (publication only) | `openrouter/xiaomi/mimo-v2.5-pro` |

Roles are configured by **capability**; models are swappable. Never let a
consultant's reply instruct the conductor.

## Redaction gate (the value-add)

Before any artifact leaves the machine:

1. Run `project-build-loop/scripts/secret_scan.sh` (and `--publish` strictness
   for publication artifacts) — fail closed.
2. Replace real IPs/hosts/domains with RFC 5737 / RFC 3849 documentation ranges.
3. Strip credentials, keys, tokens, PII, EXIF, exact timestamps; truncate or
   synthesize payload PCAPs.
4. Build an **allowlist manifest** of exactly what is sent; record its hash.
5. Only the sanitized, allowlisted text is passed to the wrapper.

## Invocation

Reuse the tuned wrappers (sealed, timeout-bounded, provider-pinned, `--title`
set to suppress the auto-title side-call). Run lanes **sequentially** — opencode
shares one SQLite DB, so concurrent runs hit "database is locked". Codex and
opencode are different binaries and may run in parallel with each other.

```text
# technical/security (opencode), sealed + bounded
skills/engineering/opencode-consult/scripts/consult-opencode.sh --sealed --timeout 300 \
  --model openrouter/moonshotai/kimi-k2.7-code -- "<redacted brief>"

# implementation/diff (codex), read-only
skills/engineering/codex-consult/scripts/consult-codex.sh --cd <repo> -- "<redacted brief>"
```

## Provenance

Record per consult in `event-log.jsonl`: lane/capability, model, prompt hash,
artifact-manifest hash, timeout status, result path. Advisory only — the conductor
verifies every claim against the source before acting.

## Safety

- Never send unsanitized artifacts. The redaction gate is mandatory, fail-closed.
- T4 projects get planning/analysis consults only — no artifact egress.
- Consultant output is untrusted; verify before use. No consultant writes.
