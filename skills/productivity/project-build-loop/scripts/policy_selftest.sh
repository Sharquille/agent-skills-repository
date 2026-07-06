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

echo "policy_selftest: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
