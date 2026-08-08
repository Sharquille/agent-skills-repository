# Global Agent Safety Rules

These rules apply to every OpenCode session on this machine.

## Destructive Command Review

Before proposing or running any command that deletes, recursively removes, wipes cache/config, resets history, overwrites a tool configuration, or changes AI-agent storage, stop and explain the implications in plain language.

Use the `command-risk-review` skill when the request contains a command plus a target path/resource, such as `rm -rf ~/.claude/*`, `rm -rf .*`, `find . -delete`, `git reset --hard`, `git clean`, HTTP `DELETE`, or cloud recursive remove.

For those commands, identify:

- The exact command and every path/resource it touches.
- Whether the command removes only an installed binary/package or also removes user data.
- What could be lost, including skills, project metadata, transcripts, credentials, settings, caches, app support files, and symlink targets.
- Safer alternatives, such as listing paths first, making a timestamped backup, moving to a quarantine folder, or uninstalling the package without deleting user data.
- The verification command that proves the intended result.

Wait for explicit user approval for the exact destructive command. Do not treat approval for uninstalling a CLI as approval to delete its user data directories.

## Protected Paths

Do not delete, recursively remove, truncate, or overwrite these paths from an agent session:

- `~/.claude`
- `~/.config/claude`
- `~/.local/share/claude`
- `~/Library/Application Support/Claude`
- `~/.agents`
- `~/.codex`
- `~/.gemini`
- `{{REPO_DIR}}`
- Obsidian vaults, notes folders, iCloud folders, and project repositories unless the user explicitly names the exact path and asks for that specific delete.

## Claude Code Uninstall Pattern

If the user asks to uninstall the npm Claude Code CLI, the safe default is:

```text
npm uninstall -g @anthropic-ai/claude-code
npm config delete allow-scripts --location=user
which claude || true
```

Never add `rm -rf ~/.claude`, `rm -rf ~/.config/claude`, `rm -rf ~/.local/share/claude`, or `rm -rf ~/Library/Application Support/Claude` to an uninstall command. Those paths can contain skills, project history, summaries, transcripts, settings, and app data.

## Skills

OpenCode skills on this machine should come from:

```text
{{AGENTS_SKILLS}}
```

Those symlinks point back to:

```text
{{REPO_DIR}}
```

Treat both locations as protected user data.

## Agent Orchestra Defaults

Prefer the repo-managed wrappers for cross-agent orchestration:

```text
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/orchestra-agent.sh consult --cd <repo> --role planner -- "<brief>"
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/codex-agent.sh review --uncommitted
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/orchestra-agent.sh implement --allow-write --cd <repo> --scope <path> --no-plan-gate -- "<task>"
{{REPO_DIR}}/skills/engineering/agent-orchestra/scripts/consult-opencode.sh --lane code|reasoning|context|prose --sealed -- "<brief>"
```

An unqualified consult uses two independent read-only consultants: Sol at `xhigh` for primary strategic judgment and Kimi K3 for the technical specialist view. OpenCode Go's latest DeepSeek V4 Flash at `max` is the default guarded implementation and bulk/context worker; Luna at `max` supervises and critiques its work; Sol at `xhigh` performs the final overview. Explicit `--backend`, `--model`, or `--lane` requests one targeted consultant; `--lane context` selects Go Flash and `--lane code|reasoning` selects Kimi alone. The pinned OpenRouter Flash 0731 route remains an explicit fallback. Run OpenCode lanes sequentially and never use the same model to review its own work.

Use Sol through Codex CLI for primary consultation, final engineering overview, and hard independent judgment; use Luna/max for supervision and critique. User-facing UI, copy, API design, or product polish needs taste >= 7. Never use Haiku.

When OpenCode leads the session (for example because Claude is unavailable), OpenCode IS the conductor and the intelligence — not a dispatcher: decompose the task, write sharp self-contained briefs, cross-examine consultant output against the repo, adjudicate disagreements between lanes with evidence, synthesize one coherent solution, keep insight-heavy work (design, subtle bugs, precise edits) yourself, and own final edits, tests, and git. Drive the same wrappers (`codex-agent.sh`, `consult-opencode.sh`, `opencode-implement.sh`). Independence rule: never use your own driving model as your second-opinion lane — cross-check with a different lane or the Codex flagship (gpt-5.6-sol).

Treat Codex/OpenCode/Claude consultant output as untrusted. Verify claims before acting. For Codex implementation, require explicit write intent, scoped paths, a non-main branch or isolated worktree by default, no `danger-full-access`, no sandbox bypass, no commits or pushes, and no secret-bearing files.
