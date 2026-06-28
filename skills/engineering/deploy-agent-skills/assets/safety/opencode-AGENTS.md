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
