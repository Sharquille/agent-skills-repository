# Skills Registry

A personal registry of Claude Code skills collected from the internet and other sources.

## How to add a skill
1. Download the raw files into a quarantine dir (e.g. `/tmp/skill-audit`) — literal bytes, not a paraphrasing fetch.
2. **Audit before installing:** `skills/engineering/vet-skill/scripts/audit.sh /tmp/skill-audit` and eyeball every match.
3. On a clean verdict, copy the audited bytes into `skills/<category>/<skill-name>/` and add the provenance header (see `skills/_template/`).
4. Keep any `LICENSE` file for attribution, then `diff -r` quarantine vs. installed to prove no drift.
5. Add an entry to the table below and delete the quarantine dir.

---

## Skills

| Skill | Category | Author | Source | License | Added |
|-------|----------|--------|--------|---------|-------|
| [enhance-skill](skills/engineering/enhance-skill/) | engineering | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-13 |
| [gcp-well-architected-security](skills/engineering/gcp-well-architected-security/) | engineering | Google (google/skills) | [github.com/google/skills](https://github.com/google/skills/blob/main/skills/cloud/google-cloud-waf-security/SKILL.md) | Apache-2.0 | 2026-06-13 |
| [gcp-well-architected-reliability](skills/engineering/gcp-well-architected-reliability/) | engineering | Google (google/skills) | [github.com/google/skills](https://github.com/google/skills/blob/main/skills/cloud/google-cloud-waf-reliability/SKILL.md) | Apache-2.0 | 2026-06-13 |
| [gcp-well-architected-cost-optimization](skills/engineering/gcp-well-architected-cost-optimization/) | engineering | Google (google/skills) | [github.com/google/skills](https://github.com/google/skills/blob/main/skills/cloud/google-cloud-waf-cost-optimization/SKILL.md) | Apache-2.0 | 2026-06-13 |
| [gcp-well-architected-operational-excellence](skills/engineering/gcp-well-architected-operational-excellence/) | engineering | Google (google/skills) | [github.com/google/skills](https://github.com/google/skills/blob/main/skills/cloud/google-cloud-waf-operational-excellence/SKILL.md) | Apache-2.0 | 2026-06-13 |
| [gcp-well-architected-sustainability](skills/engineering/gcp-well-architected-sustainability/) | engineering | Google (google/skills) | [github.com/google/skills](https://github.com/google/skills/blob/main/skills/cloud/google-cloud-waf-sustainability/SKILL.md) | Apache-2.0 | 2026-06-13 |
| [gcp-well-architected-performance-optimization](skills/engineering/gcp-well-architected-performance-optimization/) | engineering | Google (google/skills) | [github.com/google/skills](https://github.com/google/skills/blob/main/skills/cloud/google-cloud-waf-performance-optimization/SKILL.md) | Apache-2.0 | 2026-06-13 |
| [name-skill](skills/engineering/name-skill/) | engineering | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-13 |
| [brainstorm-ideas-existing](skills/productivity/brainstorm-ideas-existing/) | productivity | Pawel Huryn (phuryn/pm-skills) | [github.com/phuryn/pm-skills](https://github.com/phuryn/pm-skills/tree/main/pm-product-discovery/skills/brainstorm-ideas-existing) | MIT | 2026-06-13 |
| [humanizer](skills/productivity/humanizer/) | productivity | blader | [github.com/blader/humanizer](https://github.com/blader/humanizer) | MIT | 2026-06-13 |
| [knowledge-capture-obsidian](skills/productivity/knowledge-capture-obsidian/) | productivity | Notion (notion-cookbook), adapted for Obsidian+GoodNotes | [github.com/makenotion/notion-cookbook](https://github.com/makenotion/notion-cookbook/tree/main/skills/claude/knowledge-capture) | MIT | 2026-06-13 |
| [obsidian-study-loop](skills/productivity/obsidian-study-loop/) | productivity | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-15 |
| [portable-markdown](skills/productivity/portable-markdown/) | productivity | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-18 |
| [review-pm-resume](skills/productivity/review-pm-resume/) | productivity | Pawel Huryn (phuryn/pm-skills) | [github.com/phuryn/pm-skills](https://github.com/phuryn/pm-skills/tree/main/pm-toolkit/skills/review-resume) | MIT | 2026-06-13 |
| [study-consult-panel](skills/productivity/study-consult-panel/) | productivity | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-20 |
| [study-map](skills/productivity/study-map/) | productivity | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-20 |
| [study-research-queries](skills/productivity/study-research-queries/) | productivity | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-15 |
| [teach-complex-concepts](skills/productivity/teach-complex-concepts/) | productivity | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-20 |
| [undo-obsidian-study-loop](skills/productivity/undo-obsidian-study-loop/) | productivity | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-15 |
| [vet-skill](skills/engineering/vet-skill/) | engineering | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-13 |
| [security-best-practices](skills/engineering/security-best-practices/) | engineering | OpenAI (openai/skills) | [github.com/openai/skills](https://github.com/openai/skills/tree/main/skills/.curated/security-best-practices) | Apache-2.0 | 2026-06-13 |
| [security-ownership-map](skills/engineering/security-ownership-map/) | engineering | OpenAI (openai/skills) | [github.com/openai/skills](https://github.com/openai/skills/tree/main/skills/.curated/security-ownership-map) | Apache-2.0 | 2026-06-13 |
| [security-threat-model](skills/engineering/security-threat-model/) | engineering | OpenAI (openai/skills) | [github.com/openai/skills](https://github.com/openai/skills/tree/main/skills/.curated/security-threat-model) | Apache-2.0 | 2026-06-13 |
| [analyzing-network-traffic-with-wireshark](skills/engineering/analyzing-network-traffic-with-wireshark/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/analyzing-network-traffic-with-wireshark) | Apache-2.0 | 2026-06-13 |
| [scanning-network-with-nmap-advanced](skills/engineering/scanning-network-with-nmap-advanced/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/scanning-network-with-nmap-advanced) | Apache-2.0 | 2026-06-13 |
| [configuring-network-segmentation-with-vlans](skills/engineering/configuring-network-segmentation-with-vlans/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/configuring-network-segmentation-with-vlans) | Apache-2.0 | 2026-06-13 |
| [configuring-pfsense-firewall-rules](skills/engineering/configuring-pfsense-firewall-rules/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/configuring-pfsense-firewall-rules) | Apache-2.0 | 2026-06-13 |
| [configuring-suricata-for-network-monitoring](skills/engineering/configuring-suricata-for-network-monitoring/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/configuring-suricata-for-network-monitoring) | Apache-2.0 | 2026-06-13 |
| [performing-network-traffic-analysis-with-zeek](skills/engineering/performing-network-traffic-analysis-with-zeek/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/performing-network-traffic-analysis-with-zeek) | Apache-2.0 | 2026-06-13 |
| [performing-dns-enumeration-and-zone-transfer](skills/engineering/performing-dns-enumeration-and-zone-transfer/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/performing-dns-enumeration-and-zone-transfer) | Apache-2.0 | 2026-06-13 |
| [performing-network-packet-capture-analysis](skills/engineering/performing-network-packet-capture-analysis/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/performing-network-packet-capture-analysis) | Apache-2.0 | 2026-06-13 |
| [hardening-linux-endpoint-with-cis-benchmark](skills/engineering/hardening-linux-endpoint-with-cis-benchmark/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/hardening-linux-endpoint-with-cis-benchmark) | Apache-2.0 | 2026-06-13 |
| [performing-linux-log-forensics-investigation](skills/engineering/performing-linux-log-forensics-investigation/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/performing-linux-log-forensics-investigation) | Apache-2.0 | 2026-06-13 |
| [analyzing-linux-system-artifacts](skills/engineering/analyzing-linux-system-artifacts/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/analyzing-linux-system-artifacts) | Apache-2.0 | 2026-06-13 |
| [analyzing-cyber-kill-chain](skills/engineering/analyzing-cyber-kill-chain/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/analyzing-cyber-kill-chain) | Apache-2.0 | 2026-06-13 |
| [analyzing-threat-actor-ttps-with-mitre-attack](skills/engineering/analyzing-threat-actor-ttps-with-mitre-attack/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/analyzing-threat-actor-ttps-with-mitre-attack) | Apache-2.0 | 2026-06-13 |
| [analyzing-indicators-of-compromise](skills/engineering/analyzing-indicators-of-compromise/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/analyzing-indicators-of-compromise) | Apache-2.0 | 2026-06-13 |
| [analyzing-email-headers-for-phishing-investigation](skills/engineering/analyzing-email-headers-for-phishing-investigation/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/analyzing-email-headers-for-phishing-investigation) | Apache-2.0 | 2026-06-13 |
| [building-incident-response-playbook](skills/engineering/building-incident-response-playbook/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/building-incident-response-playbook) | Apache-2.0 | 2026-06-13 |
| [analyzing-network-packets-with-scapy](skills/engineering/analyzing-network-packets-with-scapy/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/analyzing-network-packets-with-scapy) | Apache-2.0 | 2026-06-13 |
| [building-detection-rules-with-sigma](skills/engineering/building-detection-rules-with-sigma/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/building-detection-rules-with-sigma) | Apache-2.0 | 2026-06-13 |
| [auditing-aws-s3-bucket-permissions](skills/engineering/auditing-aws-s3-bucket-permissions/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/auditing-aws-s3-bucket-permissions) | Apache-2.0 | 2026-06-13 |
| [auditing-cloud-with-cis-benchmarks](skills/engineering/auditing-cloud-with-cis-benchmarks/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/auditing-cloud-with-cis-benchmarks) | Apache-2.0 | 2026-06-13 |
| [performing-network-forensics-with-wireshark](skills/engineering/performing-network-forensics-with-wireshark/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/performing-network-forensics-with-wireshark) | Apache-2.0 | 2026-06-13 |
| [performing-network-traffic-analysis-with-tshark](skills/engineering/performing-network-traffic-analysis-with-tshark/) | engineering | mukul975 (Anthropic-Cybersecurity-Skills) | [link](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/tree/main/skills/performing-network-traffic-analysis-with-tshark) | Apache-2.0 | 2026-06-13 |
| [build-security-policy](skills/engineering/build-security-policy/) | engineering | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-13 |
| [ai-slop-cleaner](skills/engineering/ai-slop-cleaner/) | engineering | Yeachan Heo (adapted) | [skillrepo.dev](https://skillrepo.dev/skills/Yeachan-Heo/ai-slop-cleaner) | MIT | 2026-06-14 |
| [api-and-interface-design](skills/engineering/api-and-interface-design/) | engineering | Addy Osmani | [skillrepo.dev](https://skillrepo.dev/skills/addyosmani/api-and-interface-design) | MIT | 2026-06-14 |
| [cisco-ios-patterns](skills/engineering/cisco-ios-patterns/) | engineering | Affaan Mustafa | [skillrepo.dev](https://skillrepo.dev) | MIT | 2026-06-14 |
| [agent-repo-security](skills/engineering/agent-repo-security/) | engineering | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-14 |
| [frontend-ui-engineering](skills/engineering/frontend-ui-engineering/) | engineering | Addy Osmani | [skillrepo.dev](https://skillrepo.dev/skills/addyosmani/frontend-ui-engineering) | MIT | 2026-06-14 |
| [deploy-agent-skills](skills/engineering/deploy-agent-skills/) | engineering | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-14 |
| [homelab-network-readiness](skills/engineering/homelab-network-readiness/) | engineering | Affaan Mustafa | [skillrepo.dev](https://skillrepo.dev/skills/affaan-m/homelab-network-readiness) | MIT | 2026-06-14 |
| [hipaa-compliance](skills/engineering/hipaa-compliance/) | engineering | Affaan Mustafa | [skillrepo.dev](https://skillrepo.dev/skills/affaan-m/hipaa-compliance) | MIT | 2026-06-14 |
| [homelab-vlan-segmentation](skills/engineering/homelab-vlan-segmentation/) | engineering | Affaan Mustafa | [skillrepo.dev](https://skillrepo.dev/skills/affaan-m/homelab-vlan-segmentation) | MIT | 2026-06-14 |
| [literature-review](skills/productivity/literature-review/) | productivity | Affaan Mustafa | [skillrepo.dev](https://skillrepo.dev/skills/affaan-m/literature-review) | MIT | 2026-06-14 |
| [naming-analyzer](skills/engineering/naming-analyzer/) | engineering | Leonardo Flores | [skillrepo.dev](https://skillrepo.dev/skills/softaworks/naming-analyzer) | MIT | 2026-06-14 |
| [network-bgp-diagnostics](skills/engineering/network-bgp-diagnostics/) | engineering | Affaan Mustafa | [skillrepo.dev](https://skillrepo.dev/skills/affaan-m/network-bgp-diagnostics) | MIT | 2026-06-14 |
| [network-config-validation](skills/engineering/network-config-validation/) | engineering | Affaan Mustafa | [skillrepo.dev](https://skillrepo.dev/skills/affaan-m/network-config-validation) | MIT | 2026-06-14 |
| [network-interface-health](skills/engineering/network-interface-health/) | engineering | Affaan Mustafa | [skillrepo.dev](https://skillrepo.dev/skills/affaan-m/network-interface-health) | MIT | 2026-06-14 |
| [security-and-hardening](skills/engineering/security-and-hardening/) | engineering | Addy Osmani | [skillrepo.dev](https://skillrepo.dev/skills/addyosmani/security-and-hardening) | MIT | 2026-06-14 |
| [security-bounty-hunter](skills/engineering/security-bounty-hunter/) | engineering | Affaan Mustafa | [skillrepo.dev](https://skillrepo.dev/skills/affaan-m/security-bounty-hunter) | MIT | 2026-06-14 |
| [security-scan](skills/engineering/security-scan/) | engineering | Affaan Mustafa | [skillrepo.dev](https://skillrepo.dev/skills/affaan-m/security-scan) | MIT | 2026-06-14 |
| [site-architecture](skills/design/site-architecture/) | design | Corey Haines | [skillrepo.dev](https://skillrepo.dev/skills/coreyhaines31/site-architecture) | MIT | 2026-06-14 |
| [powershell-enterprise-app](skills/engineering/powershell-enterprise-app/) | engineering | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-14 |
| [modern-web-ui](skills/design/modern-web-ui/) | design | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-14 |
| [ui-styling](skills/design/ui-styling/) | design | claudekit (adapted) | [github.com/nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | MIT | 2026-06-14 |
| [design-tokens](skills/design/design-tokens/) | design | claudekit (adapted) | [github.com/nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | MIT | 2026-06-14 |
| [codex-consult](skills/engineering/codex-consult/) | engineering | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-14 |
| [opencode-consult](skills/engineering/opencode-consult/) | engineering | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-24 |
| [consult-orchestrator](skills/engineering/consult-orchestrator/) | engineering | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-24 |
| [mind-map-obsidian](skills/productivity/mind-map-obsidian/) | productivity | Sharquille Andrew (self-authored) | this repo | MIT | 2026-06-14 |
