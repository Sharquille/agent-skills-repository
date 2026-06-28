# Protected Targets Reference

Use this reference when a command targets dotfiles, agent state, app support data, project history, vaults, repositories, or broad globs.

## Agent State

| Target | Risk | What may be at stake |
|---|---|---|
| `~/.claude` | Critical | Claude Code user state, `skills/`, `projects/*.jsonl` transcripts, settings, cleanup markers, MCP/session state. |
| `~/.claude/skills` | High | User-installed and repo-backed skills. Often symlinks into a source repository. |
| `~/.claude/projects` | Critical | Per-project JSONL conversation transcripts and project history used by Claude Code/Desktop summaries. |
| `~/.config/claude` | High | Claude configuration and app/tool settings. |
| `~/.local/share/claude` | High | Local Claude app/tool data depending on install. |
| `~/Library/Application Support/Claude` | Critical | Claude Desktop app data, local-agent sessions, summaries, bundled/plugin state, and databases. |
| `~/.agents` | High | Shared agent skills loaded by OpenCode and other agents. |
| `~/.codex` | Critical | Codex skills, config, plugin cache, project state, and instructions. |
| `~/.gemini` | High | Gemini CLI skills and configuration. |
| `~/.config/opencode` | High | OpenCode config, permissions, global `AGENTS.md`, and installed plugins. |
| `~/.local/share/opencode` | High | OpenCode sessions, logs, state DBs, and project metadata. |
| `agent-skills-repository` | Critical | Source of truth for skills, deploy scripts, safety rules, and reproducibility. |

## Project and Knowledge Stores

| Target | Risk | What may be at stake |
|---|---|---|
| `.git` | Critical | Full repository history, refs, hooks, worktrees, and recovery metadata. |
| `.github`, `.gitlab`, hooks | High | CI/CD, automation, release, and security workflow definitions. |
| Obsidian vaults, notes folders | Critical | Knowledge base, study history, attachments, plugins, and sync metadata. |
| iCloud, Dropbox, Google Drive paths | Critical | Synced data where deletion can propagate to other devices. |
| `~/Documents`, `~/Downloads`, project roots | Critical | Mixed user data; never bulk delete without exact inventory. |
| `*.sqlite`, `*.db`, `*.jsonl`, `sessions`, `transcripts` | High | Conversation state, local app data, logs, and audit evidence. |

## Usually Rebuildable But Still Ask

| Target | Typical risk | Notes |
|---|---|---|
| `node_modules` | Low to medium | Usually reinstallable, but may contain local patches or generated artifacts. Verify package manager lockfile exists. |
| `.next`, `dist`, `build`, `coverage` | Low to medium | Usually generated output. Verify it is not a deployment artifact or only copy. |
| `.cache`, `~/Library/Caches` | Medium | Often rebuildable, but may contain session tokens, downloaded models, indexes, or expensive local caches. |
| package-manager caches | Medium | Rebuildable but can cost time/network and may affect offline work. |

## Dangerous Glob Patterns

- `.*` means "hidden names in this directory" in common shells. It can select many important dotfiles and dotdirs. Some shells/options may also produce `.` and `..`; even when `rm` protects those, other hidden names can still be removed.
- `.[!.]*` and `..?*` are common hidden-file cleanup patterns. They intentionally target dotfiles and should be treated as high-risk bulk deletes.
- `*` in a home directory, app support folder, repository root, vault, or config directory is high-risk because the target set is broad.
- Quoting a glob, such as `".claude/*"`, changes expansion behavior. Review both the literal argument and the likely intended path.

## Safer Patterns

- Split uninstall from data cleanup:
  ```text
  npm uninstall -g @anthropic-ai/claude-code
  npm config delete allow-scripts --location=user
  which claude || true
  ```
- Inspect before deleting:
  ```text
  ls -la ~/.claude
  find ~/.claude -maxdepth 2 -type f | sed -n '1,80p'
  du -sh ~/.claude
  ```
- Prefer backup/quarantine over delete:
  ```text
  mv ~/.claude ~/.claude.backup.$(date +%Y%m%d%H%M%S)
  ```
  Only use this after explicit approval because moving can still break active tools.

## Approval Question Pattern

Ask about the data boundary, not just the command:

```text
Do you want to remove only the installed CLI binary/package, or do you also want to delete user data at <target>? Deleting <target> may remove <specific artifacts>.
```
