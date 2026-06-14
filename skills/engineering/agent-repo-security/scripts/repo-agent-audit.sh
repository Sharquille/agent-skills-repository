#!/usr/bin/env bash
# repo-agent-audit.sh — read-only security-posture check for a repo before/while
# AI coding agents (Claude, Codex, Gemini, Cursor, aider) work in it.
#
# Usage:   repo-agent-audit.sh [repo-path]   (defaults to current directory)
# Exit:    0 = no blocking findings, 1 = review needed, 2 = usage error.
#
# Read-only: never modifies the repo. Findings are advisory — read the context.
# Uses gitleaks/trufflehog if installed; otherwise falls back to pattern checks.

set -uo pipefail
REPO="${1:-.}"
cd "$REPO" 2>/dev/null || { echo "no such path: $REPO" >&2; exit 2; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "not a git repo: $REPO" >&2; exit 2; }

FINDINGS=0
line(){ printf '%s\n' "===================================================================="; }
flag(){ FINDINGS=$((FINDINGS+1)); }

# --- 1. Secrets in tracked files / history -------------------------------------
line; echo "1. SECRETS & CREDENTIALS"; line
if command -v gitleaks >/dev/null 2>&1; then
  if gitleaks detect --no-banner -q 2>/dev/null; then echo "  gitleaks: CLEAN (tree + history)"
  else echo "  gitleaks: FINDINGS — run 'gitleaks detect --no-banner' for detail"; flag; fi
elif command -v trufflehog >/dev/null 2>&1; then
  echo "  trufflehog present — run: trufflehog git file://. --only-verified"
else
  echo "  (no gitleaks/trufflehog installed — pattern fallback only; install one for real coverage)"
fi
# tracked secret-bearing filenames
hits=$(git ls-files | grep -iE '(^|/)\.env($|\.)|\.pem$|\.key$|(^|/)id_rsa$|(^|/)id_ed25519$|\.p12$|\.pfx$|\.credentials\.json$|(^|/)credentials\.json$' || true)
if [ -n "$hits" ]; then echo "  TRACKED secret-type files:"; printf '    %s\n' $hits; flag
else echo "  no secret-type filenames tracked"; fi
# high-signal inline secret patterns in tracked text
inline=$(git grep -nIE '(AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|ghp_[A-Za-z0-9]{36}|xox[baprs]-[A-Za-z0-9-]+|AIza[0-9A-Za-z_-]{35})' -- . ':(exclude)*.md' 2>/dev/null | head -10 || true)
if [ -n "$inline" ]; then echo "  INLINE secret patterns:"; printf '    %s\n' "$inline"; flag
else echo "  no high-signal inline secret patterns in tracked code"; fi

# --- 2. Privacy / PII / identity -----------------------------------------------
line; echo "2. PRIVACY / PII / IDENTITY"; line
home=$(git grep -nI -E '/(Users|home)/[a-zA-Z0-9._-]+' -- . ':(exclude)*.md' 2>/dev/null | grep -ivE 'suspect|example|/home/user|/Users/user|<|placeholder' | head -8 || true)
if [ -n "$home" ]; then echo "  possible real home paths (review):"; printf '    %s\n' "$home"; flag
else echo "  no obvious real home paths in tracked non-doc files"; fi
email=$(git config user.email 2>/dev/null || echo "")
case "$email" in
  *@*.local|*@*"$(hostname -s 2>/dev/null)"*) echo "  git email leaks hostname: $email  → use a GitHub noreply"; flag ;;
  "") echo "  (git user.email not set)" ;;
  *users.noreply.github.com) echo "  git email: $email (noreply ✓)" ;;
  *) echo "  git email: $email (review: is this meant to be public?)" ;;
esac
if git log --all --format='%ae %ce' 2>/dev/null | grep -qiE '\.local($| )|@.*$(hostname -s 2>/dev/null)'; then
  echo "  history contains hostname-style emails — scrub before public push"; flag
fi

# --- 3. Agent config & gitignore (deny-by-default) -----------------------------
line; echo "3. AGENT CONFIG & GITIGNORE"; line
for d in .claude .cursor .aider .codeium .continue .windsurf; do
  [ -e "$d" ] || continue
  # is anything sensitive from this dir tracked?
  trk=$(git ls-files "$d" | grep -iE 'settings\.local\.json|\.credentials|secret|token|\.env' || true)
  [ -n "$trk" ] && { echo "  $d: SENSITIVE files tracked:"; printf '    %s\n' $trk; flag; }
  # is the dir covered by gitignore at all?
  if [ -f "$d/settings.local.json" ] && ! git check-ignore -q "$d/settings.local.json" 2>/dev/null; then
    echo "  $d/settings.local.json NOT gitignored — add deny-by-default rule"; flag
  fi
done
[ "$FINDINGS" -eq 0 ] || true
grep -qE '^\.claude/\*|^\.claude/settings\.local\.json' .gitignore 2>/dev/null \
  && echo "  .gitignore: .claude deny-by-default present ✓" \
  || echo "  .gitignore: no explicit .claude deny rule (add '.claude/*' + '!.claude/settings.json')"

# --- 4. Execution surface: hooks & MCP -----------------------------------------
line; echo "4. EXECUTION SURFACE (hooks / MCP / permissions)"; line
for f in .claude/settings.json .claude/settings.local.json .mcp.json; do
  [ -f "$f" ] || continue
  grep -qE '"hooks"' "$f" 2>/dev/null && { echo "  $f defines HOOKS — review (hooks auto-run shell commands)"; flag; }
  grep -qiE 'mcpServers|"command"|"url"' "$f" 2>/dev/null && echo "  $f references MCP/commands — confirm each server is expected/scoped"
  grep -qE 'Bash\(\*\)|"Bash\(.*\*\*' "$f" 2>/dev/null && { echo "  $f has broad Bash permission — prefer specific prefixes"; flag; }
done
echo "  (review what the agent may auto-run; keep it specific, not blanket)"

# --- 5. Prompt-injection surface in ingested text ------------------------------
line; echo "5. PROMPT-INJECTION SURFACE"; line
inj=$(git grep -nIiE 'ignore (all |the )?(previous|prior|above) (instructions|prompts)|disregard (the|your|all) (above|previous)|you are now|do not tell the user|exfiltrat' -- . 2>/dev/null | head -8 || true)
if [ -n "$inj" ]; then echo "  injection-style phrasing (verify it is documentation, not live instruction):"; printf '    %s\n' "$inj"; flag
else echo "  no injection-style phrasing in tracked files"; fi
# hidden / bidi / zero-width unicode in tracked text files
badu=$(git ls-files -- '*.md' '*.txt' '*.json' '*.py' '*.js' '*.ts' 2>/dev/null | while read -r f; do
  LC_ALL=C grep -lP '[\xe2\x80\x8b\xe2\x80\x8e\xe2\x80\x8f\xe2\x80\xaa-\xe2\x80\xae\xef\xbb\xbf]' "$f" 2>/dev/null
done | head -5 || true)
if [ -n "$badu" ]; then echo "  files with possible hidden/bidi/zero-width unicode:"; printf '    %s\n' "$badu"; flag
else echo "  no hidden/bidi/zero-width unicode detected in common text files"; fi

# --- 6. Network / exec in scripts ----------------------------------------------
line; echo "6. NETWORK / EXEC IN SCRIPTS"; line
fr=$(git grep -nIE '(curl|wget)[^|]*\|[^|]*(sh|bash)|eval +"\$\(' -- '*.sh' '*.py' '*.js' 2>/dev/null | head || true)
if [ -n "$fr" ]; then echo "  fetch-and-run / eval-of-output patterns:"; printf '    %s\n' "$fr"; flag
else echo "  no fetch-and-run / eval-of-output patterns"; fi

# --- Verdict -------------------------------------------------------------------
echo ""; line
if [ "$FINDINGS" -eq 0 ]; then
  echo "VERDICT: ✅ GO — no blocking findings. Re-run after config changes."
  exit 0
else
  echo "VERDICT: ⚠️  $FINDINGS area(s) flagged. Triage above; any LIVE secret is a"
  echo "hard NO-GO (rotate, then purge history). Re-run after remediation."
  exit 1
fi
