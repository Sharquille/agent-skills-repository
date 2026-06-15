#!/usr/bin/env bash
# deploy.sh — automates deployment and symlinking of agent skills to global
# environment folders for Claude Code/Desktop (~/.claude/skills), Gemini CLI
# (~/.gemini/skills), and Codex CLI (~/.codex/skills).
#
# All three discover skills one level deep (<dest>/<name>/SKILL.md), so skills
# are exposed as FLAT per-skill symlinks regardless of this repo's category
# nesting (skills/<category>/<name>/).
#
# Usage:   deploy.sh [--claude-only] [--gemini-only] [--codex-only]
#          (no flag = deploy to all three; flags combine)
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

for arg in "$@"; do
  case "$arg" in
    --claude-only) CLAUDE_ONLY=true ;;
    --gemini-only) GEMINI_ONLY=true ;;
    --codex-only)  CODEX_ONLY=true ;;
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

# Dispatch: with no --*-only flag, deploy to all three. Flags combine, so
# e.g. `--claude-only --codex-only` deploys to Claude and Codex but not Gemini.
if [ "$CLAUDE_ONLY" = false ] && [ "$GEMINI_ONLY" = false ] && [ "$CODEX_ONLY" = false ]; then
  deploy_claude
  deploy_gemini
  deploy_codex
else
  if [ "$CLAUDE_ONLY" = true ]; then deploy_claude; fi
  if [ "$GEMINI_ONLY" = true ]; then deploy_gemini; fi
  if [ "$CODEX_ONLY" = true ]; then deploy_codex; fi
fi

echo "Deployment complete! Skills are now globally available."
