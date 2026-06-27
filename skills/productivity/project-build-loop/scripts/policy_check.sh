#!/usr/bin/env bash
# policy_check.sh — fail-closed pre-action gate for the project-build-loop
# conductor. Given the project tier and a requested action (with the capability
# flags it introduces and the authorization/isolation state), decide allow/block
# per references/dual-use-rating.md. Exit: 0 allow, 1 block, 2 usage.
#
# Usage:
#   policy_check.sh --action <tooling|git-remote|consult|publish> \
#     [--tier T0..T4] [--project <dir>] [--flags a,b,c] \
#     [--authorized yes|no] [--isolated yes|no] [--publish-policy <p>]
#
# Tier resolves from --tier, else from <project>/project.json. Unknown/missing
# tier => treated as T3 (restrictive). Reclassification-triggering flags raise
# the effective tier to at least T3.

set -uo pipefail

ACTION=""; TIER=""; PROJECT=""; FLAGS=""; AUTHZ=""; ISO=""; PUBPOL=""

die() { echo "error: $*" >&2; exit 2; }
block() { echo "BLOCK ($ACTION): $*" >&2; exit 1; }
allow() { echo "ALLOW ($ACTION): $*"; exit 0; }

while [ "$#" -gt 0 ]; do
  case "$1" in
    --action) ACTION="${2:-}"; shift 2 ;;
    --tier) TIER="${2:-}"; shift 2 ;;
    --project) PROJECT="${2:-}"; shift 2 ;;
    --flags) FLAGS="${2:-}"; shift 2 ;;
    --authorized) AUTHZ="${2:-}"; shift 2 ;;
    --isolated) ISO="${2:-}"; shift 2 ;;
    --publish-policy) PUBPOL="${2:-}"; shift 2 ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

[ -n "$ACTION" ] || die "--action is required"

# Resolve tier from project.json if not given (crude but dependency-free).
if [ -z "$TIER" ] && [ -n "$PROJECT" ] && [ -f "$PROJECT/project.json" ]; then
  TIER=$(grep -oE '"dual_use_tier"[[:space:]]*:[[:space:]]*"T[0-4]"' "$PROJECT/project.json" \
         | grep -oE 'T[0-4]' | head -1)
fi
case "$TIER" in T0|T1|T2|T3|T4) : ;; *) TIER="T3" ;; esac   # unknown => restrictive

# Reclassification: high-risk flags force at least T3.
case ",$FLAGS," in
  *,mitm_proxy,*|*,traffic_decryption,*|*,exploit_poc,*|*,malware_sample,*|*,production_target,*|*,third_party_target,*)
    case "$TIER" in T0|T1|T2) echo "note: high-risk flag raises effective tier to T3" >&2; TIER="T3" ;; esac ;;
esac

tier_ge() { # tier_ge A B  -> true if A >= B numerically
  local a="${1#T}" b="${2#T}"; [ "$a" -ge "$b" ]; }

case "$ACTION" in
  tooling)
    if tier_ge "$TIER" T3; then
      [ "$AUTHZ" = "yes" ] || block "$TIER tooling requires --authorized yes (authorization gate)"
      [ "$ISO" = "yes" ]   || block "$TIER tooling requires --isolated yes (isolation proof)"
      [ "$TIER" = "T4" ] && block "T4 blocks active execution/tooling (planning/analysis only)"
      allow "$TIER offensive tooling permitted (authorized + isolated)"
    fi
    if [ "$TIER" = "T2" ]; then
      [ "$AUTHZ" = "yes" ] && [ "$ISO" = "yes" ] || block "T2 tooling requires authorization + isolation re-check"
    fi
    allow "$TIER tooling permitted" ;;
  git-remote)
    case "$TIER" in
      T0|T1) allow "remote permitted after secret-scan + approval" ;;
      T2) [ "$AUTHZ" = "yes" ] && allow "T2: private/sanitized remote with explicit approval" || block "T2 remote needs explicit approval" ;;
      T3) block "T3 defaults to no remote (documented exception required)" ;;
      T4) block "T4 blocks remote git" ;;
    esac ;;
  consult)
    tier_ge "$TIER" T4 && block "T4: planning/safe-analysis only; no artifact consult"
    tier_ge "$TIER" T3 && allow "T3: security-review consult required; send allowlisted sanitized artifacts only"
    tier_ge "$TIER" T2 && allow "T2: consult permitted with a redaction manifest"
    allow "consult permitted (advisory; redact as needed)" ;;
  publish)
    case "${PUBPOL:-}" in no-publish) block "publish_policy=no-publish" ;; esac
    case "$TIER" in
      T0|T1) allow "publish after secret-scan + approval" ;;
      T2) allow "publish DEFENSIVE/TROUBLESHOOTING narrative only (redaction manifest + review)" ;;
      T3) block "T3 defaults to no-publish; exception = security review + manual approval + redaction diff + manifest" ;;
      T4) block "T4 never publishes" ;;
    esac ;;
  *) die "unknown --action: $ACTION (tooling|git-remote|consult|publish)" ;;
esac
