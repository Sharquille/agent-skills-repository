---
name: homelab-vlan-segmentation
description: "Guides the isolation and configuration of homelab VLANs (IoT, guests, trusted, management) on pfSense, OPNsense, UniFi, and MikroTik."
category: engineering
source: https://skillrepo.dev/skills/affaan-m/homelab-vlan-segmentation
author: Affaan Mustafa
license: MIT
retrieved: 2026-06-14
---

# Homelab VLAN Segmentation

Split a home network into isolated VLANs so IoT devices, guests, and your main PCs cannot talk to each other. This is one of the most impactful security upgrades for a home network or small laboratory.

All firewall rules shown here add isolation between segments — they do not remove existing protections. Apply changes in a maintenance window and verify connectivity between segments after each step before moving on.

## When to Use

- Setting up VLANs on a home network for the first time.
- Isolating IoT devices (smart bulbs, cameras, TVs) from trusted systems.
- Creating a guest Wi-Fi network that cannot reach private home devices.
- Configuring trunk ports, access ports, and SSID-to-VLAN mappings.
- Troubleshooting inter-VLAN routing or firewall rule issues on pfSense, OPNsense, or UniFi.

## When NOT to Use

- Configuring cloud-native virtual networks (AWS VPC, GCP subnets, Azure VNet).
- Building corporate enterprise-scale WAN or multi-datacenter infrastructures.
- General software application socket programming or transport-layer protocol development.

## How It Works

Without VLANs — flat network:
- All devices on `192.168.1.0/24`
- Smart TV (potential malware) → can reach your NAS, PCs, and everything else on the LAN.

With VLANs:
- **VLAN 10 — Trusted** (`192.168.10.0/24`): PCs, phones, laptops
- **VLAN 20 — IoT** (`192.168.20.0/24`): Smart TV, bulbs, cameras
- **VLAN 30 — Servers** (`192.168.30.0/24`): NAS, Pi, VMs
- **VLAN 40 — Guest** (`192.168.40.0/24`): Visitor Wi-Fi (internet only)
- **VLAN 99 — Management** (`192.168.99.0/24`): Switch/AP web UIs

Result:
- **Smart TV** → blocked from reaching `192.168.10.0/24` and `192.168.30.0/24`.
- **Guests** → internet only, completely isolated from seeing local devices.

## VLAN Design Template

| VLAN ID | Name | Subnet | Gateway | Purpose |
|---|---|---|---|---|
| **10** | trusted | `192.168.10.0/24` | `192.168.10.1` | PCs, phones, laptops (trusted) |
| **20** | iot | `192.168.20.0/24` | `192.168.20.1` | Smart home / IoT devices |
| **30** | servers | `192.168.30.0/24` | `192.168.30.1` | NAS, Pi, self-hosted services |
| **40** | guest | `192.168.40.0/24` | `192.168.40.1` | Visitor Wi-Fi (isolated) |
| **99** | management | `192.168.99.0/24` | `192.168.99.1` | Network gear management (web UIs) |

---

## Configuration Examples

### A. UniFi Configuration

#### 1. Create Networks in UniFi Controller
Settings → Networks → Create New Network:
For each VLAN:
- **Name:** IoT
- **Purpose:** Corporate (gives DHCP + routing)
- **VLAN ID:** 20
- **Network:** `192.168.20.0/24`
- **Gateway IP:** `192.168.20.1`
- **DHCP:** Enable
- **DHCP Range:** `192.168.20.100` – `192.168.20.254`

#### 2. Map SSIDs to VLANs (UniFi)
Settings → WiFi → Create New WiFi:
- **Name:** `IoT-Network`
  - **Password:** `<separate password>`
  - **Network:** `IoT` (VLAN 20)
- **Name:** `Guest`
  - **Password:** `<guest password>`
  - **Network:** `Guest` (VLAN 40)
  - **Guest Policy:** Enable (isolates guests from each other too)

#### 3. Traffic Rules (UniFi Firewall)
Settings → Traffic & Security → Traffic Rules:
- **Block IoT from reaching Trusted VLAN**:
  - **Action:** Block
  - **Category:** Local Network
  - **Source:** IoT (`192.168.20.0/24`)
  - **Destination:** Trusted (`192.168.10.0/24`)
- **Allow IoT to reach internet only**:
  - **Action:** Allow
  - **Source:** IoT
  - **Destination:** Internet
- **Block Guest from all local networks**:
  - **Action:** Block
  - **Source:** Guest
  - **Destination:** Local Networks

---

### B. pfSense / OPNsense Configuration

#### 1. Create VLANs
Interfaces → Assignments → VLANs → Add:
- **Parent Interface:** `em1` (your LAN NIC)
- **VLAN Tag:** `20`
- **Description:** `IoT`

*(Assign each VLAN under `Interfaces → Assignments → Add`, enable the interface, and set the gateway IP address, e.g. `192.168.20.1/24`).*

#### 2. DHCP for Each VLAN
Services → DHCP Server → Select your VLAN interface:
- **Enable DHCP**
- **Range:** `192.168.20.100` to `192.168.20.254`
- **DNS Servers:** `192.168.30.2` (Pi-hole / local resolver IP)

#### 3. Firewall Rules
*Rules are processed top-to-bottom, first match wins.*

On the **IoT interface (VLAN 20)**:
- **Rule 1 (Allow IoT → Pi-hole DNS)**:
  - **Action:** Allow
  - **Protocol:** UDP/TCP
  - **Source:** IoT net
  - **Destination:** `192.168.30.2` port `53`
- **Rule 2 (Block IoT → RFC1918)**:
  - **Action:** Block
  - **Protocol:** any
  - **Source:** IoT net
  - **Destination:** RFC1918 (Alias containing `192.168.0.0/16`, `10.0.0.0/8`, `172.16.0.0/12`)
- **Rule 3 (Allow IoT → Internet)**:
  - **Action:** Allow
  - **Protocol:** any
  - **Source:** IoT net
  - **Destination:** any

On the **Trusted interface (VLAN 10)**:
- **Allow Trusted → any** (trusted devices can reach everything):
  - **Action:** Allow
  - **Source:** Trusted net
  - **Destination:** any

*Optional Home Assistant Exception (insert before Rule 2 Block):*
- **Action:** Allow
- **Protocol:** TCP
- **Source:** IoT net
- **Destination:** `192.168.30.x` port `8123`

---

### C. MikroTik Configuration

```routeros
# Step 1: Create a bridge with VLAN filtering enabled
/interface bridge
add name=bridge vlan-filtering=yes

# Step 2: Add physical ports to the bridge
# Trunk port to router/uplink (tagged for all VLANs)
/interface bridge port
add bridge=bridge interface=ether1 frame-types=admit-only-vlan-tagged

# Access port for trusted devices (untagged VLAN 10)
/interface bridge port
add bridge=bridge interface=ether2 pvid=10 frame-types=admit-only-untagged-and-priority-tagged

# Access port for IoT devices (untagged VLAN 20)
/interface bridge port
add bridge=bridge interface=ether3 pvid=20 frame-types=admit-only-untagged-and-priority-tagged

# Step 3: Define which VLANs are allowed on which ports
/interface bridge vlan
add bridge=bridge tagged=ether1 untagged=ether2 vlan-ids=10
add bridge=bridge tagged=ether1 untagged=ether3 vlan-ids=20

# Step 4: Create VLAN interfaces on the bridge (gateway IPs)
/interface vlan
add interface=bridge name=vlan10 vlan-id=10
add interface=bridge name=vlan20 vlan-id=20

# Step 5: Assign gateway IPs
/ip address
add interface=vlan10 address=192.168.10.1/24
add interface=vlan20 address=192.168.20.1/24

# Step 6: DHCP pools and servers
/ip pool
add name=pool-trusted ranges=192.168.10.100-192.168.10.254
add name=pool-iot ranges=192.168.20.100-192.168.20.254

/ip dhcp-server
add interface=vlan10 address-pool=pool-trusted name=dhcp-trusted
add interface=vlan20 address-pool=pool-iot name=dhcp-iot

/ip dhcp-server network
add address=192.168.10.0/24 gateway=192.168.10.1
add address=192.168.20.0/24 gateway=192.168.20.1

# Step 7: Firewall — block IoT from reaching trusted VLAN
/ip firewall filter
add chain=forward src-address=192.168.20.0/24 dst-address=192.168.10.0/24 \
    action=drop comment="Block IoT to Trusted"
```

---

## Switch Trunk vs Access Ports

- **Trunk port:** Carries multiple VLANs (tagged). Connects switch-to-switch, switch-to-router, switch-to-AP.
- **Access port:** Carries one VLAN (untagged). Connects directly to end devices (PCs, cameras, NAS) that are not VLAN-aware.

---

## Anti-Patterns & Best Practices

### Anti-Patterns to Avoid
- **VLANs without Firewall Rules:** VLANs alone do not provide isolation; inter-VLAN routing is active by default on most routers. Always add firewall rules immediately.
- **Putting the Pi-hole in the IoT VLAN:** This prevents trusted devices from reaching it unless extra open-all rules are written. Put the Pi-hole in the Servers VLAN.
- **Native VLAN = Management VLAN:** Leaving untagged traffic on your management segment invites VLAN hopping attacks. Always use a dedicated, unused native VLAN ID (e.g. `999`).
- **Shared Wi-Fi Passwords:** Do not share the same password between SSIDs; this permits clients to easily authenticate onto incorrect networks.

### Recommended Best Practices
- Start with **4 core VLANs**: Trusted, IoT, Servers, and Guest.
- Put local resolvers (like Pi-hole or AdGuard) in the **Servers VLAN** and allow DNS (port 53) from other VLAN interfaces with explicit named rules.
- **Verify Isolation**: Attempt a ping from an IoT device to a trusted PC; it must be blocked.
- Restrict gateway and switch management interfaces strictly to the **Trusted VLAN**.

## See Also

- Skill: [[homelab-network-readiness]]
- Skill: [[configuring-network-segmentation-with-vlans]]
- Skill: [[configuring-pfsense-firewall-rules]]
