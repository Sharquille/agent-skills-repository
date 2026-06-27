# Discovery interview — governance-complete question bank

Walk these during Phase 2. Adaptive, not a rigid script: skip what is obviously
N/A, but treat any **unknown** in the gating sections as restrictive (apply the
higher tier; block risky actions until resolved). Capture answers into
`project.json` and the build log.

## A. Objective & scope

- One-sentence objective and definition of "done" (success criteria).
- Primary and secondary **archetype** (see `project-archetypes.md`).
- In-scope vs explicitly out-of-scope assets/networks/domains.

## B. Authorization (GATE — not a score)

- Who **owns** every IP/domain/device in scope? Personal, lab tenant, or
  employer/client?
- Is there **written or policy-based authorization** (ROE)? Where is the evidence
  stored?
- Allowed actions vs excluded actions.
- For any live/third-party target: stop here unless authorization is confirmed.

## C. Isolation & safety

- How is the lab (e.g. EVE-NG) segmented from production/home/corp networks?
- Egress/NAT/DNS controls; is there a **kill-switch** for unexpected egress or
  live-malware beaconing?
- VLAN/VXLAN/air-gap evidence; snapshot/recovery plan.

## D. Environment

- EVE-NG Community or Pro? Node image versions, hypervisor resources, snapshots,
  licensing, physical underlay.
- For production work: rollback/snapshot state.

## E. Capability flags (drive the tier)

Which of these will the project introduce? `passive_recon`, `active_scan`,
`packet_capture`, `traffic_decryption`, `mitm_proxy`, `exploit_poc`,
`malware_sample`, `credential_material`, `production_target`,
`third_party_target`, `internet_egress`.

## F. Evidence & data

- Which artifacts (PCAP, logs, configs, screenshots, CLI output)?
- Hash algorithm + timestamping? Retention period? Vault access control?
- **Data classes** present (PII, credentials, customer-like, synthetic)?

## G. Redaction & publication

- What must be redacted (IPs, hostnames, domains, credentials, certs, PII)?
- Intended **audience** (`internal-only`, `client-confidential`,
  `community-shared`, `public`)?
- Publish intent: defensive write-up, troubleshooting guide, or none?

## H. Tooling supply chain

- Source of EVE-NG images, GitHub tools, container images — vetted? hashes?

## I. Lifecycle close-out

- Decommission plan: VM/snapshot deletion, secret rotation, evidence destruction.
- Reproducibility: which versions/configs are needed to rebuild?
