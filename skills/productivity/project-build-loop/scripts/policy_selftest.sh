#!/usr/bin/env bash
# policy_selftest.sh — regression matrix for policy_check.sh against the
# golden fixtures and gate rules in references/dual-use-rating.md.
# Exit: 0 all pass, 1 one or more mismatches.

set -uo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
PC="$DIR/policy_check.sh"
pass=0; fail=0

# expect EXPECTED_RC -- <policy_check args...>
expect() {
  local want="$1"; shift
  [ "$1" = "--" ] && shift
  local out rc
  out="$("$PC" "$@" 2>&1)"; rc=$?
  if [ "$rc" -eq "$want" ]; then
    pass=$((pass+1))
  else
    fail=$((fail+1))
    printf 'FAIL want rc=%s got rc=%s :: %s\n     -> %s\n' "$want" "$rc" "$* " "$(printf '%s' "$out" | tail -1)"
  fi
}
# rc: 0 allow, 1 block, 2 usage

# --- Tier floors from capability flags (decision tree) ---
# credential_material / production_target / third_party_target => T4 (blocks tooling)
expect 1 -- --action tooling --tier T2 --flags credential_material --authorized yes --scoped yes --isolated yes
expect 1 -- --action tooling --tier T1 --flags production_target --authorized yes --scoped yes --isolated yes
expect 1 -- --action tooling --tier T0 --flags third_party_target --authorized yes --scoped yes --isolated yes
# active_scan / exploit_poc / malware_sample / mitm_proxy => T3 (tooling ok iff authorized+scoped+isolated)
expect 0 -- --action tooling --tier T2 --flags active_scan --authorized yes --scoped yes --isolated yes
expect 1 -- --action tooling --tier T2 --flags exploit_poc --authorized yes --scoped no --isolated yes
# packet_capture must NOT bump to T3 (golden: isolated lab capture stays T1-T2)
expect 0 -- --action tooling --tier T2 --flags packet_capture --authorized yes --isolated yes

# --- Golden fixtures ---
# OSINT chain (passive_recon, internet_egress) T2: tooling ok w/ authz+iso
expect 0 -- --action tooling --tier T2 --flags passive_recon,internet_egress --authorized yes --isolated yes
# MITM (mitm_proxy, traffic_decryption) => T3 tooling needs full proof; blocked without scope
expect 1 -- --action tooling --tier T2 --flags mitm_proxy,traffic_decryption --authorized yes --isolated yes
# Authorized pentest (active_scan, exploit_poc) T3 publish default no (needs approval exception)
expect 1 -- --action publish --tier T3 --publish-policy defensive-only
expect 0 -- --action publish --tier T3 --publish-policy defensive-only --approval yes

# --- git-remote / publish approval gating ---
expect 1 -- --action git-remote --tier T1                       # no approval => block
expect 0 -- --action git-remote --tier T1 --approval yes
expect 1 -- --action git-remote --tier T3 --approval yes        # T3 no remote regardless
expect 1 -- --action publish   --tier T0                        # no approval => block
expect 0 -- --action publish   --tier T0 --approval yes
expect 1 -- --action publish   --tier T4 --approval yes         # T4 never

# --- consult kinds ---
expect 1 -- --action consult --tier T4                          # artifact consult blocked at T4
expect 0 -- --action consult --tier T4 --consult-kind planning
expect 0 -- --action consult --tier T3

# --- unknown tier / malformed => restrictive ---
expect 1 -- --action publish --tier T9                          # unknown => T3 => block without approval
expect 0 -- --action publish --tier T9 --approval yes           # T3 exception path with approval
expect 2 -- --action                                            # missing value => usage error, no hang

# --- state_check.sh: phase + task transitions ---
SC="$DIR/state_check.sh"
sexpect() { local want="$1"; shift; [ "$1" = "--" ] && shift; "$SC" "$@" >/dev/null 2>&1; local rc=$?; if [ "$rc" -eq "$want" ]; then pass=$((pass+1)); else fail=$((fail+1)); printf 'FAIL(state) want rc=%s got rc=%s :: %s\n' "$want" "$rc" "$*"; fi; }
sexpect 0 -- phase --from intake --to discovery
sexpect 0 -- phase --from consult --to task-loop          # loop back after consult
sexpect 1 -- phase --from intake --to completion          # illegal skip
sexpect 0 -- phase --from intake --to completion --allow-regress
sexpect 1 -- task --from todo --to done                   # must pass in-progress
sexpect 0 -- task --from in-progress --to done
sexpect 1 -- task --from done --to in-progress            # terminal
sexpect 0 -- task --from done --to in-progress --allow-reopen

# --- closure-proof + append seq + validate_state (integration) ---
BS="$DIR/bootstrap_project.sh"; AE="$DIR/append_event.sh"; VS="$DIR/validate_state.py"
TDIR="$(mktemp -d)"
"$BS" --base "$TDIR/p" --install-root --apply >/dev/null 2>&1
"$BS" --base "$TDIR/p" --title 'selftest proj' --category software-development --apply >/dev/null 2>&1
PJ="$TDIR/p/software-development/selftest-proj"
iexpect() { local want="$1" got="$2" label="$3"; if [ "$got" -eq "$want" ]; then pass=$((pass+1)); else fail=$((fail+1)); printf 'FAIL(integ) %s want rc=%s got rc=%s\n' "$label" "$want" "$got"; fi; }
"$SC" closure --project "$PJ" --task 1.1 >/dev/null 2>&1; iexpect 1 $? "closure-no-ledger"
printf '# t\n<!-- task-steps-ledger:task-1.1 -->\n## Validation And Evidence\n| Check | Command or probe | Expected | Observed | Evidence pointer | Status |\n|---|---|---|---|---|---|\n| DNS | dig x | A | A returned | evidence/x.txt | observed |\n' > "$PJ/build-log/task-1.1.steps.md"
"$SC" closure --project "$PJ" --task 1.1 >/dev/null 2>&1; iexpect 0 $? "closure-validated-row"
"$AE" --project "$PJ" --event classify --field tier=T2 >/dev/null 2>&1
"$AE" --project "$PJ" --event gate --field decision=allow >/dev/null 2>&1
python3 "$VS" event-log "$PJ/event-log.jsonl" >/dev/null 2>&1; iexpect 0 $? "eventlog-monotonic-valid"
python3 "$VS" project "$PJ/project.json" >/dev/null 2>&1; iexpect 0 $? "project-json-valid"
"$DIR/policy_check.sh" --action git-remote --tier T1 --approval yes --receipt "$PJ" >/dev/null 2>&1
tail -1 "$PJ/event-log.jsonl" | grep -q '"gate":"policy_check"'; iexpect 0 $? "gate-receipt-written"
printf '{"ts":"a","seq":1,"event":"b"}\n{"ts":"c","seq":1,"event":"dup"}\n' > "$TDIR/bad.jsonl"
python3 "$VS" event-log "$TDIR/bad.jsonl" >/dev/null 2>&1; iexpect 1 $? "eventlog-nonmonotonic-rejected"

# --- fail-closed regressions from the gate-script review ---
HDR='| Check | Command | Expected | Observed | Evidence pointer | Status |\n|---|---|---|---|---|---|\n'
LG="$PJ/build-log/task-9.9.steps.md"
printf "# t\n## Validation And Evidence\n${HDR}| ping | p | reply | got reply | evidence/x.txt | failed |\n" > "$LG"
"$SC" closure --project "$PJ" --task 9.9 >/dev/null 2>&1; iexpect 1 $? "closure-status-failed-blocked"
printf "# t\n## Validation And Evidence\n${HDR}| ping | p | reply | got reply | evidence/x.txt | reviewed |\n" > "$LG"
"$SC" closure --project "$PJ" --task 9.9 >/dev/null 2>&1; iexpect 1 $? "closure-nonallowlist-status-blocked"
printf "# t\n## Limitations\n- none\n" > "$LG"
"$SC" closure --project "$PJ" --task 9.9 >/dev/null 2>&1; iexpect 1 $? "closure-negating-limitation-blocked"
printf "# t\n## Limitations\n- hardware NIC unavailable; validated in emulator only\n" > "$LG"
"$SC" closure --project "$PJ" --task 9.9 >/dev/null 2>&1; iexpect 0 $? "closure-real-limitation-allowed"
# boolean seq rejected by validator and by append
printf '{"ts":"a","seq":true,"event":"x"}\n' > "$TDIR/bool.jsonl"
python3 "$VS" event-log "$TDIR/bool.jsonl" >/dev/null 2>&1; iexpect 1 $? "eventlog-bool-seq-rejected"
mkdir -p "$TDIR/bp"; printf '{"ts":"a","seq":true,"event":"x"}\n' > "$TDIR/bp/event-log.jsonl"
"$AE" --project "$TDIR/bp" --event y >/dev/null 2>&1; iexpect 2 $? "append-refuses-corrupt-log"
# malformed --raw rejected
"$AE" --project "$PJ" --event x --raw bad='{nope' >/dev/null 2>&1; iexpect 2 $? "append-malformed-raw-rejected"
# task validation: example strict-invalid, --example valid, bad enum invalid
python3 "$VS" task "$DIR/../references/schemas/task.json" >/dev/null 2>&1; iexpect 1 $? "task-example-strict-invalid"
python3 "$VS" task --example "$DIR/../references/schemas/task.json" >/dev/null 2>&1; iexpect 0 $? "task-example-flag-valid"
printf '{"id":"1.1","title":"t","status":"finished","gate":"validate"}\n' > "$TDIR/bt.json"
python3 "$VS" task "$TDIR/bt.json" >/dev/null 2>&1; iexpect 1 $? "task-bad-status-invalid"
# unreadable file scan fails closed
echo secret > "$TDIR/nr.txt"; chmod 000 "$TDIR/nr.txt"
"$DIR/secret_scan.sh" "$TDIR/nr.txt" >/dev/null 2>&1; iexpect 1 $? "secretscan-unreadable-failclosed"; chmod 644 "$TDIR/nr.txt"
rm -rf "$TDIR"

echo "policy_selftest: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
