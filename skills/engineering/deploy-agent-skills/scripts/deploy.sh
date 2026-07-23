#!/usr/bin/env bash
# deploy.sh — automates deployment and symlinking of agent skills to global
# environment folders for Claude Code/Desktop (~/.claude/skills), Gemini CLI
# (~/.gemini/skills), Codex CLI (~/.codex/skills), and OpenCode/shared agents
# (~/.agents/skills). It also installs reproducible safety guardrails by default.
#
# When Claude is part of the run it additionally snapshots the version-controllable
# ~/.claude/settings.json back into the dotfiles repo (capture only) so the tracked
# copy never silently drifts from a hand-edit. Skip with --skip-config-sync.
#
# Supported agents discover skills one level deep (<dest>/<name>/SKILL.md), so skills
# are exposed as FLAT per-skill symlinks regardless of this repo's category
# nesting (skills/<category>/<name>/).
#
# Usage:   deploy.sh [--claude-only] [--gemini-only] [--codex-only] [--opencode-only]
#          deploy.sh [--safety-only] [--skip-safety] [--skip-config-sync]
#          (no flag = deploy to all supported agents, sync Claude config to
#           dotfiles, and install safety; flags combine)
# Exit:    0 = success, 1 = failure.

set -euo pipefail

# Find repository root directory
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
SKILLS_SRC="$REPO_DIR/skills"

echo "Deploying Agent Skills..."
echo "Source Repository: $REPO_DIR"
echo ""

CLAUDE_ONLY=false
GEMINI_ONLY=false
CODEX_ONLY=false
OPENCODE_ONLY=false
SAFETY_ONLY=false
SKIP_SAFETY=false
SKIP_CONFIG_SYNC=false

for arg in "$@"; do
  case "$arg" in
    --claude-only) CLAUDE_ONLY=true ;;
    --gemini-only) GEMINI_ONLY=true ;;
    --codex-only)  CODEX_ONLY=true ;;
    --opencode-only) OPENCODE_ONLY=true ;;
    --safety-only) SAFETY_ONLY=true ;;
    --skip-safety|--no-safety) SKIP_SAFETY=true ;;
    --skip-config-sync|--no-config-sync) SKIP_CONFIG_SYNC=true ;;
    *) echo "Unknown argument: $arg" >&2; exit 1 ;;
  esac
done

deploy_claude() {
  local SKILLS_DEST="$HOME/.claude/skills"
  echo "--- Deploying to Claude Code / Desktop ---"
  echo "Destination: $SKILLS_DEST"

  mkdir -p "$HOME/.claude"

  # Claude discovers skills at ~/.claude/skills/<name>/SKILL.md — ONE level deep.
  # This repo nests skills under categories (skills/<category>/<name>/), so a
  # whole-dir symlink (~/.claude/skills -> repo/skills) buries every skill one
  # level too deep and NONE of them load. Use FLAT per-skill symlinks instead,
  # exactly like the Gemini path below (same 1-deep limit).

  # Migrate a legacy whole-dir symlink from older installs into a real directory.
  if [ -L "$SKILLS_DEST" ]; then
    echo "  Removing legacy whole-dir symlink (it nested skills too deep to load)."
    rm "$SKILLS_DEST"
  elif [ -e "$SKILLS_DEST" ] && [ ! -d "$SKILLS_DEST" ]; then
    local BACKUP="$SKILLS_DEST.backup.$(date +%Y%m%d%H%M%S)"
    echo "  Backing up existing ~/.claude/skills -> $BACKUP"
    mv "$SKILLS_DEST" "$BACKUP"
  fi
  mkdir -p "$SKILLS_DEST"

  local linked_count=0
  for skill_dir in "$SKILLS_SRC"/*/*; do
    [ -d "$skill_dir" ] || continue
    local skill_name
    skill_name=$(basename "$skill_dir")
    [ "$skill_name" = ".gitkeep" ] && continue
    [ "$skill_name" = "_template" ] && continue
    [[ "$skill_name" =~ ^\. ]] && continue
    [ -f "$skill_dir/SKILL.md" ] || continue   # only real skills

    local abs_path
    abs_path="$(cd "$skill_dir" && pwd)"
    ln -sfn "$abs_path" "$SKILLS_DEST/$skill_name"
    linked_count=$((linked_count + 1))
  done

  # Prune stale links that no longer resolve to a skill (e.g. renamed/removed).
  for existing in "$SKILLS_DEST"/*; do
    [ -L "$existing" ] || continue
    [ -e "$existing/SKILL.md" ] || { echo "  Pruning stale link: $(basename "$existing")"; rm -f "$existing"; }
  done

  echo "  Successfully linked $linked_count skills to Claude (~/.claude/skills)."
  echo ""
}

deploy_gemini() {
  local GEMINI_DEST="$HOME/.gemini/skills"
  echo "--- Deploying to Gemini CLI ---"
  echo "Destination: $GEMINI_DEST"
  
  mkdir -p "$GEMINI_DEST"

  # Iterate over categorized subfolders (skills/<category>/<skill_name>)
  # Wildcard pattern matches skills/*/*, e.g. skills/engineering/ai-slop-cleaner
  local linked_count=0
  for skill_dir in "$SKILLS_SRC"/*/*; do
    [ -d "$skill_dir" ] || continue
    local skill_name
    skill_name=$(basename "$skill_dir")
    
    # Exclude placeholders, templates or hidden files
    [ "$skill_name" = ".gitkeep" ] && continue
    [ "$skill_name" = "_template" ] && continue
    [[ "$skill_name" =~ ^\. ]] && continue

    local abs_path
    abs_path="$(cd "$skill_dir" && pwd)"
    local dest_link="$GEMINI_DEST/$skill_name"

    # Remove existing link/file if any
    [ -L "$dest_link" ] || [ -e "$dest_link" ] && rm -rf "$dest_link"

    # Create individual symlink conforming to Gemini's 1-directory deep nesting limit
    ln -s "$abs_path" "$dest_link"
    echo "  Linked: ~/.gemini/skills/$skill_name -> $skill_dir"
    linked_count=$((linked_count + 1))
  done

  # Prune stale links that no longer resolve to a skill (e.g. renamed/removed).
  for existing in "$GEMINI_DEST"/*; do
    [ -L "$existing" ] || continue
    [ -e "$existing/SKILL.md" ] || { echo "  Pruning stale link: $(basename "$existing")"; rm -f "$existing"; }
  done

  echo "  Successfully linked $linked_count skills to Gemini CLI."
  echo ""
}

deploy_codex() {
  local CODEX_DEST="$HOME/.codex/skills"
  echo "--- Deploying to Codex CLI ---"
  echo "Destination: $CODEX_DEST"

  mkdir -p "$CODEX_DEST"

  # Codex discovers skills one level deep (~/.codex/skills/<name>/SKILL.md), so
  # use FLAT per-skill symlinks — same approach as Claude and Gemini.
  local linked_count=0
  for skill_dir in "$SKILLS_SRC"/*/*; do
    [ -d "$skill_dir" ] || continue
    local skill_name
    skill_name=$(basename "$skill_dir")
    [ "$skill_name" = ".gitkeep" ] && continue
    [ "$skill_name" = "_template" ] && continue
    [[ "$skill_name" =~ ^\. ]] && continue
    [ -f "$skill_dir/SKILL.md" ] || continue   # only real skills

    local abs_path
    abs_path="$(cd "$skill_dir" && pwd)"
    ln -sfn "$abs_path" "$CODEX_DEST/$skill_name"
    linked_count=$((linked_count + 1))
  done

  # Prune stale links that no longer resolve to a skill.
  for existing in "$CODEX_DEST"/*; do
    [ -L "$existing" ] || continue
    [ -e "$existing/SKILL.md" ] || { echo "  Pruning stale link: $(basename "$existing")"; rm -f "$existing"; }
  done

  echo "  Successfully linked $linked_count skills to Codex (~/.codex/skills)."
  echo ""
}

deploy_opencode() {
  local OPENCODE_DEST="$HOME/.agents/skills"
  echo "--- Deploying to OpenCode / shared agent skills ---"
  echo "Destination: $OPENCODE_DEST"

  mkdir -p "$OPENCODE_DEST"

  # OpenCode discovers external skills from ~/.agents/skills/<name>/SKILL.md
  # and ~/.claude/skills/<name>/SKILL.md. Use ~/.agents/skills so OpenCode is
  # not dependent on Claude's user-data directory existing.
  local linked_count=0
  for skill_dir in "$SKILLS_SRC"/*/*; do
    [ -d "$skill_dir" ] || continue
    local skill_name
    skill_name=$(basename "$skill_dir")
    [ "$skill_name" = ".gitkeep" ] && continue
    [ "$skill_name" = "_template" ] && continue
    [[ "$skill_name" =~ ^\. ]] && continue
    [ -f "$skill_dir/SKILL.md" ] || continue

    local abs_path
    abs_path="$(cd "$skill_dir" && pwd)"
    ln -sfn "$abs_path" "$OPENCODE_DEST/$skill_name"
    linked_count=$((linked_count + 1))
  done

  # Prune stale links that no longer resolve to a skill.
  for existing in "$OPENCODE_DEST"/*; do
    [ -L "$existing" ] || continue
    [ -e "$existing/SKILL.md" ] || { echo "  Pruning stale link: $(basename "$existing")"; rm -f "$existing"; }
  done

  echo "  Successfully linked $linked_count skills to OpenCode/shared agents (~/.agents/skills)."
  echo ""
}

sync_claude_dotfiles() {
  # Snapshot the version-controllable ~/.claude/settings.json back into the
  # dotfiles repo so a hand-edit (via /config, /model, theme, or new hooks)
  # doesn't silently drift from the committed copy. Capture direction ONLY
  # (live -> dotfiles): never touches the live config, never commits.
  # Override the destination dir with CLAUDE_DOTFILES_DIR if your repo differs.
  local src="$HOME/.claude/settings.json"
  local dest_dir="${CLAUDE_DOTFILES_DIR:-$HOME/dotfiles/.claude}"
  local dest="$dest_dir/settings.json"

  echo "--- Syncing Claude config to dotfiles ---"
  if [ ! -f "$src" ]; then
    echo "  Skipped: $src not found."; echo ""; return 0
  fi
  if [ ! -d "$dest_dir" ]; then
    echo "  Skipped: $dest_dir not found (dotfiles repo absent)."; echo ""; return 0
  fi

  # Fail-safe: never capture a config that looks like it gained a credential.
  # (Secrets belong in settings.local.json, which stays git-ignored. The dotfiles
  # repo's own gitleaks pre-commit hook is the authoritative gate; this is just a
  # high-signal early guard so a secret never reaches the working tree.)
  if grep -iqE '(sk-[A-Za-z0-9]{20}|ghp_[A-Za-z0-9]{20}|gho_[A-Za-z0-9]{20}|github_pat_|AKIA[0-9A-Z]{12}|xox[baprs]-[0-9A-Za-z-]|-----BEGIN [A-Z].*PRIVATE|apiKeyHelper)' "$src"; then
    echo "  ⚠ Skipped: $src looks like it contains secrets/credentials — not"
    echo "    copying into the tracked repo. Move secrets to settings.local.json."
    echo ""; return 0
  fi

  if [ -f "$dest" ] && cmp -s "$src" "$dest"; then
    echo "  Up to date: dotfiles copy already matches live config."; echo ""; return 0
  fi
  cp "$src" "$dest"
  echo "  Updated: $dest"
  echo "  (dotfiles working tree changed — review & commit when ready)"
  echo ""
}

install_safety() {
  local installer="$REPO_DIR/skills/engineering/deploy-agent-skills/scripts/install-agent-safety.py"
  python3 "$installer" --repo-dir "$REPO_DIR"
}

if [ "$SAFETY_ONLY" = true ]; then
  install_safety
  echo "Safety deployment complete."
  exit 0
fi

# Dispatch: with no --*-only flag, deploy to all supported agents. Flags combine,
# so e.g. `--claude-only --codex-only` deploys to Claude and Codex only.
if [ "$CLAUDE_ONLY" = false ] && [ "$GEMINI_ONLY" = false ] && [ "$CODEX_ONLY" = false ] && [ "$OPENCODE_ONLY" = false ]; then
  deploy_claude
  deploy_gemini
  deploy_codex
  deploy_opencode
else
  if [ "$CLAUDE_ONLY" = true ]; then deploy_claude; fi
  if [ "$GEMINI_ONLY" = true ]; then deploy_gemini; fi
  if [ "$CODEX_ONLY" = true ]; then deploy_codex; fi
  if [ "$OPENCODE_ONLY" = true ]; then deploy_opencode; fi
fi

# Capture the (version-controllable) Claude config back into dotfiles whenever
# Claude was part of this run — i.e. the default all-agents run, or --claude-only.
# Capture-only: never edits the live config, never commits.
if [ "$SKIP_CONFIG_SYNC" = false ] && { [ "$CLAUDE_ONLY" = true ] || \
   { [ "$CLAUDE_ONLY" = false ] && [ "$GEMINI_ONLY" = false ] && [ "$CODEX_ONLY" = false ] && [ "$OPENCODE_ONLY" = false ]; }; }; then
  sync_claude_dotfiles
fi

if [ "$SKIP_SAFETY" = false ]; then
  install_safety
fi

echo "Deployment complete! Skills and safety guardrails are now globally available."
