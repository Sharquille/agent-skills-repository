---
name: deploy-agent-skills
description: "Automates deployment and symlinking of agent skills in this repository to Claude Desktop/Code (~/.claude/skills), Gemini CLI (~/.gemini/skills), Codex CLI (~/.codex/skills), and OpenCode/shared agents (~/.agents/skills). Also installs reproducible local safety and orchestration guardrails for destructive command review, protected agent data paths, and Agent Orchestra wrapper-first model routing. Run with no flag to deploy skills and safety to all supported agents, combine --claude-only / --gemini-only / --codex-only / --opencode-only, use --safety-only for guardrails only, or --skip-safety for skills only. Trigger when the user wants to configure, install, link, deploy, update, or reproduce local repository skills and agent safety rules across terminal or AI assistants."
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
  blocks: wrapper-first Codex and OpenCode calls, optional plugin use only,
  `gpt-5.5` via Codex CLI for bulk work, taste-aware model routing, no Haiku,
  and guarded Codex implementation through
  `codex-agent.sh --allow-write --scope`.
- Keeps Codex's own `AGENTS.md` safety-only so invoked Codex workers do not
  recursively route back through Agent Orchestra.

### 4) Command Line Options

- **Default (No arguments):** Deploys to all supported environments and installs safety guardrails.
- `--claude-only`: Only deploys and symlinks Claude skills.
- `--gemini-only`: Only deploys and symlinks Gemini skills.
- `--codex-only`: Only deploys and symlinks Codex skills.
- `--opencode-only`: Only deploys and symlinks OpenCode/shared-agent skills.
- `--safety-only`: Only install safety guardrails.
- `--skip-safety` / `--no-safety`: Deploy skills without installing safety guardrails.
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
