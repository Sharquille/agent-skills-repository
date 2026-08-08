#!/usr/bin/env bash
set -euo pipefail

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$TEST_DIR/.." && pwd)"
SCRIPTS_DIR="$SKILL_DIR/scripts"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/agent-orchestra-tests.XXXXXX")"
trap 'rm -rf "$TMP_ROOT"' EXIT

passes=0

pass() {
  passes=$((passes + 1))
  printf 'ok %d - %s\n' "$passes" "$1"
}

fail() {
  printf 'not ok - %s\n' "$1" >&2
  exit 1
}

assert_contains() {
  local text="$1" expected="$2" label="$3"
  case "$text" in
    *"$expected"*) pass "$label" ;;
    *) printf '%s\n' "$text" >&2; fail "$label (missing: $expected)" ;;
  esac
}

assert_not_contains() {
  local text="$1" unexpected="$2" label="$3"
  case "$text" in
    *"$unexpected"*) printf '%s\n' "$text" >&2; fail "$label (unexpected: $unexpected)" ;;
    *) pass "$label" ;;
  esac
}

assert_status() {
  local actual="$1" expected="$2" label="$3"
  [ "$actual" -eq "$expected" ] && pass "$label" || fail "$label (expected $expected, got $actual)"
}

new_repo() {
  local repo="$1"
  mkdir -p "$repo/allowed" "$repo/allowed space"
  printf 'inside\n' >"$repo/allowed/in.txt"
  printf 'space\n' >"$repo/allowed space/in.txt"
  printf 'outside\n' >"$repo/outside.txt"
  git -C "$repo" init -q
  git -C "$repo" config user.name "Agent Orchestra Tests"
  git -C "$repo" config user.email "tests@example.invalid"
  git -C "$repo" add .
  git -C "$repo" commit -qm baseline
  git -C "$repo" switch -qc codex/test
}

# shellcheck source=../scripts/write-scope.sh
. "$SCRIPTS_DIR/write-scope.sh"

# --- Scope normalization and snapshot enforcement ---
normalized="$(orchestra_normalize_scope './allowed/')"
[ "$normalized" = "allowed" ] && pass "scope normalization removes harmless prefixes" || fail "scope normalization"
[ "$(orchestra_normalize_scope '.')" = "." ] && pass "whole-repository scope is explicit and reachable" || fail "whole-repository scope"

for unsafe in "/tmp/out" "../out" ".git/config" "src/.git/config" ".env" ".envrc" "config/prod.pem" "config/prod.jks" "src/*"; do
  if orchestra_normalize_scope "$unsafe" >/dev/null 2>&1; then
    fail "unsafe scope was accepted: $unsafe"
  fi
done
pass "unsafe, secret-shaped, and glob scopes are refused"

scope_repo="$TMP_ROOT/scope-repo"
new_repo "$scope_repo"
scope_state="$TMP_ROOT/scope-state"
orchestra_validate_scope_tree "$scope_repo" allowed || fail "valid scope tree was rejected"
orchestra_scope_snapshot_create "$scope_repo" "$scope_state" allowed || fail "scope snapshot failed"
printf 'changed\n' >>"$scope_repo/allowed/in.txt"
orchestra_scope_snapshot_verify "$scope_repo" "$scope_state" "during test" allowed >/dev/null 2>&1 || fail "in-scope tracked change was rejected"
pass "in-scope tracked changes pass"

printf 'changed\n' >>"$scope_repo/outside.txt"
if orchestra_scope_snapshot_verify "$scope_repo" "$scope_state" "during test" allowed >/dev/null 2>&1; then
  fail "out-of-scope tracked change was accepted"
fi
pass "out-of-scope tracked changes fail without rollback"

dirty_repo="$TMP_ROOT/dirty-repo"
new_repo "$dirty_repo"
printf 'user dirty baseline\n' >>"$dirty_repo/outside.txt"
dirty_state="$TMP_ROOT/dirty-state"
orchestra_scope_snapshot_create "$dirty_repo" "$dirty_state" allowed || fail "dirty baseline snapshot failed"
printf 'delegate\n' >>"$dirty_repo/allowed/in.txt"
orchestra_scope_snapshot_verify "$dirty_repo" "$dirty_state" "during test" allowed >/dev/null 2>&1 || fail "unchanged dirty baseline was rejected"
pass "pre-existing dirty work outside scope is preserved and tolerated"

git -C "$dirty_repo" add outside.txt
set +e
orchestra_scope_snapshot_verify "$dirty_repo" "$dirty_state" "during test" allowed >/dev/null 2>&1
staged_baseline_status=$?
set -e
assert_status "$staged_baseline_status" 1 "out-of-scope index changes are enforced"

ignored_repo="$TMP_ROOT/ignored-repo"
new_repo "$ignored_repo"
mkdir -p "$ignored_repo/cache"
printf 'cache/\n' >"$ignored_repo/.gitignore"
printf 'ignored\n' >"$ignored_repo/cache/state.bin"
git -C "$ignored_repo" add .gitignore && git -C "$ignored_repo" commit -qm ignore-cache
ignored_state="$TMP_ROOT/ignored-state"
orchestra_scope_snapshot_create "$ignored_repo" "$ignored_state" allowed || fail "ignored baseline snapshot failed"
printf 'changed\n' >>"$ignored_repo/cache/state.bin"
if orchestra_scope_snapshot_verify "$ignored_repo" "$ignored_state" "during test" allowed >/dev/null 2>&1; then
  fail "out-of-scope ignored change was accepted"
fi
pass "ignored files outside scope are enforced"

mkdir -p "$scope_repo/config"
printf 'secret\n' >"$scope_repo/config/.env"
if orchestra_validate_scope_tree "$scope_repo" config >/dev/null 2>&1; then
  fail "scope containing a secret descendant was accepted"
fi
pass "broad scopes containing secret-shaped descendants are refused"

external_dir="$TMP_ROOT/external"
mkdir -p "$external_dir"
ln -s "$external_dir" "$scope_repo/allowed/link"
if orchestra_validate_scope_tree "$scope_repo" allowed >/dev/null 2>&1; then
  fail "scope containing a symlink was accepted"
fi
pass "scoped symlinks are refused"

link_repo="$TMP_ROOT/link-repo"
new_repo "$link_repo"
ln -s "$external_dir" "$link_repo/outside-link"
if orchestra_validate_scope_tree "$link_repo" allowed >/dev/null 2>&1; then
  fail "external symlink outside scope was accepted"
fi
pass "external repository symlinks are refused regardless of scope"

directory_repo="$TMP_ROOT/directory-repo"
new_repo "$directory_repo"
directory_state="$TMP_ROOT/directory-state"
orchestra_scope_snapshot_create "$directory_repo" "$directory_state" allowed || fail "directory baseline snapshot failed"
mkdir "$directory_repo/outside-empty"
if orchestra_scope_snapshot_verify "$directory_repo" "$directory_state" "during test" allowed >/dev/null 2>&1; then
  fail "out-of-scope empty directory was accepted"
fi
pass "out-of-scope empty directories are enforced"

metadata_repo="$TMP_ROOT/metadata-repo"
new_repo "$metadata_repo"
metadata_state="$TMP_ROOT/metadata-state"
orchestra_scope_snapshot_create "$metadata_repo" "$metadata_state" allowed || fail "Git metadata baseline snapshot failed"
git -C "$metadata_repo" tag delegate-tag
if orchestra_scope_snapshot_verify "$metadata_repo" "$metadata_state" "during test" allowed >/dev/null 2>&1; then
  fail "Git ref change was accepted"
fi
pass "Git refs, config, and reflog state are enforced"

plan_record="$TMP_ROOT/plan-record.txt"
printf 'plan: P2\nstatus: accepted\nindependent-review: complete\nblocking-findings: resolved\n' >"$plan_record"
[ "$(orchestra_validate_plan_record "$plan_record")" = P2 ] || fail "valid plan record was rejected"
pass "accepted plan records are validated"

# --- Mocked passive doctor states ---
fake_bin="$TMP_ROOT/fake-bin"
fake_codex_home="$TMP_ROOT/codex-home"
mkdir -p "$fake_bin" "$fake_codex_home"
printf 'model = "gpt-5.6-sol"\nmodel_reasoning_effort = "high"\n' >"$fake_codex_home/config.toml"

cat >"$fake_bin/codex" <<'EOF'
#!/usr/bin/env bash
[ -n "${FAKE_CALL_LOG:-}" ] && printf 'codex %s\n' "$*" >>"$FAKE_CALL_LOG"
case "${1:-}" in
  --version)
    [ "${FAKE_CODEX_VERSION_STATUS:-0}" -eq 0 ] || exit "$FAKE_CODEX_VERSION_STATUS"
    echo "codex-cli test"
    ;;
  login) [ "${2:-}" = status ] && exit "${FAKE_CODEX_AUTH_STATUS:-0}" ;;
  exec)
    dir=""
    shift
    while [ "$#" -gt 0 ]; do
      case "$1" in
        --cd) dir="$2"; shift 2 ;;
        *) shift ;;
      esac
    done
    [ -n "${FAKE_WRITE_REL:-}" ] && printf 'delegate change\n' >>"$dir/$FAKE_WRITE_REL"
    if [ "${FAKE_COMMIT:-0}" -eq 1 ]; then
      git -C "$dir" add -A
      git -C "$dir" commit -qm delegate-commit
    fi
    exit "${FAKE_DELEGATE_STATUS:-0}"
    ;;
  *) exit 0 ;;
esac
EOF

cat >"$fake_bin/opencode" <<'EOF'
#!/usr/bin/env bash
[ -n "${FAKE_CALL_LOG:-}" ] && printf 'opencode %s\n' "$*" >>"$FAKE_CALL_LOG"
[ -n "${FAKE_CONFIG_LOG:-}" ] && printf '%s\n' "${OPENCODE_CONFIG_CONTENT:-}" >>"$FAKE_CONFIG_LOG"
if [ "${1:-}" = "--pure" ]; then shift; fi
case "${1:-}" in
  --version)
    [ "${FAKE_OPENCODE_VERSION_STATUS:-0}" -eq 0 ] || exit "$FAKE_OPENCODE_VERSION_STATUS"
    echo "opencode test"
    ;;
  auth)
    [ "${FAKE_AUTH_STATUS:-0}" -eq 0 ] || exit "$FAKE_AUTH_STATUS"
    [ "${2:-}" = list ] && printf 'OpenRouter environment credential\n'
    ;;
  models)
    [ "${FAKE_MODELS_STATUS:-0}" -eq 0 ] || exit "$FAKE_MODELS_STATUS"
    printf '%s\n' \
      'opencode-go/kimi-k3' \
      'opencode-go/deepseek-v4-flash' \
      'openrouter/deepseek/deepseek-v4-flash-0731' \
      'openrouter/xiaomi/mimo-v2.5-pro'
    ;;
  run)
    dir=""
    shift
    while [ "$#" -gt 0 ]; do
      case "$1" in
        --dir) dir="$2"; shift 2 ;;
        *) shift ;;
      esac
    done
    [ -n "${FAKE_WRITE_REL:-}" ] && printf 'delegate change\n' >>"$dir/$FAKE_WRITE_REL"
    if [ "${FAKE_COMMIT:-0}" -eq 1 ]; then
      git -C "$dir" add -A
      git -C "$dir" commit -qm delegate-commit
    fi
    exit "${FAKE_DELEGATE_STATUS:-0}"
    ;;
  *) exit 0 ;;
esac
EOF
chmod +x "$fake_bin/codex" "$fake_bin/opencode"

doctor_log="$TMP_ROOT/doctor-calls.log"
doctor_output="$(PATH="$fake_bin:$PATH" CODEX_HOME="$fake_codex_home" FAKE_CALL_LOG="$doctor_log" "$SCRIPTS_DIR/orchestra-doctor.sh" --require-ready 2>&1)" || fail "green doctor preflight failed"
assert_contains "$doctor_output" "model-listed" "doctor distinguishes catalog membership"
assert_contains "$doctor_output" "invocation=unverified" "doctor never claims live callability"
doctor_calls="$(sed -n '1,20p' "$doctor_log")"
assert_contains "$doctor_calls" "opencode --pure auth list" "doctor inspects the plugin-disabled credential inventory"
assert_contains "$doctor_calls" "opencode --pure models" "doctor inspects the plugin-disabled model catalog"
case "$doctor_calls" in
  *"codex exec"*|*"codex review"*|*"opencode run"*) fail "doctor made a model call" ;;
  *) pass "doctor performs no model invocation" ;;
esac

printf "model = 'gpt-5.6-sol'\nmodel_reasoning_effort = high\n" >"$fake_codex_home/config.toml"
single_quote_output="$(PATH="$fake_bin:$PATH" CODEX_HOME="$fake_codex_home" "$SCRIPTS_DIR/orchestra-doctor.sh" --require-ready 2>&1)" || fail "single-quoted config preflight failed"
assert_contains "$single_quote_output" "configured-model=gpt-5.6-sol" "doctor parses single-quoted Codex model values"
assert_contains "$single_quote_output" "reasoning=high" "doctor parses unquoted Codex effort values"

set +e
broken_version_output="$(PATH="$fake_bin:$PATH" CODEX_HOME="$fake_codex_home" FAKE_CODEX_VERSION_STATUS=5 "$SCRIPTS_DIR/orchestra-doctor.sh" --require-ready 2>&1)"
broken_version_status=$?
malformed_lane_output="$(PATH="$fake_bin:$PATH" CODEX_HOME="$fake_codex_home" ORCHESTRA_LANE_CODE=not-a-route "$SCRIPTS_DIR/orchestra-doctor.sh" --require-ready 2>&1)"
malformed_lane_status=$?
set -e
assert_status "$broken_version_status" 1 "broken CLI version fails strict preflight"
assert_contains "$broken_version_output" "installed=no" "broken CLI is not reported as installed"
assert_status "$malformed_lane_status" 1 "malformed lane override fails strict preflight"
assert_contains "$malformed_lane_output" "invalid-route" "malformed lane is labeled without catalog guessing"

set +e
strict_models_output="$(PATH="$fake_bin:$PATH" CODEX_HOME="$fake_codex_home" FAKE_CODEX_AUTH_STATUS=7 \
  "$SCRIPTS_DIR/orchestra-doctor.sh" --models --require-ready 2>&1)"
strict_models_status=$?
set -e
assert_status "$strict_models_status" 1 "strict models report includes auth and wrapper readiness"
assert_contains "$strict_models_output" "authentication was not reported" "strict models report does not bypass auth checks"

set +e
degraded_output="$(PATH="$fake_bin:$PATH" CODEX_HOME="$fake_codex_home" FAKE_MODELS_STATUS=7 "$SCRIPTS_DIR/orchestra-doctor.sh" 2>&1)"
degraded_status=$?
strict_output="$(PATH="$fake_bin:$PATH" CODEX_HOME="$fake_codex_home" FAKE_MODELS_STATUS=7 "$SCRIPTS_DIR/orchestra-doctor.sh" --require-ready 2>&1)"
strict_status=$?
set -e
assert_status "$degraded_status" 0 "descriptive doctor mode tolerates degraded state"
assert_status "$strict_status" 1 "strict doctor mode fails on degraded state"
assert_contains "$degraded_output" "catalog=unavailable" "catalog failure becomes unknown state"
case "$degraded_output" in
  *"Working lanes"*) fail "degraded doctor still claims working lanes" ;;
  *) pass "degraded doctor does not claim working lanes" ;;
esac

# --- Wrapper integration: explicit authority and fail-closed escape checks ---
wrapper_repo="$TMP_ROOT/wrapper-repo"
new_repo "$wrapper_repo"

set +e
missing_scope_output="$(PATH="$fake_bin:$PATH" CODEX_HOME="$fake_codex_home" FAKE_WRITE_REL=allowed/should-not-exist.txt \
  "$SCRIPTS_DIR/codex-agent.sh" implement --allow-write --cd "$wrapper_repo" --no-plan-gate --timeout 0 -- "bounded edit" 2>&1)"
missing_scope_status=$?
missing_gate_output="$(PATH="$fake_bin:$PATH" CODEX_HOME="$fake_codex_home" FAKE_WRITE_REL=allowed/should-not-exist.txt \
  "$SCRIPTS_DIR/codex-agent.sh" implement --allow-write --cd "$wrapper_repo" --scope allowed --timeout 0 -- "bounded edit" 2>&1)"
missing_gate_status=$?
set -e
assert_status "$missing_scope_status" 2 "implementation refuses missing scope"
assert_contains "$missing_scope_output" "requires at least one explicit --scope" "missing-scope failure is actionable"
assert_status "$missing_gate_status" 2 "implementation refuses an implicit plan-gate decision"
assert_contains "$missing_gate_output" "explicit gate decision" "missing-gate failure is actionable"
[ ! -e "$wrapper_repo/allowed/should-not-exist.txt" ] && pass "authority preflight failures do not launch the delegate" || fail "delegate ran after authority preflight failure"

set +e
codex_escape_output="$(PATH="$fake_bin:$PATH" CODEX_HOME="$fake_codex_home" FAKE_WRITE_REL=outside.txt \
  "$SCRIPTS_DIR/codex-agent.sh" implement --allow-write --cd "$wrapper_repo" --scope allowed --no-plan-gate --timeout 0 -- "bounded edit" 2>&1)"
codex_escape_status=$?
set -e
assert_status "$codex_escape_status" 3 "Codex wrapper returns scope-violation status"
assert_contains "$codex_escape_output" "outside --scope" "Codex wrapper reports escaped path"
assert_contains "$(tail -n 1 "$wrapper_repo/outside.txt")" "delegate change" "Codex wrapper never hides or reverts escaped change"

git -C "$wrapper_repo" restore outside.txt
set +e
opencode_escape_output="$(PATH="$fake_bin:$PATH" FAKE_WRITE_REL=outside.txt \
  "$SCRIPTS_DIR/opencode-implement.sh" --allow-write --cd "$wrapper_repo" --scope allowed --no-plan-gate --model test/model --timeout 0 -- "bounded edit" 2>&1)"
opencode_escape_status=$?
set -e
assert_status "$opencode_escape_status" 3 "OpenCode wrapper returns scope-violation status"
assert_contains "$opencode_escape_output" "outside --scope" "OpenCode wrapper reports escaped path"

git -C "$wrapper_repo" restore outside.txt
set +e
codex_inside_output="$(PATH="$fake_bin:$PATH" CODEX_HOME="$fake_codex_home" FAKE_WRITE_REL=allowed/new.txt \
  "$SCRIPTS_DIR/codex-agent.sh" implement --allow-write --cd "$wrapper_repo" --scope allowed --no-plan-gate --timeout 0 -- "bounded edit" 2>&1)"
codex_inside_status=$?
set -e
assert_status "$codex_inside_status" 0 "Codex wrapper accepts an in-scope creation"
assert_contains "$codex_inside_output" "Working-tree changes" "Codex wrapper reports the resulting tree"

set +e
codex_nonzero_output="$(PATH="$fake_bin:$PATH" CODEX_HOME="$fake_codex_home" FAKE_WRITE_REL=allowed/nonzero.txt FAKE_DELEGATE_STATUS=9 \
  "$SCRIPTS_DIR/codex-agent.sh" implement --allow-write --cd "$wrapper_repo" --scope allowed --no-plan-gate --timeout 0 -- "bounded edit" 2>&1)"
codex_nonzero_status=$?
set -e
assert_status "$codex_nonzero_status" 9 "delegate failure is preserved when scope remains valid"

git -C "$wrapper_repo" restore outside.txt 2>/dev/null || true
set +e
codex_both_output="$(PATH="$fake_bin:$PATH" CODEX_HOME="$fake_codex_home" FAKE_WRITE_REL=outside.txt FAKE_DELEGATE_STATUS=9 \
  "$SCRIPTS_DIR/codex-agent.sh" implement --allow-write --cd "$wrapper_repo" --scope allowed --no-plan-gate --timeout 0 -- "bounded edit" 2>&1)"
codex_both_status=$?
set -e
assert_status "$codex_both_status" 3 "scope violation takes precedence over delegate failure"

commit_repo="$TMP_ROOT/commit-repo"
new_repo "$commit_repo"
set +e
commit_escape_output="$(PATH="$fake_bin:$PATH" CODEX_HOME="$fake_codex_home" FAKE_WRITE_REL=outside.txt FAKE_COMMIT=1 \
  "$SCRIPTS_DIR/codex-agent.sh" implement --allow-write --cd "$commit_repo" --scope allowed --no-plan-gate --timeout 0 -- "bounded edit" 2>&1)"
commit_escape_status=$?
set -e
assert_status "$commit_escape_status" 3 "delegate commit cannot hide an out-of-scope change"
assert_contains "$commit_escape_output" "HEAD changed during delegation" "commit bypass reports the changed HEAD"

set +e
inspection_output="$(orchestra_scope_snapshot_verify "$TMP_ROOT/not-a-repo" "$dirty_state" "during test" allowed 2>&1)"
inspection_status=$?
set -e
assert_status "$inspection_status" 2 "scope inspection failures remain distinct from violations"
assert_contains "$inspection_output" "could not inspect repository" "scope inspection failure is explained accurately"

# --- Unified selector: routing, effort, independence, and three-stage defaults ---
selector="$SCRIPTS_DIR/orchestra-agent.sh"
selector_list="$($selector --list)"
assert_contains "$selector_list" "latest Go DeepSeek V4 Flash" "selector presents the latest Go worker route"
assert_contains "$selector_list" "reasoning=max" "selector presents max reasoning for the worker"
assert_contains "$selector_list" "gpt-5.6-luna  reasoning=max" "selector presents Luna/max critique"
assert_contains "$selector_list" "gpt-5.6-sol  reasoning=xhigh" "selector presents Sol/xhigh overview"
assert_contains "$selector_list" "opencode-go/kimi-k3" "selector presents Kimi K3 as the optional specialist"
assert_not_contains "$selector_list" "minimax" "selector removes MiniMax routes"

selector_log="$TMP_ROOT/selector-calls.log"
: >"$selector_log"
selector_dry="$(PATH="$fake_bin:$PATH" CODEX_HOME="$fake_codex_home" FAKE_CALL_LOG="$selector_log" \
  "$selector" implement --dry-run --allow-write --scope allowed --no-plan-gate -- "bounded edit")"
assert_contains "$selector_dry" "model=opencode-go/deepseek-v4-flash reasoning=max" "dry-run resolves Go DeepSeek/max as worker"
assert_contains "$selector_dry" "model=gpt-5.6-luna reasoning=max" "dry-run resolves Luna/max critic"
assert_contains "$selector_dry" "model=gpt-5.6-sol reasoning=xhigh" "dry-run resolves Sol/xhigh overview"
[ ! -s "$selector_log" ] && pass "selector dry-run makes no provider invocation" || fail "selector dry-run invoked a provider"

set +e
duplicate_output="$("$selector" implement --dry-run --backend codex --model luna --allow-write --scope allowed --no-plan-gate -- "bounded edit" 2>&1)"
duplicate_status=$?
caller_duplicate_output="$("$selector" review --dry-run --current-model luna -- "review" 2>&1)"
caller_duplicate_status=$?
set -e
assert_status "$duplicate_status" 2 "selector rejects duplicate worker and critic models"
assert_contains "$duplicate_output" "choose independent models" "duplicate-stage error is actionable"
assert_status "$caller_duplicate_status" 2 "selector rejects self-review by the caller model"
assert_contains "$caller_duplicate_output" "caller and primary-stage" "self-review error identifies the collision"

: >"$selector_log"
PATH="$fake_bin:$PATH" CODEX_HOME="$fake_codex_home" FAKE_CALL_LOG="$selector_log" \
  "$SCRIPTS_DIR/codex-agent.sh" review --cd "$wrapper_repo" --uncommitted --timeout 0 >/dev/null 2>&1 || fail "default Luna review failed"
review_call="$(sed -n '1p' "$selector_log")"
assert_contains "$review_call" 'model="gpt-5.6-luna"' "direct critique defaults to Luna"
assert_contains "$review_call" 'model_reasoning_effort="max"' "direct critique defaults to max reasoning"

set +e
ultra_output="$(PATH="$fake_bin:$PATH" CODEX_HOME="$fake_codex_home" \
  "$SCRIPTS_DIR/codex-agent.sh" review --cd "$wrapper_repo" --effort ultra --uncommitted 2>&1)"
ultra_status=$?
set -e
assert_status "$ultra_status" 2 "undocumented ultra effort remains refused"

worker_repo="$TMP_ROOT/worker-repo"
new_repo "$worker_repo"
: >"$selector_log"
config_log="$TMP_ROOT/opencode-config.log"
: >"$config_log"
PATH="$fake_bin:$PATH" FAKE_CALL_LOG="$selector_log" FAKE_CONFIG_LOG="$config_log" \
  "$SCRIPTS_DIR/opencode-implement.sh" --allow-write --cd "$worker_repo" --scope allowed --no-plan-gate --timeout 0 -- "bounded edit" >/dev/null 2>&1 || fail "default DeepSeek worker failed"
worker_call="$(sed -n '1p' "$selector_log")"
worker_config="$(sed -n '1p' "$config_log")"
assert_contains "$worker_call" "--model opencode-go/deepseek-v4-flash" "direct worker defaults to Go DeepSeek V4 Flash"
assert_contains "$worker_call" "--variant max" "direct worker selects the Go max reasoning variant"
assert_not_contains "$worker_config" '"openrouter"' "Go worker does not inject OpenRouter routing"

: >"$selector_log"
PATH="$fake_bin:$PATH" FAKE_CALL_LOG="$selector_log" \
  "$SCRIPTS_DIR/opencode-implement.sh" --allow-write --cd "$worker_repo" --scope allowed --no-plan-gate --model openrouter/test/model --variant exact --timeout 0 -- "bounded edit" >/dev/null 2>&1 || fail "OpenCode override worker failed"
override_call="$(sed -n '1p' "$selector_log")"
assert_contains "$override_call" "--variant exact" "OpenCode implementation still forwards provider variants"

: >"$selector_log"
PATH="$fake_bin:$PATH" CODEX_HOME="$fake_codex_home" FAKE_CALL_LOG="$selector_log" \
  "$selector" implement --allow-write --cd "$worker_repo" --scope allowed --no-plan-gate --timeout 0 -- "bounded edit" >/dev/null 2>&1 || fail "default three-stage pipeline failed"
pipeline_calls="$(grep -E '^(opencode|codex) ' "$selector_log")"
assert_contains "$pipeline_calls" "opencode --pure run" "pipeline starts with the OpenCode worker"
assert_contains "$pipeline_calls" 'model="gpt-5.6-luna"' "pipeline runs the Luna critique"
assert_contains "$pipeline_calls" 'model="gpt-5.6-sol"' "pipeline runs the Sol overview"

printf '1..%d\n' "$passes"
