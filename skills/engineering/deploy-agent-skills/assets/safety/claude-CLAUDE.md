# Global Claude Safety Rules

Before proposing or running destructive filesystem commands, explain the exact paths, what user data could be lost, safer alternatives, and the verification step. Wait for explicit approval for the exact command.

Use the `command-risk-review` skill when a request combines a command with a target path/resource, such as `rm -rf ~/.claude/*`, `rm -rf .*`, `find . -delete`, `git reset --hard`, `git clean`, HTTP `DELETE`, or cloud recursive remove.

Never delete or recursively remove `~/.claude`, `~/.config/claude`, `~/.local/share/claude`, `~/Library/Application Support/Claude`, `~/.agents`, `~/.codex`, `~/.gemini`, or `{{REPO_DIR}}` from an agent session.

## Agent Orchestra Defaults

For Claude-to-Codex/OpenCode orchestration, prefer the repo-managed wrappers over plugins:

```text
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/codex-agent.sh consult --cd <repo> -- "<brief>"
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/codex-agent.sh review --uncommitted
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/codex-agent.sh implement --allow-write --cd <repo> --scope <path> -- "<task>"
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/consult-opencode.sh --sealed --model provider/model -- "<brief>"
```

The Claude Code Codex plugin is optional convenience only. Do not block on it when the wrappers can do the job.

Use `gpt-5.5` through Codex CLI for bulk implementation, migrations, hard debugging, investigation, data analysis, and an independent engineering review. For user-facing UI, copy, API design, or product polish, require taste >= 7. For plan/implementation reviews, prefer `fable-5` or `opus-4.8`, optionally with a separate `gpt-5.5` Codex pass. Never use Haiku.

When a workflow needs `gpt-5.5` from a Claude subagent, spawn a thin `sonnet-5` low-effort wrapper whose job is only to write a self-contained Codex prompt, run `codex-agent.sh`, and return Codex output or the changed-file summary. The conductor verifies the output and owns final edits, tests, commits, and judgment.

Only run Codex implementation when the user explicitly wants Codex to make changes. Require `--allow-write`, scope paths with `--scope`, prefer a non-main branch or isolated worktree, never use `danger-full-access`, never bypass approvals/sandboxing, and never let Codex commit, push, or touch secrets.

Uninstalling the npm Claude Code CLI is not the same as deleting Claude user data. The safe default is:

```text
npm uninstall -g @anthropic-ai/claude-code
npm config delete allow-scripts --location=user
which claude || true
```

Do not add `rm -rf ~/.claude`, `rm -rf ~/.config/claude`, `rm -rf ~/.local/share/claude`, or `rm -rf ~/Library/Application Support/Claude` to uninstall commands.
