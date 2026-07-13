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
#     [--approval yes|no] [--consult-kind planning|artifact] [--publish-policy <p>] \
#     [--artifact <file>] [--redaction-manifest <file>] \
#     [--security-review yes|no] [--remote-visibility private|public] \
#     [--receipt <project-dir>]
#
# Tier resolves from exactly one source: --tier for standalone checks, or the
# structurally validated classification in <project>/project.json. Supplying
# both is rejected so a project classification cannot be downgraded by CLI.
# Unknown standalone tiers are treated as T3 (restrictive). An unconfirmed
# project classification is also treated as unresolved => at least T3.
# Reclassification flags raise the effective tier: credential_material / production_target /
# third_party_target => T4; active_scan / mitm_proxy / traffic_decryption /
# exploit_poc / malware_sample => T3. --approval yes attests that a human
# approved AND a secret scan passed; git-remote and publish fail closed without it.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ACTION=""; TIER=""; PROJECT=""; FLAGS=""; AUTHZ=""; ISO=""; PUBPOL=""; TIER_CLI=""
SCOPED=""; APPROVAL=""; CONSULT_KIND=""
RECEIPT=""; MODEL=""; ARTIFACT=""; PROMPT_HASH=""
PUBPOL_CLI=""; REDACTION_MANIFEST=""; SECURITY_REVIEW=""
REMOTE_VISIBILITY=""

die() { echo "error: $*" >&2; exit 2; }

sha256_of() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
  else python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$1"; fi
}

canonical_path() {
  python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$1"
}

# Audit receipt appended via append_event.sh: mandatory and automatic for a
# project-backed gate, optional for standalone checks. Any configured receipt is
# mandatory for an allow decision. Blocks stay blocked if recording still fails.
write_receipt() {
  local decision="$1"
  [ -n "$RECEIPT" ] || return 0
  local args=(--project "$RECEIPT" --event gate --field gate=policy_check \
              --field action="$ACTION" --field tier="$TIER" --field decision="$decision")
  [ -n "$MODEL" ] && args+=(--field model="$MODEL")
  [ -n "$PROMPT_HASH" ] && args+=(--field prompt_sha256="$PROMPT_HASH")
  [ -n "$CONSULT_KIND" ] && args+=(--field consult_kind="$CONSULT_KIND")
  [ -n "$SECURITY_REVIEW" ] && args+=(--field security_review="$SECURITY_REVIEW")
  [ -n "$REMOTE_VISIBILITY" ] && args+=(--field remote_visibility="$REMOTE_VISIBILITY")
  if [ -n "$ARTIFACT" ]; then
    if [ -f "$ARTIFACT" ] && _h=$(sha256_of "$ARTIFACT" 2>/dev/null) && [ -n "$_h" ]; then
      args+=(--field artifact_sha256="$_h")
    else
      echo "warn: gate artifact hash not recorded: $ARTIFACT" >&2
      [ "$decision" = "block" ] || return 1
      args+=(--field artifact_hash_error="could not hash supplied artifact")
    fi
  fi
  if [ -n "$REDACTION_MANIFEST" ]; then
    if [ -f "$REDACTION_MANIFEST" ] && _rh=$(sha256_of "$REDACTION_MANIFEST" 2>/dev/null) && [ -n "$_rh" ]; then
      args+=(--field redaction_manifest_sha256="$_rh")
    else
      echo "warn: gate redaction manifest hash not recorded: $REDACTION_MANIFEST" >&2
      [ "$decision" = "block" ] || return 1
      args+=(--field redaction_manifest_hash_error="could not hash supplied redaction manifest")
    fi
  fi
  if ! "$SCRIPT_DIR/append_event.sh" "${args[@]}" >/dev/null 2>&1; then
    echo "warn: gate receipt not recorded" >&2
    return 1
  fi
}

block() { write_receipt block || true; echo "BLOCK ($ACTION): $*" >&2; exit 1; }
allow() {
  if ! write_receipt allow; then
    echo "BLOCK ($ACTION): requested audit receipt (including required proof hashes) could not be recorded" >&2
    exit 1
  fi
  echo "ALLOW ($ACTION): $*"
  exit 0
}

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
    --publish-policy) need_val "$@"; PUBPOL="$2"; PUBPOL_CLI=1; shift 2 ;;
    --receipt) need_val "$@"; RECEIPT="$2"; shift 2 ;;
    --model) need_val "$@"; MODEL="$2"; shift 2 ;;
    --artifact) need_val "$@"; ARTIFACT="$2"; shift 2 ;;
    --redaction-manifest) need_val "$@"; REDACTION_MANIFEST="$2"; shift 2 ;;
    --security-review) need_val "$@"; SECURITY_REVIEW="$2"; shift 2 ;;
    --remote-visibility) need_val "$@"; REMOTE_VISIBILITY="$2"; shift 2 ;;
    --prompt-hash) need_val "$@"; PROMPT_HASH="$2"; shift 2 ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
done

[ -n "$ACTION" ] || die "--action is required"

# Every project-backed decision writes its receipt to that same project. Resolve
# both paths canonically so alternate spellings/symlinks cannot redirect the
# audit record. A mismatched explicit target is rejected and recorded against
# the project, never against the caller-supplied directory.
if [ -n "$PROJECT" ]; then
  if ! PROJECT_CANON=$(canonical_path "$PROJECT" 2>/dev/null) || [ -z "$PROJECT_CANON" ]; then
    die "cannot resolve --project path: $PROJECT"
  fi
  if [ -n "$RECEIPT" ]; then
    RECEIPT_ARG="$RECEIPT"
    if ! RECEIPT_CANON=$(canonical_path "$RECEIPT_ARG" 2>/dev/null) || [ -z "$RECEIPT_CANON" ]; then
      RECEIPT="$PROJECT_CANON"
      TIER="unresolved"
      block "cannot resolve --receipt path: $RECEIPT_ARG"
    fi
    RECEIPT="$PROJECT_CANON"
    if [ "$RECEIPT_CANON" != "$PROJECT_CANON" ]; then
      TIER="unresolved"
      block "--receipt must resolve to the same project as --project"
    fi
  else
    RECEIPT="$PROJECT_CANON"
  fi
  PROJECT="$PROJECT_CANON"

  # Project-backed decisions have one authoritative classification source.
  if [ -n "$TIER_CLI" ] || [ -n "$PUBPOL_CLI" ]; then
    TIER="unresolved"
    block "--project cannot be combined with --tier or --publish-policy; project.json classification is authoritative"
  fi
fi

# Resolve project policy structurally. Validate every classification field used
# by this gate so malformed or ambiguous state cannot reach an allow path.
PJSON=""
CLSTATUS=""
PROJECT_FLAGS=""
PROJECT_GITPOL=""
if [ -n "$PROJECT" ]; then
  PJSON="$PROJECT/project.json"
  [ -f "$PJSON" ] || { TIER="unresolved"; block "project.json not found: $PJSON"; }
  if ! python3 "$SCRIPT_DIR/validate_state.py" project "$PJSON" >/dev/null 2>&1; then
    TIER="unresolved"
    block "project.json does not satisfy the current project schema"
  fi
  if ! PROJECT_POLICY=$(python3 - "$PJSON" <<'PY'
import json
import sys

path = sys.argv[1]

def reject_duplicates(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError(f"duplicate key: {key}")
        obj[key] = value
    return obj

def fail(message):
    print(f"error: invalid project classification: {message}", file=sys.stderr)
    raise SystemExit(1)

try:
    with open(path, encoding="utf-8") as handle:
        project = json.load(handle, object_pairs_hook=reject_duplicates)
except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
    fail(str(exc))

if not isinstance(project, dict):
    fail("project.json top level must be an object")
if project.get("schema_version") != "1.1":
    fail("schema_version must be the current project schema '1.1'")
classification = project.get("classification")
if not isinstance(classification, dict):
    fail("classification must be an object")
if classification.get("policy_version") != "1.0":
    fail("classification.policy_version must be the current policy '1.0'")

required = {
    "status": {"provisional", "confirmed", "review_required"},
    "dual_use_tier": {"T0", "T1", "T2", "T3", "T4"},
    "publish_policy": {"no-publish", "defensive-only", "sanitized-only", "publishable"},
    "git_policy": {"local-only", "private-remote", "public-remote"},
}
values = []
for key, allowed in required.items():
    value = classification.get(key)
    if not isinstance(value, str) or value not in allowed:
        fail(f"classification.{key} is missing or invalid")
    values.append(value)

known_flags = {
    "passive_recon", "active_scan", "packet_capture", "traffic_decryption",
    "mitm_proxy", "exploit_poc", "malware_sample", "credential_material",
    "production_target", "third_party_target", "internet_egress",
}
flags = classification.get("capability_flags")
if not isinstance(flags, list):
    fail("classification.capability_flags must be a list")
if any(not isinstance(flag, str) or flag not in known_flags for flag in flags):
    fail("classification.capability_flags contains an unknown or invalid value")
if len(flags) != len(set(flags)):
    fail("classification.capability_flags contains duplicates")

print("\t".join(values + [",".join(flags)]))
PY
  ); then
    TIER="unresolved"
    block "project.json classification is malformed or incomplete"
  fi
  IFS=$'\t' read -r CLSTATUS TIER PROJECT_PUBPOL PROJECT_GITPOL PROJECT_FLAGS <<< "$PROJECT_POLICY"
  [ -n "$PUBPOL" ] || PUBPOL="$PROJECT_PUBPOL"

  # dual-use-rating.md: while unresolved, enforce the higher tier.
  case "$CLSTATUS" in
    confirmed) : ;;
    *) case "$TIER" in
         T0|T1|T2)
           echo "note: classification not confirmed ($CLSTATUS) => enforcing T3" >&2
           TIER="T3"
           ;;
       esac ;;
  esac
else
  case "$TIER" in T0|T1|T2|T3|T4) : ;; *) TIER="T3" ;; esac   # unknown => restrictive
fi

# Merge authoritative project flags with any action-specific CLI flags. Both
# sources use the controlled enum from dual-use-rating.md; unknown spellings or
# malformed comma lists block instead of silently bypassing a tier floor.
CLI_FLAGS="$FLAGS"
FLAGS=""
add_capability_flag() {
  local flag="$1"
  case "$flag" in
    passive_recon|active_scan|packet_capture|traffic_decryption|mitm_proxy|exploit_poc|malware_sample|credential_material|production_target|third_party_target|internet_egress) : ;;
    *) block "unknown capability flag: ${flag:-<empty>}" ;;
  esac
  case ",$FLAGS," in
    *",$flag,"*) : ;;
    *) FLAGS="${FLAGS:+$FLAGS,}$flag" ;;
  esac
}

if [ -n "$PROJECT_FLAGS" ]; then
  IFS=',' read -r -a _project_flag_items <<< "$PROJECT_FLAGS"
  for _flag in "${_project_flag_items[@]}"; do add_capability_flag "$_flag"; done
fi
if [ -n "$CLI_FLAGS" ]; then
  case "$CLI_FLAGS" in ,*|*,|*,,*) block "--flags must be a comma-separated list without empty values" ;; esac
  IFS=',' read -r -a _cli_flag_items <<< "$CLI_FLAGS"
  for _flag in "${_cli_flag_items[@]}"; do add_capability_flag "$_flag"; done
fi
case "$SECURITY_REVIEW" in
  ""|yes|no) : ;;
  *) block "--security-review must be yes or no" ;;
esac
case "$REMOTE_VISIBILITY" in
  ""|private|public) : ;;
  *) block "--remote-visibility must be private or public" ;;
esac

require_redaction_manifest() {
  local context="$1" manifest_hash
  [ -n "$REDACTION_MANIFEST" ] && [ -f "$REDACTION_MANIFEST" ] \
    && [ -s "$REDACTION_MANIFEST" ] \
    || block "$context needs an existing, non-empty --redaction-manifest file"
  manifest_hash=$(sha256_of "$REDACTION_MANIFEST" 2>/dev/null) \
    && [ -n "$manifest_hash" ] \
    || block "$context needs a readable, hashable --redaction-manifest file"
}

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
    if [ -n "$PROJECT" ]; then
      case "$PROJECT_GITPOL" in
        local-only)
          block "classification.git_policy=local-only"
          ;;
        private-remote)
          [ "$REMOTE_VISIBILITY" = "private" ] \
            || block "classification.git_policy=private-remote requires --remote-visibility private"
          ;;
        public-remote)
          [ -n "$REMOTE_VISIBILITY" ] \
            || block "classification.git_policy=public-remote requires --remote-visibility private|public"
          ;;
      esac
    fi
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
    case "$CONSULT_KIND" in
      planning)
        [ -z "$ARTIFACT" ] || block "planning consult rejects --artifact payloads"
        [ -z "$REDACTION_MANIFEST" ] || block "planning consult rejects --redaction-manifest payloads"
        if [ "$TIER" = "T3" ]; then
          [ "$SECURITY_REVIEW" = "yes" ] \
            || block "T3 planning consult requires --security-review yes"
        fi
        allow "$TIER planning/safe-analysis consult permitted (no artifact payloads)"
        ;;
      artifact)
        [ -n "$ARTIFACT" ] && [ -f "$ARTIFACT" ] \
          || block "artifact consult requires an existing --artifact file"
        [ "$TIER" != "T4" ] || block "T4 blocks artifact consults; planning only"
        if tier_ge "$TIER" T2; then
          require_redaction_manifest "$TIER artifact consult"
        fi
        if tier_ge "$TIER" T3; then
          [ "$SECURITY_REVIEW" = "yes" ] \
            || block "$TIER artifact consult requires --security-review yes"
          allow "$TIER artifact consult permitted (sanitized artifact + manifest + security review attested)"
        fi
        if tier_ge "$TIER" T2; then
          allow "$TIER artifact consult permitted (sanitized artifact + redaction manifest)"
        fi
        allow "$TIER artifact consult permitted"
        ;;
      *) block "consult requires explicit --consult-kind planning|artifact" ;;
    esac ;;
  publish)
    case "${PUBPOL:-}" in
      no-publish) block "publish_policy=no-publish" ;;
      sanitized-only) require_redaction_manifest "publish_policy=sanitized-only" ;;
      ""|defensive-only|publishable) : ;;
      *) block "unknown publish policy: $PUBPOL" ;;
    esac
    case "$TIER" in
      T0|T1) [ "$APPROVAL" = "yes" ] && allow "T0/T1: publish (secret-scan + approval attested)" \
                                     || block "T0/T1 publish needs --approval yes (secret-scan passed + human approval)" ;;
      T2)
        [ "$APPROVAL" = "yes" ] \
          || block "T2 publish needs --approval yes (secret scan + human review)"
        require_redaction_manifest "T2 publish"
        allow "T2: publish DEFENSIVE/TROUBLESHOOTING narrative only (approval + redaction manifest attested)"
        ;;
      T3)
        [ "$APPROVAL" = "yes" ] \
          || block "T3 publish exception needs --approval yes"
        require_redaction_manifest "T3 publish exception"
        [ "$SECURITY_REVIEW" = "yes" ] \
          || block "T3 publish exception needs --security-review yes"
        allow "T3 publish EXCEPTION: security review + manual approval + redaction manifest attested"
        ;;
      T4) block "T4 never publishes" ;;
    esac ;;
  *)
    if [ -n "$PROJECT" ]; then
      block "unknown --action: $ACTION (tooling|git-remote|consult|publish)"
    fi
    die "unknown --action: $ACTION (tooling|git-remote|consult|publish)"
    ;;
esac
