# Global Claude Safety Rules

Before proposing or running destructive filesystem commands, explain the exact paths, what user data could be lost, safer alternatives, and the verification step. Wait for explicit approval for the exact command.

Use the `command-risk-review` skill when a request combines a command with a target path/resource, such as `rm -rf ~/.claude/*`, `rm -rf .*`, `find . -delete`, `git reset --hard`, `git clean`, HTTP `DELETE`, or cloud recursive remove.

Never delete or recursively remove `~/.claude`, `~/.config/claude`, `~/.local/share/claude`, `~/Library/Application Support/Claude`, `~/.agents`, `~/.codex`, `~/.gemini`, or `{{REPO_DIR}}` from an agent session.

## Agent Orchestra Defaults

Claude-to-Codex/OpenCode orchestration is wrapper-only (no plugins). The purpose is to preserve Claude usage and rate limits: delegate input-heavy work (repo investigation, log analysis, big-diff review) and output-heavy work (bulk implementation, migrations) to non-Claude lanes, and spend Claude on scoping, verification, and final judgment.

Claude is the intelligence of this system, not a dispatcher. Delegation replaces Claude's typing and reading, never its thinking: Claude decomposes the task, writes sharp self-contained briefs, cross-examines consultant output against the repo, adjudicates disagreements between lanes with evidence, synthesizes one coherent solution, and keeps work where the analysis IS the deliverable (design decisions, subtle bugs, small precise edits). Forwarding prompts and pasting back answers is a failure mode. The conductor role is agent-agnostic: when Claude is unavailable and another agent (OpenCode, Gemini) leads the session, the same conductor duties and wrapper paths apply to it.

```text
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/codex-agent.sh consult --cd <repo> -- "<brief>"
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/codex-agent.sh review --uncommitted
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/codex-agent.sh implement --allow-write --cd <repo> --scope <path> -- "<task>"
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/consult-opencode.sh --lane code|reasoning|context|prose --sealed -- "<brief>"
```

OpenCode lanes: `--lane code` = Kimi K2.7 Code (technical/config/security checks), `--lane reasoning` = MiniMax M3 (deep reasoning at high effort), `--lane context` = DeepSeek V4 Flash (cheap ~1M-context sweeps of logs/diffs/repos), `--lane prose` = MiMo v2.5 Pro (writing/readability). Run lanes sequentially. The Codex flagship lane (`gpt-5.6-sol`, default effort high, xhigh per call for the hardest tasks, never max/ultra) is the main implementor; only when Codex rate-limits, times out, or is down, step down to OpenCode instead of pulling bulk work into Claude: consult -> `--lane reasoning` (hard thinking) or `--lane context` (input-heavy sweeps); review -> local `git diff` sealed to `--lane code`; implement -> `opencode-implement.sh --allow-write --scope <path>` (file edits only, no shell; the conductor runs tests and owns git).

Use `gpt-5.6-sol` through Codex CLI for bulk implementation, migrations, hard debugging, investigation, data analysis, and an independent engineering review. For user-facing UI, copy, API design, or product polish, require taste >= 7. For plan/implementation reviews, prefer `fable-5` or `opus-4.8`, optionally with a separate Codex (`gpt-5.6-sol`) pass. Never use Haiku.

Run the wrappers directly with Bash from the conductor — do not spawn a Claude subagent just to make a wrapper call. Only when a Claude subagent must own the call, spawn a thin `sonnet-5` low-effort wrapper whose job is only to write a self-contained Codex prompt, run `codex-agent.sh`, and return Codex output or the changed-file summary. The conductor verifies the output and owns final edits, tests, commits, and judgment.

Only run Codex implementation when the user explicitly wants Codex to make changes. Require `--allow-write`, scope paths with `--scope`, prefer a non-main branch or isolated worktree, never use `danger-full-access`, never bypass approvals/sandboxing, and never let Codex commit, push, or touch secrets.

Uninstalling the npm Claude Code CLI is not the same as deleting Claude user data. The safe default is:

```text
npm uninstall -g @anthropic-ai/claude-code
npm config delete allow-scripts --location=user
which claude || true
```

Do not add `rm -rf ~/.claude`, `rm -rf ~/.config/claude`, `rm -rf ~/.local/share/claude`, or `rm -rf ~/Library/Application Support/Claude` to uninstall commands.
