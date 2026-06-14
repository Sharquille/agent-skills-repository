---
name: network-interface-health
description: "Use this skill when a network symptom might be caused by a physical link, switch port, cable, transceiver, duplex setting, or congested interface."
category: engineering
source: https://skillrepo.dev/skills/affaan-m/network-interface-health
author: Affaan Mustafa
license: MIT
retrieved: 2026-06-14
---

# Network Interface Health

Use this skill when a network symptom might be caused by a physical link, switch port, cable, transceiver, duplex setting, or congested interface.

## When to Use

- A host or VLAN has packet loss, latency spikes, or intermittent reachability.
- A switch or router interface shows CRCs, runts, giants, drops, resets, or flapping events.
- Comparing both ends of a physical link before authorizing hardware replacement.
- Collecting before/after interface counter evidence states for a change window.
- Monitoring services report rising `ifInErrors`, `ifOutErrors`, or `ifOutDiscards` SNMP metrics.

## When NOT to Use

- Setting up or troubleshooting cloud-native network borders (e.g., AWS Security Groups, VPC routes).
- Drafting general application-level performance metrics, software database queries, or server scripts.
- General codebase refactoring, code formatting, or software quality analyses.

---

## How It Works

Interface counters are historical evidence, but the **trend matters more than the absolute number**. Always capture an initial baseline, wait a standardized measurement interval (e.g., 60 seconds), capture again, and calculate the increments.

### Discovery Commands

On Cisco switches/routers:
```text
show interfaces <interface>
show interfaces <interface> status
show logging | include <interface>|changed state|line protocol
```

On Linux hosts:
```text
ip -s link show <interface>
ethtool <interface>
ethtool -S <interface>
```

---

## Interface Counter Reference

| Counter | Meaning | Common Cause |
|---|---|---|
| **CRC** | Received frame checksum failed | Faulty patch cable, dirty fiber, bad transceiver (optic), or duplex mismatch |
| **input errors** | Aggregate receive-side errors | Check sub-counters (CRC, runts, framing) before concluding |
| **runts** | Frames below minimum Ethernet size (64 bytes) | Duplex mismatch, collision domain boundaries, or faulty network card (NIC) |
| **giants** | Frames larger than maximum MTU limits | MTU configuration mismatch across a jumbo-frame boundary |
| **input drops** | Device buffer full; cannot accept inbound packets | Burst traffic, oversubscription, CPU queue path bottleneck, or queue pressure |
| **output drops** | Egress hardware queue full; packets discarded | Congestion, active QoS policy drops, or undersized link capacity |
| **resets** | Interface controller hardware resets | Flapping links, keepalive losses, driver errors, failing optics, or power issues |
| **collisions** | Shared Ethernet collision events | Half-duplex operations or speed/duplex autonegotiation mismatches |

---

## Diagnostic Flow

### 1. CRCs or Input Errors
- **Is it Incrementing?** Confirm counters are currently rising, not just historical accumulation.
- **Both Sides**: Check interface stats on both ends of the link. Receive-side errors pointing to incoming signals usually mean the physical issue lies with the sending port, optic, or intermediate cable.
- **Physical Clean**: Reseat/replace patch cables, clean fiber tips, or swap transceivers (optics).
- **Match Settings**: Confirm speed and duplex settings are identical on both ends.
- **Log Review**: Search local logs for line-protocol or interface flap events around matching timestamps.

### 2. Drops
- **Drops Direction**: Separate input drops (buffer pressure) from output drops (link congestion).
- **Rate Check**: Compare interface rate against configured bandwidth/capacity.
- **Oversubscription**: Check QoS configurations and examine if the link serves as an oversubscribed uplink port.
- **Congestion Proof**: Treat queue tuning as secondary. First prove if the link is actively congested.

### 3. Duplex and Speed
- **Autonegotiation**: Strongly prefer speed and duplex auto-negotiation on all modern Ethernet links when both sides support it.
- **Explicit configuration**: If one side must be fixed, configure both sides explicitly to matching values. **Never mix fixed speed/duplex on one end with auto-negotiation on the other.**

---

## Safe Parser Example (Python)

Slice each interface block from one header to the next. Do not use an arbitrary character window; large interface blocks can cause counters to be missed or assigned to the wrong port.

```python
import re
from typing import Any

HEADER_RE = re.compile(
    r"^(?P<name>\S+) is (?P<status>(?:administratively )?down|up), "
    r"line protocol is (?P<protocol>up|down)",
    re.I | re.M,
)
ERROR_RE = re.compile(r"(?P<input>\d+) input errors, (?P<crc>\d+) CRC", re.I)
DROP_RE = re.compile(r"(?P<output>\d+) output errors", re.I)
DUPLEX_RE = re.compile(r"(?P<duplex>Full|Half|Auto)-duplex,\s+(?P<speed>[^,]+)", re.I)

def parse_show_interfaces(raw: str) -> list[dict[str, Any]]:
    headers = list(HEADER_RE.finditer(raw))
    interfaces = []
    for index, header in enumerate(headers):
        end = headers[index + 1].start() if index + 1 < len(headers) else len(raw)
        block = raw[header.start():end]
        errors = ERROR_RE.search(block)
        drops = DROP_RE.search(block)
        duplex = DUPLEX_RE.search(block)
        interfaces.append({
            "name": header.group("name"),
            "status": header.group("status"),
            "protocol": header.group("protocol"),
            "duplex": duplex.group("duplex") if duplex else "unknown",
            "speed": duplex.group("speed").strip() if duplex else "unknown",
            "input_errors": int(errors.group("input")) if errors else 0,
            "crc_errors": int(errors.group("crc")) if errors else 0,
            "output_errors": int(drops.group("output")) if drops else 0,
        })
    return interfaces
```

---

## Anti-Patterns to Avoid

- **Premature Clears**: Clearing device counters before saving an initial baseline report.
- **One-Sided Triage**: Reviewing counters on only one end of a physical link assignable to two ports.
- **Historical Bias**: Treating historic CRC error counts as active physical link problems without capturing a delta.
- **Mismatching Autoneg**: Leaving one end on auto-negotiation while pinning speed/duplex on the opposite port.
- **Physical Assumptions**: Attributing egress output drops to bad cables before checking for congested links.

## See Also

- Skill: [[cisco-ios-patterns]]
- Skill: [[configuring-network-segmentation-with-vlans]]
