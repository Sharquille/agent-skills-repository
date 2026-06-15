---
name: deploy-agent-skills
description: "Automates deployment and symlinking of agent skills in this repository to Claude Desktop/Code (~/.claude/skills), Gemini CLI (~/.gemini/skills), and Codex CLI (~/.codex/skills). All three discover skills one level deep, so skills are exposed as flat per-skill symlinks regardless of this repo's category nesting. Run with no flag to deploy to all three, or combine --claude-only / --gemini-only / --codex-only. Trigger when the user wants to configure, install, link, deploy, or update local repository skills across their terminal or AI assistants."
category: engineering
source: self-authored (this repository)
author: Sharquille Andrew
license: MIT
retrieved: 2026-06-14
---

# Deploy Agent Skills

Deploy and symlink agent skills from this repository to your global configuration environments for Claude (Desktop & Code), Gemini CLI, and Codex CLI. This ensures that skills you add or modify locally in this workspace are dynamically loaded and always active in your global agent sessions without duplicating files or writing manual config.

## When to use

- After onboarding a new skill (e.g. `frontend-ui-engineering`) to this repository to make it available globally.
- Setting up a new computer or environment for your local coding agents.
- Keeping skills synchronized across different coding assistants (Claude, Codex, Gemini CLI).
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
The script deploys to three directories. All three discover skills one level deep
(`<dest>/<name>/SKILL.md`), so each skill is exposed as a **flat per-skill symlink**
regardless of this repo's category nesting (`skills/<category>/<name>/`).

| Agent Platform | Destination Path | Mechanism |
|---|---|---|
| **Claude (Desktop/Code)** | `~/.claude/skills/` | Flat per-skill symlinks (a whole-dir symlink would nest skills too deep to load) |
| **Gemini CLI** | `~/.gemini/skills/` | Flat per-skill symlinks (Gemini's 1-directory-deep limit) |
| **Codex CLI** | `~/.codex/skills/` | Flat per-skill symlinks (same 1-deep discovery) |

### 3) Command Line Options

- **Default (No arguments):** Deploys to all three environments (Claude, Gemini, Codex).
- `--claude-only`: Only deploys and symlinks Claude skills.
- `--gemini-only`: Only deploys and symlinks Gemini skills.
- `--codex-only`: Only deploys and symlinks Codex skills.
- Flags **combine** — e.g. `--claude-only --codex-only` deploys to Claude and Codex but not Gemini.

### 4) Verification
After running the script, verify correct discovery in your interactive agents:

- In **Gemini CLI**, run:
  ```text
  /skills list
  ```
  *(If already inside a session, use `/skills reload` or `/skills refresh`)*
- In **Claude Code / Desktop**, the agent will discover them automatically in its registry on startup.
