---
name: deploy-agent-skills
description: "Automates deployment and symlinking of agent skills in this repository to Claude Desktop/Code (~/.claude/skills), Gemini CLI (~/.gemini/skills), Codex CLI (~/.codex/skills), and OpenCode/shared agents (~/.agents/skills). Also installs reproducible local safety and orchestration guardrails for destructive command review, protected agent data paths, and Agent Orchestra wrapper-first model routing. Run with no flag to deploy skills and safety to all supported agents, combine --claude-only / --gemini-only / --codex-only / --opencode-only, use --safety-only for guardrails only, or --skip-safety for skills only. When Claude is deployed it also snapshots ~/.claude/settings.json into the dotfiles repo (capture-only, secret-guarded; skip with --skip-config-sync). Trigger when the user wants to configure, install, link, deploy, update, or reproduce local repository skills and agent safety rules across terminal or AI assistants."
category: engineering
source: self-authored (this repository)
author: Sharquille Andrew
license: MIT
retrieved: 2026-06-14
---

# Deploy Agent Skills

Deploy and symlink agent skills from this repository to your global configuration environments for Claude (Desktop & Code), Gemini CLI, Codex CLI, and OpenCode/shared agents. The deployment also installs tracked safety and orchestration guardrails so destructive commands must be reviewed with target-aware context and agents prefer Agent Orchestra's wrapper-first model routing defaults.

## When to use

- After onboarding a new skill (e.g. `frontend-ui-engineering`) to this repository to make it available globally.
- Setting up a new computer or environment for your local coding agents.
- Keeping skills synchronized across different coding assistants (Claude, Codex, Gemini CLI).
- Reinstalling OpenCode safety rules and shared skills after moving to a new machine.
- Restoring protected-path guidance after agent config or cache cleanup.
- Updating existing links if directory structures change.

## When NOT to use

- Trying to build or audit a single skill file → use `vet-skill`.
- Setting up project-specific configs or scanning workspace security → use `agent-repo-security`.

## Workflow

### 1) Run the automated deployment script
Execute the script from the root of this repository:
```text
scripts/deploy.sh
```
Or run the deployment through this skill's shipped script directly:
```text
skills/engineering/deploy-agent-skills/scripts/deploy.sh
```

### 2) Support Platforms
The script deploys to four directories. These agents discover skills one level deep
(`<dest>/<name>/SKILL.md`), so each skill is exposed as a **flat per-skill symlink**
regardless of this repo's category nesting (`skills/<category>/<name>/`).

| Agent Platform | Destination Path | Mechanism |
|---|---|---|
| **Claude (Desktop/Code)** | `~/.claude/skills/` | Flat per-skill symlinks (a whole-dir symlink would nest skills too deep to load) |
| **Gemini CLI** | `~/.gemini/skills/` | Flat per-skill symlinks (Gemini's 1-directory-deep limit) |
| **Codex CLI** | `~/.codex/skills/` | Flat per-skill symlinks (same 1-deep discovery) |
| **OpenCode / shared agents** | `~/.agents/skills/` | Flat per-skill symlinks independent of Claude's user-data directory |

### 3) Safety And Orchestration Guardrails
By default, deployment installs safety and Agent Orchestra routing rules from `assets/safety/` through `scripts/install-agent-safety.py`.

The safety installer:

- Merges OpenCode permissions into `~/.config/opencode/opencode.jsonc`.
- Adds `~/.agents/skills` as OpenCode's explicit skill path.
- Hard-denies high-risk delete patterns for `.claude`, `.agents`, `.codex`, `.gemini`, Claude app support data, broad hidden globs such as `rm -rf .*`, and this repository.
- Appends or refreshes managed safety blocks in:
  - `~/.config/opencode/AGENTS.md`
  - `~/.claude/CLAUDE.md`
  - `~/.gemini/GEMINI.md`
  - `~/.codex/AGENTS.md`
- Backs up files before changing them.
- Adds Agent Orchestra defaults to the Claude, Gemini, and OpenCode managed
  blocks: wrapper-only Codex and OpenCode calls (no plugins), delegation of
  token-heavy work off-Claude to preserve Claude usage and rate limits,
  Sol/xhigh + Kimi K3 consultation, OpenCode Go DeepSeek V4 Flash/max
  implementation and bulk/context work, Luna/max supervision/critique,
  Sol/xhigh overview, targeted single-lane overrides, no Haiku, and
  guarded implementation through `orchestra-agent.sh --allow-write --scope`.
- Adds a short, preservation-first writing-standard pointer to all four managed
  blocks. `anti-slop-standard` owns code authoring and handover; `unslop` owns
  prose authoring. The full code, prose, document-structure, and Markdown rules
  stay in the repository skills and load when the relevant work requires them.
  The writing standard does not override user instructions, required legal or
  security wording, technical precision, or established repository terminology.
- Keeps Codex's own `AGENTS.md` to safety and the writing standard, with no
  orchestration routing, so invoked Codex workers do not recursively route back
  through Agent Orchestra.

### Claude Config Snapshot

When Claude is part of the run (default, or `--claude-only`), the script also
snapshots the version-controllable `~/.claude/settings.json` back into the
dotfiles repo (`~/dotfiles/.claude/settings.json`; override with
`CLAUDE_DOTFILES_DIR`). This keeps the committed copy from silently drifting
when the config is hand-edited via `/config`, `/model`, theme, or new hooks.

- **Capture only** (`live → dotfiles`): never edits the live config and never
  commits — it refreshes the working-tree copy for you to review and commit.
- **Secret fail-safe:** if the config looks like it gained a credential (token
  shapes, `apiKeyHelper`, private-key blocks) the snapshot is skipped with a
  warning. Secrets belong in the git-ignored `settings.local.json`.
- Runs only when Claude is being deployed; disable with `--skip-config-sync`.

### 4) Command Line Options

- **Default (No arguments):** Deploys to all supported environments, snapshots Claude config to dotfiles, and installs safety guardrails.
- `--claude-only`: Only deploys and symlinks Claude skills.
- `--gemini-only`: Only deploys and symlinks Gemini skills.
- `--codex-only`: Only deploys and symlinks Codex skills.
- `--opencode-only`: Only deploys and symlinks OpenCode/shared-agent skills.
- `--safety-only`: Only install safety guardrails.
- `--skip-safety` / `--no-safety`: Deploy skills without installing safety guardrails.
- `--skip-config-sync` / `--no-config-sync`: Skip snapshotting `~/.claude/settings.json` into the dotfiles repo.
- Flags **combine** — e.g. `--claude-only --codex-only` deploys to Claude and Codex but not Gemini.

For a narrow guardrail refresh, call the installer directly with `--target`:

```text
skills/engineering/deploy-agent-skills/scripts/install-agent-safety.py --repo-dir <repo> --target claude
```

Targets: `claude`, `codex`, `gemini`, `opencode-agents`, `opencode-config`, or
`all` (default).

### 5) Verification
After running the script, verify correct discovery in your interactive agents:

- In **Gemini CLI**, run:
  ```text
  /skills list
  ```
  *(If already inside a session, use `/skills reload` or `/skills refresh`)*
- In **Claude Code / Desktop**, the agent will discover them automatically in its registry on startup.
- In **OpenCode**, run:
  ```text
  opencode debug skill
  ```
  and confirm skill locations include `~/.agents/skills`.
- For safety rules, run:
  ```text
  opencode debug config
  ```
  and confirm `permission.bash` includes protected-path denies and `skills.paths` includes `~/.agents/skills`.
