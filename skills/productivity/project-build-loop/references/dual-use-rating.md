# Dual-use rating policy

The conductor's authoritative policy for classifying a project's sensitivity and
gating tooling, git, consults, and publication. The LLM **proposes** a
classification; `scripts/policy_check.sh` **validates** it before any risky
action. Fail closed.

## Core principles

1. **Archetype routes; capability flags rate.** Archetype selects the default
   skill bundle and placement (routing only). The **tier** comes from concrete
   capability flags via the decision tree below — never from a free-form score.
2. **Authorization is a gate, not a score.** A separate `authorization` object
   must read `authorized + scoped + isolated` or the action is **no-go**. Strong
   authorization permits work; it never lowers a tier.
3. **Dual-use risk and data sensitivity are independent axes.** A PHI app is
   high-sensitivity / low-offensive; a MITM lab is offensive-sensitive even with
   synthetic data. The stricter axis sets `artifact_class_floor`.
4. **Unknown = restrictive.** Unknown ownership, egress, data class, or publish
   intent applies the higher tier and blocks risky actions until resolved.
5. **One confirmed tier.** `project.json` stores one tier or `review_required`;
   while unresolved, enforce the higher tier.

## Capability flags (controlled enum)

`passive_recon`, `active_scan`, `packet_capture`, `traffic_decryption`,
`mitm_proxy`, `exploit_poc`, `malware_sample`, `credential_material`,
`production_target`, `third_party_target`, `internet_egress`.

A task **declares** the flags it introduces. Introducing a higher-risk flag
(`mitm_proxy`, `traffic_decryption`, `exploit_poc`, `malware_sample`,
`production_target`, `third_party_target`) forces **reclassification** before the
conductor routes execution.

## Tier decision tree (first match wins, top-down)

- **T4** — any of: missing/unclear authorization for a live target;
  `credential_material` theft against a real account; persistence/evasion;
  destructive action; `production_target` or `third_party_target` exploitation;
  control-bypass guidance; data exfiltration.
- **T3** — any of: `mitm_proxy`, `traffic_decryption`, `exploit_poc`,
  `malware_sample`, `active_scan` against a live host, or other usable
  interception/exploitation/credential-adjacent or live-target capability **even
  with authorization**.
- **T2** — dual-use but bounded to a lab / owned target / defensive telemetry
  (e.g. `passive_recon`, `packet_capture` in an isolated lab).
- **T1** — defensive or owned-environment work with no attack-enabling
  deliverable (hardening, detection-rule authoring, config validation).
- **T0** — informational / docs / normal app work, no security-sensitive
  capability.

Split note: passive capture/analysis is **T1–T2**; **active MITM positioning is
T3**; add credential/session capture or certificate forgery and it is **T4**.

## Tier → gate table (fail closed, per action)

| Tier | Tooling | Git | Consult | Publish |
|---|---|---|---|---|
| T0/T1 | normal | local; remote only after secret-scan + approval | optional | after secret-scan + approval |
| T2 | re-check authorization + isolation | private/sanitized remote, explicit approval | **redaction manifest required** | **defensive/troubleshooting narrative only** |
| T3 | explicit authorization + **isolation proof** before offensive tooling | **no remote** by default | **security-review consult required**; allowlisted sanitized artifacts only | default **no-publish**; exception = security review + manual approval + redaction diff + publish manifest |
| T4 | **block** active execution/tooling | **block** | planning/scoping/safe-analysis only | **never** |

**Reclassification triggers:** a later task adding packet capture, live targets,
credentials, malware, exploit code, or public-publish intent **invalidates and
reruns** classification. Upward changes are automatic; **downward** changes
require explicit human rationale + an `event-log.jsonl` entry.

## Publication rules (controls, not disclaimers)

A dual-use disclaimer is boilerplate added **after** the controls below pass; it
is not itself a control.

**Hard gate:** allowlisted publish manifest + forbidden-content rules + redaction
review + a pre-publish secret scan.

**Always redact:** exploit payloads / one-liner commands; ready-to-use
control-bypass configs/scripts; real hostnames/IPs/domains (replace with **RFC
5737** IPv4 `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24` and **RFC 3849**
IPv6 `2001:db8::/32`); certs/keys/tokens/credentials; PII / org-identifying data;
full payload PCAPs (publish only sanitized, truncated, or synthetic); precise
production topology; screenshot EXIF/metadata; exact timestamps.

**Required defensive framing (purple-team):** state authorization + isolation; a
**Detection** section (IOCs, Sigma/Suricata rules, log sources, alert logic); a
**Mitigation** section (segmentation, TLS/MACsec, 802.1X, certificate pinning,
hardening); structure as **attack → detect → harden**, methodology not weaponized
tooling.

**Refuse public publication when:** no written authorization evidence; real /
identifiable data present; unpatched vuln without coordinated disclosure;
export-control or legal review says no; the content mainly lowers the attack
barrier with little detection value; an NDA/confidentiality applies; or any active
MITM/session capture against a non-isolated target.

## Audience classes (separate from artifact classes)

`internal-only`, `client-confidential`, `community-shared`, `public`. The public
portfolio index reads only **approved publish manifests** and never reveals
unpublished T3/T4 project names. Keep tier in private metadata, never in a path.

## Golden-example fixtures

| Project | Flags | Tier | Publish |
|---|---|---|---|
| Own-target OSINT chain (Kali→WG→Mullvad→owned) | passive_recon, internet_egress | T2 (activity), publication of tradecraft T2 | defensive-only |
| Passive lab packet capture (isolated) | packet_capture | T1–T2 | defensive-only |
| MITM router / interception tooling | mitm_proxy, traffic_decryption | T3 | no-publish by default |
| Authorized pentest (scoped, written ROE) | active_scan, exploit_poc | T3 | defensive-only, redaction diff |
| Malware sandbox (isolated) | malware_sample | T3 | defensive-only |
| App handling PII | (data_class: pii) | T0/T1 offensive, high data-sensitivity | sanitized only |
| Linux/CIS hardening only | (none offensive) | T1 | publishable after scan |
