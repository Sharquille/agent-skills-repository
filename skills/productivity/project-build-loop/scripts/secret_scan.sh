#!/usr/bin/env bash
# secret_scan.sh — fail-closed secret/PII gate. Run before staging, committing,
# consulting, and publishing. Scans given paths (or staged git diff) for secret
# patterns always, and for non-documentation IPv4 in --publish mode. Does NOT
# detect IPv6/hostnames/EXIF/timestamps — those stay manual-review items.
# A missing/unreadable scan target is a finding (fail closed).
# Exit: 0 clean, 1 findings, 2 usage.
#
# Usage:
#   secret_scan.sh <path> [<path> ...]     # scan files/dirs
#   secret_scan.sh --staged                # scan `git diff --cached`
#   secret_scan.sh --publish <dir>         # stricter: also flag real IPs/hosts

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MODE="paths"
STRICT=0
RECEIPT=""
PATHS=()

while [ "$#" -gt 0 ]; do
  case "$1" in
    --staged) MODE="staged"; shift ;;
    --publish) MODE="paths"; STRICT=1; shift ;;
    --receipt) shift; [ "$#" -ge 1 ] || { echo "error: --receipt needs a value" >&2; exit 2; }; RECEIPT="$1"; shift ;;
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

# Read a file into a variable, failing closed if it cannot be read.
read_file() { # sets REPLYTEXT; returns nonzero on failure
  [ -r "$1" ] || return 1
  REPLYTEXT=$(cat -- "$1" 2>/dev/null) || return 1
  return 0
}

if [ "$MODE" = "staged" ]; then
  command -v git >/dev/null 2>&1 || { echo "error: git not found" >&2; exit 2; }
  # Fail closed: if git cannot produce the staged diff, do not report "clean".
  if ! staged=$(git diff --cached 2>&1); then
    echo "ERROR: could not read staged diff (git failed): $staged" >&2
    exit 2
  fi
  scan_text "git staged diff" "$staged"
else
  [ "${#PATHS[@]}" -gt 0 ] || { echo "error: no paths given" >&2; exit 2; }
  for p in "${PATHS[@]}"; do
    if [ -d "$p" ]; then
      while IFS= read -r f; do
        if read_file "$f"; then
          scan_text "$f" "$REPLYTEXT"
        else
          echo "ERROR: unreadable file in scan target (fail closed): $f" >&2
          rc=1
        fi
      done < <(find "$p" -type f ! -path '*/.git/*' 2>/dev/null)
    elif [ -f "$p" ]; then
      if read_file "$p"; then
        scan_text "$p" "$REPLYTEXT"
      else
        echo "ERROR: unreadable file (fail closed): $p" >&2
        rc=1
      fi
    else
      # Fail closed: a scan target that cannot be read must not pass silently.
      echo "ERROR: scan target not found or unreadable: $p" >&2
      rc=1
    fi
  done
fi

if [ "$rc" -eq 0 ]; then echo "secret_scan: clean"; else echo "secret_scan: FINDINGS (fail closed)" >&2; fi

# Optional audit receipt (best-effort; never changes rc).
if [ -n "$RECEIPT" ]; then
  decision=$([ "$rc" -eq 0 ] && echo clean || echo findings)
  scan_mode=$([ "$STRICT" -eq 1 ] && echo publish || echo "$MODE")
  "$SCRIPT_DIR/append_event.sh" --project "$RECEIPT" --event gate \
    --field gate=secret_scan --field mode="$scan_mode" --field decision="$decision" \
    >/dev/null 2>&1 || echo "warn: secret_scan receipt not recorded" >&2
fi

exit "$rc"
