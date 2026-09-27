#!/usr/bin/env bash
# Runs deploy.sh against a temporary HOME and checks that a real (managed)
# skill folder is never replaced, deleted, or given a nested link, while
# symlinks and empty paths are still (re)linked.
set -euo pipefail

DEPLOY="$(cd "$(dirname "${BASH_SOURCE[0]}")/../scripts" && pwd)/deploy.sh"
SKILLS_SRC="$(cd "$(dirname "$DEPLOY")/../../.." && pwd)"
# Any real skill works; take the first one that has a SKILL.md.
REAL_SKILL="$(basename "$(dirname "$(ls "$SKILLS_SRC"/*/*/SKILL.md | head -1)")")"

TMP_HOME="$(mktemp -d)"
trap 'rm -rf "$TMP_HOME"' EXIT
fail() { echo "FAIL: $*"; exit 1; }

DESTS=(.claude/skills .gemini/skills .codex/skills .agents/skills)
for d in "${DESTS[@]}"; do
  mkdir -p "$TMP_HOME/$d/$REAL_SKILL"
  echo keep > "$TMP_HOME/$d/$REAL_SKILL/marker.txt"
  ln -s /nonexistent/old-skill "$TMP_HOME/$d/stale-skill"
done

out="$(HOME="$TMP_HOME" bash "$DEPLOY" --claude-only --gemini-only --codex-only --opencode-only \
  --skip-safety --skip-config-sync)"

for d in "${DESTS[@]}"; do
  managed="$TMP_HOME/$d/$REAL_SKILL"
  [ -d "$managed" ] && [ ! -L "$managed" ] || fail "$d/$REAL_SKILL is no longer a real folder"
  [ "$(cat "$managed/marker.txt")" = keep ] || fail "$d/$REAL_SKILL contents changed"
  [ ! -e "$managed/$REAL_SKILL" ] && [ ! -L "$managed/$REAL_SKILL" ] || fail "nested link inside $d/$REAL_SKILL"
  [ ! -L "$TMP_HOME/$d/stale-skill" ] || fail "stale link in $d was not pruned"
  linked=$(find "$TMP_HOME/$d" -mindepth 1 -maxdepth 1 -type l | wc -l)
  [ "$linked" -gt 0 ] || fail "no skills linked into $d"
done

[ "$(grep -c "Skipping $REAL_SKILL: real folder" <<<"$out")" -eq 4 ] || fail "expected one skip warning per destination"
echo "PASS: real folders untouched in ${#DESTS[@]} destinations; others linked; stale links pruned"
