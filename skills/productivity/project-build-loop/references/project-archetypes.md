# Project archetypes

Archetype = **routing only**. It selects a default domain-skill bundle, placement
category, and a *base* tier hint. The confirmed tier always comes from
`dual-use-rating.md` capability flags, never from the archetype alone. A project
may carry a `primary` and a `secondary` archetype.

Each archetype lists: default category · base-tier hint · default skill bundle.

## Cybersecurity / networking

- **osint-recon** · networking-and-cybersecurity · T2 ·
  `performing-dns-enumeration-and-zone-transfer`, `study-research-queries`,
  `literature-review`, `security-ownership-map`.
- **network-lab-emulation** · networking-and-cybersecurity · T1 ·
  `eve-ng-topology`, `configuring-network-segmentation-with-vlans`,
  `cisco-ios-patterns`, `network-config-validation`, `homelab-*`.
- **passive-traffic-analysis** · networking-and-cybersecurity · T1–T2 ·
  `performing-network-packet-capture-analysis`,
  `performing-network-traffic-analysis-with-tshark`,
  `performing-network-traffic-analysis-with-zeek`,
  `analyzing-network-traffic-with-wireshark`.
- **active-interception** (MITM positioning) · networking-and-cybersecurity ·
  **T3** · routes only after authorization + isolation proof; pairs with
  detection/mitigation skills (`building-detection-rules-with-sigma`,
  `configuring-suricata-for-network-monitoring`) for purple-team framing.
- **malware-analysis** · networking-and-cybersecurity · T3 ·
  `analyzing-indicators-of-compromise`, `analyzing-linux-system-artifacts`,
  isolated sample handling.
- **detection-engineering** · networking-and-cybersecurity · T1 ·
  `building-detection-rules-with-sigma`, `configuring-suricata-for-network-monitoring`,
  `analyzing-threat-actor-ttps-with-mitre-attack`.
- **hardening-compliance** · networking-and-cybersecurity · T1 ·
  `hardening-linux-endpoint-with-cis-benchmark`, `auditing-cloud-with-cis-benchmarks`,
  `configuring-pfsense-firewall-rules`, `security-and-hardening`.
- **pentest-engagement** · networking-and-cybersecurity · T3 ·
  `scanning-network-with-nmap-advanced` + scoped offensive skills; requires
  written ROE before any active flag.
- **forensics-ir** · networking-and-cybersecurity · T1–T2 ·
  `performing-network-forensics-with-wireshark`,
  `performing-linux-log-forensics-investigation`,
  `building-incident-response-playbook`, `analyzing-cyber-kill-chain`.
- **detection/analysis adjuncts** · `analyzing-email-headers-for-phishing-investigation`,
  `analyzing-network-packets-with-scapy`.

## Coding / infrastructure

- **app-build** · software-development · T0 · standard engineering skills; risk
  comes from `data_classes` (e.g. PII) not offense.
- **infra-build** · software-development · T0–T1 · IaC/devops; tier rises with
  `production_target` or `internet_egress` flags.

## Additional archetypes to seed (stubs — expand on first use)

vulnerability-research/exploit-dev (T3–T4), reverse-engineering (T2–T3),
active-directory/identity-lab (T2–T3), cloud-security-lab (T2),
container/k8s-security (T2), wireless/RF (T2–T3), ICS/OT/SCADA (T3),
social-engineering/phishing-sim (T2–T3), purple-team (T2),
supply-chain/SCA (T1–T2), mobile-security (T2), crypto/PKI (T1–T2),
threat-intel-production (T1–T2).

> Predicate hygiene: `network-lab-emulation` vs `active-interception` and
> `passive-traffic-analysis` vs `active-interception` must be distinguished by
> **capability flags**, not name. `app-build`/`infra-build` carry real risk only
> through flags and `data_classes`.
