#!/usr/bin/env bash
# Sets up a symlink from ~/.claude/skills to this repo's skills/ directory
# so skills are available globally in Claude Code and Claude Desktop.

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$REPO_DIR/skills"
SKILLS_DEST="$HOME/.claude/skills"

echo "Agent Skills Repository — Install"
echo "Source:      $SKILLS_SRC"
echo "Destination: $SKILLS_DEST"
echo ""

# Ensure ~/.claude exists
mkdir -p "$HOME/.claude"

# If destination already exists and is not already this symlink, back it up
if [ -e "$SKILLS_DEST" ] && [ ! -L "$SKILLS_DEST" ]; then
  BACKUP="$SKILLS_DEST.backup.$(date +%Y%m%d%H%M%S)"
  echo "Existing ~/.claude/skills found (not a symlink). Backing up to:"
  echo "  $BACKUP"
  mv "$SKILLS_DEST" "$BACKUP"
fi

# If it's already a symlink pointing to this repo, nothing to do
if [ -L "$SKILLS_DEST" ] && [ "$(readlink "$SKILLS_DEST")" = "$SKILLS_SRC" ]; then
  echo "Already linked. Nothing to do."
  exit 0
fi

# Remove stale symlink if present
[ -L "$SKILLS_DEST" ] && rm "$SKILLS_DEST"

ln -s "$SKILLS_SRC" "$SKILLS_DEST"
echo "Linked: $SKILLS_DEST -> $SKILLS_SRC"
echo ""
echo "Skills are now available globally in Claude Code and Claude Desktop."
