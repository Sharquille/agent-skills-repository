# Discovery interview — governance-complete question bank

Walk these during Phase 2. Adaptive, not a rigid script: skip what is obviously
N/A, but treat any **unknown** in the gating sections as restrictive (apply the
higher tier; block risky actions until resolved). Capture answers into
`project.json` and the build log.

Ask questions in a concrete, beginner-readable form. Before using lifecycle
terms such as topology, trust boundary, egress, evidence, retention, or
decommission, explain what the term means for this project. Give safe examples,
allow placeholders, and tell the user when `unsure` is acceptable so the
conductor can propose a default.

Use this pattern for follow-up questions:

```text
Task N.N: <title>
This means: <concrete objects or decisions involved>.
Why it matters: <safety/function/evidence gate>.
What I need from you:
1. <specific input with example or placeholder>
2. <specific input with example or placeholder>
Do not send: <secrets/private data to avoid>.
```

## A. Objective & scope

- One-sentence objective and definition of "done" (success criteria).
- Primary and secondary **archetype** (see `project-archetypes.md`).
- In-scope vs explicitly out-of-scope assets/networks/domains.
- Plain-language prompt: "What are we building, who or what may it touch, and
  what result proves the first version works?"

## B. Authorization (GATE — not a score)

- Who **owns** every IP/domain/device in scope? Personal, lab tenant, or
  employer/client?
- Is there **written or policy-based authorization** (ROE)? Where is the evidence
  stored?
- Allowed actions vs excluded actions.
- For any live/third-party target: stop here unless authorization is confirmed.
- Plain-language prompt: "Which systems, accounts, names, domains, or profiles
  are yours to test, and which ones must we avoid?"

## C. Isolation & safety

- How is the lab (e.g. EVE-NG) segmented from production/home/corp networks?
- Egress/NAT/DNS controls; is there a **kill-switch** for unexpected egress or
  live-malware beaconing?
- VLAN/VXLAN/air-gap evidence; snapshot/recovery plan.
- Plain-language prompt: "Which VM NIC connects to the outside network, which
  NIC connects to the private lab, what traffic is allowed out, and what should
  be blocked if the tunnel or gateway fails?"

## D. Environment

- EVE-NG Community or Pro? Node image versions, hypervisor resources, snapshots,
  licensing, physical underlay.
- For production work: rollback/snapshot state.
- Plain-language prompt: "List the devices, VM images, EVE-NG networks/clouds,
  interface names, and any version numbers you already know. Use placeholders if
  needed."

## E. Capability flags (drive the tier)

Which of these will the project introduce? `passive_recon`, `active_scan`,
`packet_capture`, `traffic_decryption`, `mitm_proxy`, `exploit_poc`,
`malware_sample`, `credential_material`, `production_target`,
`third_party_target`, `internet_egress`.

## F. Evidence & data

- Which artifacts (PCAP, logs, configs, screenshots, CLI output)?
- Hash algorithm + timestamping? Retention period? Vault access control?
- **Data classes** present (PII, credentials, customer-like, synthetic)?
- Plain-language prompt: "What proof should we save to show the build worked:
  screenshots, tcpdump/PCAPs, route tables, firewall rules, DNS leak checks, IP
  checks, logs, or sanitized configs?"

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
- Plain-language prompt: "When this lab is done, what should be kept, what
  should be deleted, and what notes/configs would let you rebuild it later?"
