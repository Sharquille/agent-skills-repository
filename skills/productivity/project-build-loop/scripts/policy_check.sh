#!/usr/bin/env bash
# policy_check.sh — fail-closed pre-action gate for the project-build-loop
# conductor. Given the project tier and a requested action (with the capability
# flags it introduces and the authorization/isolation state), decide allow/block
# per references/dual-use-rating.md. Exit: 0 allow, 1 block, 2 usage.
#
# Usage:
#   policy_check.sh --action <tooling|git-remote|consult|publish> \
#     [--tier T0..T4] [--project <dir>] [--flags a,b,c] \
#     [--authorized yes|no] [--scoped yes|no] [--isolated yes|no] \
#     [--approval yes|no] [--consult-kind planning|artifact] [--publish-policy <p>]
#
# Tier resolves from --tier, else from <project>/project.json. Unknown/missing
# tier => treated as T3 (restrictive). An unconfirmed classification.status in
# project.json is also treated as unresolved => at least T3. Reclassification
# flags raise the effective tier: credential_material / production_target /
# third_party_target => T4; active_scan / mitm_proxy / traffic_decryption /
# exploit_poc / malware_sample => T3. --approval yes attests that a human
# approved AND a secret scan passed; git-remote and publish fail closed without it.

set -uo pipefail

ACTION=""; TIER=""; PROJECT=""; FLAGS=""; AUTHZ=""; ISO=""; PUBPOL=""; TIER_CLI=""
SCOPED=""; APPROVAL=""; CONSULT_KIND=""

die() { echo "error: $*" >&2; exit 2; }
block() { echo "BLOCK ($ACTION): $*" >&2; exit 1; }
allow() { echo "ALLOW ($ACTION): $*"; exit 0; }

# need_val "$@": guard a value-taking flag. Missing value would leave $1
# unchanged and spin the loop forever (shift 2 fails silently when $# < 2); a
# value that looks like another option (-*) means the flag's argument was
# omitted and the next flag got swallowed. Reject both.
need_val() {
  [ "$#" -ge 2 ] || die "$1 needs a value"
  case "$2" in -*|"") die "$1 needs a non-option value (got: '${2:-}')" ;; esac
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --action) need_val "$@"; ACTION="$2"; shift 2 ;;
    --tier) need_val "$@"; TIER="$2"; TIER_CLI=1; shift 2 ;;
    --project) need_val "$@"; PROJECT="$2"; shift 2 ;;
    --flags) need_val "$@"; FLAGS="$2"; shift 2 ;;
    --authorized) need_val "$@"; AUTHZ="$2"; shift 2 ;;
    --isolated) need_val "$@"; ISO="$2"; shift 2 ;;
    --scoped) need_val "$@"; SCOPED="$2"; shift 2 ;;
    --approval) need_val "$@"; APPROVAL="$2"; shift 2 ;;
    --consult-kind) need_val "$@"; CONSULT_KIND="$2"; shift 2 ;;
    --publish-policy) need_val "$@"; PUBPOL="$2"; shift 2 ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

[ -n "$ACTION" ] || die "--action is required"

# Resolve tier/policy from project.json if not given (crude but dependency-free).
PJSON=""
if [ -n "$PROJECT" ] && [ -f "$PROJECT/project.json" ]; then
  PJSON="$PROJECT/project.json"
fi
if [ -z "$TIER" ] && [ -n "$PJSON" ]; then
  TIER=$(grep -oE '"dual_use_tier"[[:space:]]*:[[:space:]]*"T[0-4]"' "$PJSON" \
         | grep -oE 'T[0-4]' | head -1)
fi
case "$TIER" in T0|T1|T2|T3|T4) : ;; *) TIER="T3" ;; esac   # unknown => restrictive

# Unconfirmed classification is treated as unresolved => enforce the higher tier
# (dual-use-rating.md: "while unresolved, enforce the higher tier"). Only an
# explicit --tier on the CLI is trusted to bypass this project-file check.
if [ -n "$PJSON" ] && [ -z "${TIER_CLI:-}" ]; then
  CLSTATUS=$(grep -oE '"status"[[:space:]]*:[[:space:]]*"(provisional|confirmed|review_required)"' "$PJSON" \
             | grep -oE '(provisional|confirmed|review_required)' | head -1)
  case "$CLSTATUS" in
    confirmed) : ;;
    *) # provisional, review_required, or unreadable => restrict to at least T3
       case "$TIER" in T0|T1|T2) echo "note: classification not confirmed (${CLSTATUS:-missing}) => enforcing T3" >&2; TIER="T3" ;; esac ;;
  esac
fi

# Read publish_policy from the project file when the caller did not pass one.
if [ -z "$PUBPOL" ] && [ -n "$PJSON" ]; then
  PUBPOL=$(grep -oE '"publish_policy"[[:space:]]*:[[:space:]]*"[a-zA-Z0-9_-]+"' "$PJSON" \
           | sed -E 's/.*"([a-zA-Z0-9_-]+)"$/\1/' | head -1)
fi

# Reclassification: high-risk flags force a tier floor, mirroring the
# dual-use-rating.md decision tree (first match wins, top-down). Fail closed:
# if a flag is present we assume the worst-case context the tree names for it.
#   T4 set: credential_material (theft vs real account), production_target /
#           third_party_target (exploitation) — the tree puts these at T4.
#   T3 set: active_scan (live host), mitm_proxy, traffic_decryption,
#           exploit_poc, malware_sample.
# packet_capture is deliberately NOT here: the tree rates it T1-T2 (bounded lab),
# so it triggers a conductor re-classification, not an automatic tier bump.
case ",$FLAGS," in
  *,credential_material,*|*,production_target,*|*,third_party_target,*)
    case "$TIER" in T0|T1|T2|T3) echo "note: high-risk flag raises effective tier to T4" >&2; TIER="T4" ;; esac ;;
  *,active_scan,*|*,mitm_proxy,*|*,traffic_decryption,*|*,exploit_poc,*|*,malware_sample,*)
    case "$TIER" in T0|T1|T2) echo "note: high-risk flag raises effective tier to T3" >&2; TIER="T3" ;; esac ;;
esac

tier_ge() { # tier_ge A B  -> true if A >= B numerically
  local a="${1#T}" b="${2#T}"; [ "$a" -ge "$b" ]; }

case "$ACTION" in
  tooling)
    if [ "$TIER" = "T4" ]; then block "T4 blocks active execution/tooling (planning/analysis only)"; fi
    if tier_ge "$TIER" T3; then
      # policy: authorized + scoped + isolation proof before offensive tooling
      [ "$AUTHZ" = "yes" ] || block "$TIER tooling requires --authorized yes (authorization gate)"
      [ "$SCOPED" = "yes" ] || block "$TIER tooling requires --scoped yes (scope defined + agreed)"
      [ "$ISO" = "yes" ]   || block "$TIER tooling requires --isolated yes (isolation proof)"
      allow "$TIER offensive tooling permitted (authorized + scoped + isolated)"
    fi
    if [ "$TIER" = "T2" ]; then
      [ "$AUTHZ" = "yes" ] && [ "$ISO" = "yes" ] || block "T2 tooling requires authorization + isolation re-check"
    fi
    allow "$TIER tooling permitted" ;;
  git-remote)
    # Every tier that can push at all requires human approval AND a clean
    # secret scan first; --approval yes is the conductor's attestation that both
    # (approval + a passed secret_scan) happened. Fail closed without it.
    case "$TIER" in
      T0|T1) [ "$APPROVAL" = "yes" ] && allow "T0/T1: remote permitted (secret-scan + approval attested)" \
                                     || block "T0/T1 remote needs --approval yes (secret-scan passed + human approval)" ;;
      T2) { [ "$AUTHZ" = "yes" ] && [ "$APPROVAL" = "yes" ]; } && allow "T2: private/sanitized remote (authorized + approved)" \
                                     || block "T2 remote needs --authorized yes and --approval yes" ;;
      T3) block "T3 defaults to no remote (documented exception required)" ;;
      T4) block "T4 blocks remote git" ;;
    esac ;;
  consult)
    # T4 permits planning/safe-analysis consults but never artifact egress.
    if [ "$TIER" = "T4" ]; then
      [ "$CONSULT_KIND" = "planning" ] && allow "T4: planning/safe-analysis consult only (no artifacts)" \
                                       || block "T4: only --consult-kind planning permitted; no artifact consult"
    fi
    tier_ge "$TIER" T3 && allow "T3: security-review consult required; send allowlisted sanitized artifacts only"
    tier_ge "$TIER" T2 && allow "T2: consult permitted with a redaction manifest"
    allow "consult permitted (advisory; redact as needed)" ;;
  publish)
    case "${PUBPOL:-}" in no-publish) block "publish_policy=no-publish" ;; esac
    case "$TIER" in
      T0|T1) [ "$APPROVAL" = "yes" ] && allow "T0/T1: publish (secret-scan + approval attested)" \
                                     || block "T0/T1 publish needs --approval yes (secret-scan passed + human approval)" ;;
      T2) [ "$APPROVAL" = "yes" ] && allow "T2: publish DEFENSIVE/TROUBLESHOOTING narrative only (redaction manifest + review attested)" \
                                  || block "T2 publish needs --approval yes (redaction manifest + review)" ;;
      T3) [ "$APPROVAL" = "yes" ] && allow "T3 publish EXCEPTION: security review + manual approval + redaction diff + manifest attested" \
                                  || block "T3 defaults to no-publish; exception needs --approval yes (security review + redaction diff + manifest)" ;;
      T4) block "T4 never publishes" ;;
    esac ;;
  *) die "unknown --action: $ACTION (tooling|git-remote|consult|publish)" ;;
esac
