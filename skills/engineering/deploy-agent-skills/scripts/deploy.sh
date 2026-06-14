#!/usr/bin/env bash
# deploy.sh — automates deployment and symlinking of agent skills to global
# environment folders for Claude Code/Desktop (~/.claude/skills) and Gemini CLI (~/.gemini/skills).
#
# Usage:   deploy.sh [--gemini-only | --claude-only]
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

for arg in "$@"; do
  case "$arg" in
    --claude-only) CLAUDE_ONLY=true ;;
    --gemini-only) GEMINI_ONLY=true ;;
    *) echo "Unknown argument: $arg" >&2; exit 1 ;;
  esac
done

deploy_claude() {
  local SKILLS_DEST="$HOME/.claude/skills"
  echo "--- Deploying to Claude Code / Desktop ---"
  echo "Destination: $SKILLS_DEST"
  
  mkdir -p "$HOME/.claude"

  # If destination already exists and is not a symlink, back it up
  if [ -e "$SKILLS_DEST" ] && [ ! -L "$SKILLS_DEST" ]; then
    local BACKUP="$SKILLS_DEST.backup.$(date +%Y%m%d%H%M%S)"
    echo "  Backup existing ~/.claude/skills -> $BACKUP"
    mv "$SKILLS_DEST" "$BACKUP"
  fi

  # Link if not already linked to correct source
  if [ -L "$SKILLS_DEST" ] && [ "$(readlink "$SKILLS_DEST")" = "$SKILLS_SRC" ]; then
    echo "  Claude skills already linked correctly."
  else
    [ -L "$SKILLS_DEST" ] && rm "$SKILLS_DEST"
    ln -s "$SKILLS_SRC" "$SKILLS_DEST"
    echo "  Linked: $SKILLS_DEST -> $SKILLS_SRC"
  fi
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

if [ "$CLAUDE_ONLY" = false ] && [ "$GEMINI_ONLY" = false ]; then
  deploy_claude
  deploy_gemini
elif [ "$CLAUDE_ONLY" = true ]; then
  deploy_claude
elif [ "$GEMINI_ONLY" = true ]; then
  deploy_gemini
fi

echo "Deployment complete! Skills are now globally available."
