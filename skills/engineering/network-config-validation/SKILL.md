---
name: network-config-validation
description: "Use this skill to review network configuration before a change window or before an automation run touches production devices."
category: engineering
source: https://skillrepo.dev/skills/affaan-m/network-config-validation
author: Affaan Mustafa
license: MIT
retrieved: 2026-06-14
---

# Network Config Validation

Use this skill to review network configuration before a change window or before an automation run touches production devices.

## When to Use

- Reviewing Cisco IOS or IOS-XE style configuration snippets before deployment.
- Auditing generated configuration files from scripts, playbooks, or templates.
- Scanning for dangerous commands, duplicate IP assignments, or subnet overlaps.
- Verifying whether ACLs, route-maps, prefix-lists, or VTY line policies are referenced but not defined.
- Integrating pre-flight validation gates inside network automation pipelines.

## When NOT to Use

- Reviewing application-level software input schemas, web validation parameters, or SQL database structures.
- Auditing web server/API configuration states, SSL/TLS certificates, or cloud access roles.
- Drafting general software engineering policy documents or unit-testing codebases.

---

## How It Works

Treat config validation as layered evidence, not as a complete parser. Regex checks are useful for pre-flight warnings, but final approval still needs a network engineer to review intent, platform syntax, and rollback steps.

Validate in this order:
1. Destructive commands.
2. Credential and management-plane exposure.
3. Duplicate addresses and overlapping subnets.
4. Stale references to ACLs, route-maps, prefix-lists, and interfaces.
5. Operational hygiene such as NTP, timestamps, remote logging, and banners.

---

## Dangerous Command Detection (Python)

```python
import re

DANGEROUS_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\breload\b", re.I), "reload causes downtime"),
    (re.compile(r"\berase\s+(startup|nvram|flash)", re.I), "erases persistent storage"),
    (re.compile(r"\bformat\b", re.I), "formats a device filesystem"),
    (re.compile(r"\bno\s+router\s+(bgp|ospf|eigrp)\b", re.I), "removes a routing process"),
    (re.compile(r"\bno\s+interface\s+\S+", re.I), "removes interface configuration"),
    (re.compile(r"\baaa\s+new-model\b", re.I), "changes authentication behavior"),
    (re.compile(r"\bcrypto\s+key\s+(zeroize|generate)\b", re.I), "changes device SSH keys"),
]

def find_dangerous_commands(lines: list[str]) -> list[dict[str, str | int]]:
    findings = []
    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()
        for pattern, reason in DANGEROUS_PATTERNS:
            if pattern.search(stripped):
                findings.append({
                    "line": line_number,
                    "command": stripped,
                    "reason": reason,
                })
    return findings
```

---

## Duplicate IPs & Subnet Overlaps (Python)

```python
import ipaddress
import re
from collections import Counter

IP_ADDRESS_RE = re.compile(
    r"^\s*ip address\s+"
    r"(?P<ip>\d{1,3}(?:\.\d{1,3}){3})\s+"
    r"(?P<mask>\d{1,3}(?:\.\d{1,3}){3})\b",
    re.I | re.M,
)

def extract_interfaces(config: str) -> list[dict[str, str]]:
    results = []
    current = None
    for line in config.splitlines():
        if line.startswith("interface "):
            current = line.split(maxsplit=1)[1]
            continue
        match = IP_ADDRESS_RE.match(line)
        if current and match:
            ip = match.group("ip")
            mask = match.group("mask")
            network = ipaddress.ip_interface(f"{ip}/{mask}").network
            results.append({"interface": current, "ip": ip, "network": str(network)})
    return results

def find_duplicate_ips(config: str) -> list[str]:
    ips = [entry["ip"] for entry in extract_interfaces(config)]
    counts = Counter(ips)
    return sorted(ip for ip, count in counts.items() if count > 1)

def find_subnet_overlaps(config: str) -> list[tuple[str, str]]:
    networks = [ipaddress.ip_network(entry["network"]) for entry in extract_interfaces(config)]
    overlaps = []
    for index, left in enumerate(networks):
        for right in networks[index + 1:]:
            if left.overlaps(right):
                overlaps.append((str(left), str(right)))
    return overlaps
```

---

## Management-Plane Checks (Python)

Parse VTY blocks by section so access-class checks do not spill across unrelated lines.

```python
import re

def iter_blocks(config: str, starts_with: str) -> list[str]:
    blocks = []
    current: list[str] = []
    for line in config.splitlines():
        if line.startswith(starts_with):
            if current:
                blocks.append("\n".join(current))
            current = [line]
            continue
        if current:
            if line and not line.startswith(" "):
                blocks.append("\n".join(current))
                current = []
            else:
                current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks

def check_vty_blocks(config: str) -> list[str]:
    issues = []
    for block in iter_blocks(config, "line vty"):
        if re.search(r"transport\s+input\s+.*telnet", block, re.I):
            issues.append("VTY allows Telnet; require SSH only.")
        if not re.search(r"\baccess-class\s+\S+\s+in\b", block, re.I):
            issues.append("VTY block has no inbound access-class source restriction.")
        if not re.search(r"\bexec-timeout\s+\d+\s+\d+\b", block, re.I):
            issues.append("VTY block has no explicit exec-timeout.")
    return issues
```

---

## Security Hygiene Checks (Python)

```python
import re

SECURITY_PATTERNS = [
    (re.compile(r"\bsnmp-server community\s+(public|private)\b", re.I),
     "default SNMP community configured"),
    (re.compile(r"\bsnmp-server community\s+\S+", re.I),
     "SNMPv2 community string configured; prefer SNMPv3 authPriv"),
    (re.compile(r"\bip ssh version 1\b", re.I),
     "SSH version 1 enabled"),
    (re.compile(r"\benable password\b", re.I),
     "enable password is present; use enable secret"),
    (re.compile(r"\busername\s+\S+\s+password\b", re.I),
     "local username uses password instead of secret"),
]

BEST_PRACTICE_PATTERNS = [
    (re.compile(r"\bntp server\b", re.I), "NTP server"),
    (re.compile(r"\bservice timestamps\b", re.I), "log timestamps"),
    (re.compile(r"\blogging\s+\S+", re.I), "logging destination or buffer"),
    (re.compile(r"\bsnmp-server group\s+\S+\s+v3\s+priv\b", re.I), "SNMPv3 authPriv group"),
    (re.compile(r"\bbanner\s+(login|motd)\b", re.I), "login banner"),
]

def check_security(config: str) -> list[str]:
    return [message for pattern, message in SECURITY_PATTERNS if pattern.search(config)]

def check_missing_hygiene(config: str) -> list[str]:
    return [
        f"Missing {description}"
        for pattern, description in BEST_PRACTICE_PATTERNS
        if not pattern.search(config)
    ]
```

---

## Integration Scenarios

### Change-Window Preflight
- Run dangerous-command checks on the exact configuration snippet to be pasted.
- Run duplicate IP and subnet overlap checks against the full candidate device configuration.
- Confirm every referenced ACL, route-map, and prefix-list actively exists in the running-config.
- Verify rollback commands, out-of-band console lines, and backup access routes are verified before changing management-plane bounds.

### Automation Preflight
- Integrate validation scripts as blocking check gates inside Netmiko, NAPALM, Ansible, or REST API scripts.
- Fail closed and abort transactions upon detecting unauthorized dangerous commands or exposed credentials.
- Generate warning reports for missing operational hygiene markers without disrupting active change scopes.

---

## Anti-Patterns to Avoid

- **Inert Over-Reliance:** Treating pattern matches as complete syntactic parser states. Always dry-run configurations.
- **Skipping Diffs:** Applying templated configurations directly to devices without performing a dry-run diff against the running config.
- **Insecure Monitoring defaults:** Approving the configure of default SNMPv2 communities (`public`/`private`) for monitoring convenience.
- **Unstructured Checks:** Scanning VTY line settings using regex checks that do not respect section formatting blocks, leading to mixed line matches.

## See Also

- Skill: [[cisco-ios-patterns]]
- Skill: [[configuring-pfsense-firewall-rules]]
