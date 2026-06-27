#!/usr/bin/env bash
# secret_scan.sh — fail-closed secret/PII gate. Run before staging, committing,
# consulting, and publishing. Scans given paths (or staged git diff) for secret
# patterns and non-documentation IPs/hosts. Exit: 0 clean, 1 findings, 2 usage.
#
# Usage:
#   secret_scan.sh <path> [<path> ...]     # scan files/dirs
#   secret_scan.sh --staged                # scan `git diff --cached`
#   secret_scan.sh --publish <dir>         # stricter: also flag real IPs/hosts

set -uo pipefail

MODE="paths"
STRICT=0
PATHS=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --staged) MODE="staged"; shift ;;
    --publish) MODE="paths"; STRICT=1; shift ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    *) PATHS+=("$1"); shift ;;
  esac
done

# Secret signatures (high-confidence)
secret_re='BEGIN [A-Z ]*PRIVATE KEY|AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|github_pat_|gh[pousr]_[A-Za-z0-9_]{20,}|xox[baprs]-|sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{20,}|-----BEGIN|password[[:space:]]*[:=]|passwd[[:space:]]*[:=]|api[_-]?key[[:space:]]*[:=]|secret[[:space:]]*[:=]|token[[:space:]]*[:=]'

# Real (non-documentation) IPv4: flag any, then the caller whitelists RFC5737 doc ranges.
# Documentation ranges that are SAFE to publish: 192.0.2.x, 198.51.100.x, 203.0.113.x.
realip_re='\b(([0-9]{1,3})\.){3}[0-9]{1,3}\b'
docip_re='\b(192\.0\.2\.|198\.51\.100\.|203\.0\.113\.)'

rc=0

scan_text() {
  local label="$1" text="$2"
  local hits
  hits=$(printf '%s' "$text" | grep -EnI "$secret_re" 2>/dev/null | head -20 || true)
  if [ -n "$hits" ]; then
    echo "SECRET findings in $label:" >&2
    printf '%s\n' "$hits" | sed 's/^/  /' >&2
    rc=1
  fi
  if [ "$STRICT" -eq 1 ]; then
    local ips
    ips=$(printf '%s' "$text" | grep -EoI "$realip_re" 2>/dev/null | grep -Ev "$docip_re" \
          | grep -Ev '^(0\.|127\.|255\.|10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)' | sort -u | head -20 || true)
    if [ -n "$ips" ]; then
      echo "REAL-IP findings (publish mode) in $label — replace with RFC 5737 doc ranges:" >&2
      printf '%s\n' "$ips" | sed 's/^/  /' >&2
      rc=1
    fi
  fi
}

if [ "$MODE" = "staged" ]; then
  command -v git >/dev/null 2>&1 || { echo "error: git not found" >&2; exit 2; }
  scan_text "git staged diff" "$(git diff --cached 2>/dev/null)"
else
  [ "${#PATHS[@]}" -gt 0 ] || { echo "error: no paths given" >&2; exit 2; }
  for p in "${PATHS[@]}"; do
    if [ -d "$p" ]; then
      while IFS= read -r f; do
        scan_text "$f" "$(cat "$f" 2>/dev/null)"
      done < <(find "$p" -type f ! -path '*/.git/*' 2>/dev/null)
    elif [ -f "$p" ]; then
      scan_text "$p" "$(cat "$p" 2>/dev/null)"
    else
      echo "warn: not found: $p" >&2
    fi
  done
fi

if [ "$rc" -eq 0 ]; then echo "secret_scan: clean"; else echo "secret_scan: FINDINGS (fail closed)" >&2; fi
exit "$rc"
