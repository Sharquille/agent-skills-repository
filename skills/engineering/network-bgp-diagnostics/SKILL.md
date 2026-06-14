---
name: network-bgp-diagnostics
description: "Use this skill when a BGP session is down, flapping, established with missing routes, or advertising unexpected prefixes."
category: engineering
source: https://skillrepo.dev/skills/affaan-m/network-bgp-diagnostics
author: Affaan Mustafa
license: MIT
retrieved: 2026-06-14
---

# Network BGP Diagnostics

Use this skill when a BGP session is down, flapping, established with missing routes, or advertising unexpected prefixes. The default workflow is read-only evidence collection; policy and reset actions belong in a reviewed change window.

## When to Use

- BGP neighbors are stuck in Idle, Connect, Active, OpenSent, or OpenConfirm states.
- A session is Established but expected prefixes are missing from the routing table.
- A route-map, prefix-list, max-prefix limit, or AS path policy may be filtering routes.
- Collecting before/after evidence configuration states for BGP modifications.
- Reviewing automation or parser scripts that interpret BGP summary outputs.

## When NOT to Use

- General application-level TCP/UDP socket programming.
- General local web design, user interface layout styling, or front-end JS operations.
- Non-networking software codebase refactoring or code quality analysis.

---

## Read-Only Triage Flow

1. **Identify Peer Details**: Determine the exact neighbor IP, address family (IPv4/IPv6), VRF, and local/remote ASNs.
2. **Summary State**: Capture summary state and the last reset reason.
3. **Reachability**: Prove routing reachability to the peer source address.
4. **Policy Mapping**: Check route policy references before assuming transport failure.
5. **Route Compare**: Compare advertised, received, and installed routes where the platform supports those commands.

### Discovery Commands

```text
show bgp summary
show bgp neighbors <peer>
show ip route <peer>
show tcp brief | include <peer>|:179
show logging | include BGP|<peer>
show running-config | section router bgp
show ip prefix-list
show route-map
```

*Use platform-specific address-family commands when the device uses VRFs, IPv6, VPNv4, or EVPN. Do not assume global IPv4 unicast.*

---

## BGP State Interpretation

| State | First Checks |
|---|---|
| **Established (with prefixes)** | Route exchange is up; inspect policy and routing table selection. |
| **Established (zero prefixes)** | Check inbound policy, max-prefix limit, advertised routes, and matching AFI/SAFI configurations. |
| **Active** | TCP session is not completing; check routing, source interface, ACLs, and peer reachability. |
| **Connect** | TCP connection is in progress; check routing path and remote listener status. |
| **OpenSent / OpenConfirm** | TCP works; check ASN mismatch, MD5 authentication keys, timers, capabilities, and device logs. |
| **Idle** | Neighbor may be disabled (shutdown), missing config, blocked by policy, or in a backoff timer loop. |

---

## Transport & Reachability Checks

Verify paths and TCP listener status:

```text
ping <peer> source <local-source>
traceroute <peer> source <local-source>
show ip route <peer>
show bgp neighbors <peer> | include BGP state|Last reset|Local host|Foreign host
```

*If the peer is sourced from a loopback, confirm both directions route to the loopback addresses and that the neighbor config uses the expected update source.*

> ⚠️ **Injunction:** Avoid disabling ACLs or firewall policies as a diagnostic shortcut. Read hit counters, logs, and path state first.

---

## Route Policy Checks

Analyze if route-maps or prefix-lists are dropping packets:

```text
show bgp neighbors <peer> advertised-routes
show bgp neighbors <peer> routes
show ip prefix-list <name>
show route-map <name>
show bgp <prefix>
```

*Note: Some platforms require additional configuration (such as soft-reconfiguration inbound) before received-routes is available. Do not add that configuration during active incident triage unless the operator explicitly approves.*

---

## AS Path & Prefix Review

```text
show bgp regexp _65001_
show bgp regexp ^65001$
show bgp <prefix>
show bgp neighbors <peer> advertised-routes | include Network|Path|<prefix>
```

*Use AS-path regex carefully. `_65001_` matches AS 65001 as a token. Plain `65001` can match longer ASNs or unrelated text.*

---

## Parser Pattern (Python)

```python
import re
from typing import Any

BGP_SUMMARY_RE = re.compile(
    r"^(?P<neighbor>\d{1,3}(?:\.\d{1,3}){3})\s+"
    r"(?P<version>\d+)\s+"
    r"(?P<remote_as>\d+)\s+"
    r"(?P<msg_rcvd>\d+)\s+"
    r"(?P<msg_sent>\d+)\s+"
    r"(?P<table_version>\d+)\s+"
    r"(?P<input_queue>\d+)\s+"
    r"(?P<output_queue>\d+)\s+"
    r"(?P<uptime>\S+)\s+"
    r"(?P<state_or_prefixes>\S+)$",
    re.M,
)

def parse_bgp_summary(raw: str) -> list[dict[str, Any]]:
    rows = []
    for match in BGP_SUMMARY_RE.finditer(raw):
        state_or_prefixes = match.group("state_or_prefixes")
        if state_or_prefixes.isdigit():
            state = "Established"
            prefixes_received = int(state_or_prefixes)
        else:
            state = state_or_prefixes
            prefixes_received = None
        rows.append({
            "neighbor": match.group("neighbor"),
            "remote_as": int(match.group("remote_as")),
            "state": state,
            "prefixes_received": prefixes_received,
            "uptime": match.group("uptime"),
        })
    return rows
```

*Prefer structured parser output when available, but always store the raw CLI output with the incident record because BGP summary formats vary widely by platform.*

---

## Change-Window Restrictions

These actions can disrupt production routing and must **never** be suggested as automatic diagnostics:
- Clearing BGP sessions (`clear ip bgp *`).
- Changing neighbor authentication keys, timers, update sources, route-maps, or prefix-lists.
- Enabling additional received-route storage configurations.
- Relaxing firewall, ACL, or control-plane protection policies.

*If a reset is approved, prefer the least disruptive option (soft-reset or route-refresh) supported by the platform, and document exactly why it is safe.*

---

## Anti-Patterns to Avoid

- **Assuming Active is Down**: Active state means TCP connection attempts are failing. Check routing, firewalls, and source configuration.
- **Ignoring Scope**: Forgetting address family (AFI/SAFI), VRF, or loopback update-source differences.
- **Over-broad Regex**: Utilizing raw ASN regex filters without proper token word boundaries.
- **Hard Resets first**: Issuing hard BGP clears before analyzing log buffers and reset counters.
- **Empty Output Assumptions**: Treating empty received-routes tables as proof that no advertisements were sent by the peer.

## See Also

- Skill: [[configuring-pfsense-firewall-rules]]
- Skill: [[cisco-ios-patterns]]
