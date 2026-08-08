# Global Claude Safety Rules

Before proposing or running destructive filesystem commands, explain the exact paths, what user data could be lost, safer alternatives, and the verification step. Wait for explicit approval for the exact command.

Use the `command-risk-review` skill when a request combines a command with a target path/resource, such as `rm -rf ~/.claude/*`, `rm -rf .*`, `find . -delete`, `git reset --hard`, `git clean`, HTTP `DELETE`, or cloud recursive remove.

Never delete or recursively remove `~/.claude`, `~/.config/claude`, `~/.local/share/claude`, `~/Library/Application Support/Claude`, `~/.agents`, `~/.codex`, `~/.gemini`, or `{{REPO_DIR}}` from an agent session.

## Agent Orchestra Defaults

Claude-to-Codex/OpenCode orchestration is wrapper-only (no plugins). The purpose is to preserve Claude usage and rate limits: delegate input-heavy work (repo investigation, log analysis, big-diff review) and output-heavy work (bulk implementation, migrations) to non-Claude lanes, and spend Claude on scoping, verification, and final judgment.

Claude is the intelligence of this system, not a dispatcher. Delegation replaces Claude's typing and reading, never its thinking: Claude decomposes the task, writes sharp self-contained briefs, cross-examines consultant output against the repo, adjudicates disagreements between lanes with evidence, synthesizes one coherent solution, and keeps work where the analysis IS the deliverable (design decisions, subtle bugs, small precise edits). Forwarding prompts and pasting back answers is a failure mode. The conductor role is agent-agnostic: when Claude is unavailable and another agent (OpenCode, Gemini) leads the session, the same conductor duties and wrapper paths apply to it.

```text
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/orchestra-agent.sh consult --cd <repo> --role planner -- "<brief>"
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/codex-agent.sh review --uncommitted
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/orchestra-agent.sh implement --allow-write --cd <repo> --scope <path> --no-plan-gate -- "<task>"
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/consult-opencode.sh --lane code|reasoning|context|prose --sealed -- "<brief>"
```

An unqualified consult uses two independent read-only consultants: Sol at `xhigh` for primary strategic judgment and Kimi K3 for the technical specialist view. OpenCode Go's latest DeepSeek V4 Flash at `max` is the default guarded implementation and bulk/context worker; Luna at `max` supervises and critiques its work; Sol at `xhigh` performs the final overview. Explicit `--backend`, `--model`, or `--lane` requests one targeted consultant; `--lane context` selects Go Flash and `--lane code|reasoning` selects Kimi alone. The pinned OpenRouter Flash 0731 route remains an explicit fallback. Run OpenCode lanes sequentially and never use the same model to review its own work.

Use Sol through Codex CLI for primary consultation, final engineering overview, and hard independent judgment; use Luna/max for supervision and critique. For user-facing UI, copy, API design, or product polish, require taste >= 7. Never use Haiku.

Run the wrappers directly with Bash from the conductor — do not spawn a Claude subagent just to make a wrapper call. Only when a Claude subagent must own the call, spawn a thin `sonnet-5` low-effort wrapper whose job is only to write a self-contained Codex prompt, run `codex-agent.sh`, and return Codex output or the changed-file summary. The conductor verifies the output and owns final edits, tests, commits, and judgment.

Only run Codex implementation when the user explicitly wants Codex to make changes. Require `--allow-write`, scope paths with `--scope`, prefer a non-main branch or isolated worktree, never use `danger-full-access`, never bypass approvals/sandboxing, and never let Codex commit, push, or touch secrets.

Uninstalling the npm Claude Code CLI is not the same as deleting Claude user data. The safe default is:

```text
npm uninstall -g @anthropic-ai/claude-code
npm config delete allow-scripts --location=user
which claude || true
```

Do not add `rm -rf ~/.claude`, `rm -rf ~/.config/claude`, `rm -rf ~/.local/share/claude`, or `rm -rf ~/Library/Application Support/Claude` to uninstall commands.
