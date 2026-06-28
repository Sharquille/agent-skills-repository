---
name: eve-ng-topology
description: "Turn an EVE-NG lab into clean, version-controlled, presentation-grade topology diagrams. Use when the user has an EVE-NG .unl lab file (or HTML/PNG export) and wants a diffable topology: parse the .unl XML as the source of truth into structured topology.json, then generate Mermaid (logical/versionable) and Graphviz DOT->SVG (precise, vendor icons) for docs or a static site. Also runs in reverse to scaffold an importable EVE-NG Pro .unl from a topology spec + node catalog (scripts/generate_unl.py) so a lab is easier to stand up without manual node-dragging — structure only: it embeds device configs verbatim and never performs technical config changes for the user. Do not trigger for live device polling (use network-config-validation) or for non-EVE-NG diagrams. The .unl schema differs between Community and Pro, so validate the parser against a real export before relying on it."
# --- provenance ---
category: engineering
source: self-authored; part of the project orchestra (docs/plans/project-orchestra-plan.md)
author: Sharquille Andrew
license: MIT
retrieved: 2026-06-27
---

# EVE-NG Topology

EVE-NG's HTML/PNG exports are not diffable, editable, or automatable. The **`.unl`
file is XML** — treat it as the single source of truth and generate everything
else from it.

## Pipeline

1. **Parse** `lab.unl` → `topology.json` (nodes, interfaces, networks,
   coordinates) with `scripts/unl_to_topology.py`.
2. **Annotate** the JSON with roles, addresses (use RFC 5737 / RFC 3849
   documentation ranges in anything published), and icons.
3. **Generate**:
   - **Mermaid** (`graph LR`) for logical, version-controlled docs.
   - **Graphviz DOT → SVG** for precise diagrams with vendor icons.
   - Keep the EVE-NG PNG only as a thumbnail, never the canonical diagram.
4. **Embed** the SVG in the site; optionally wrap in Cytoscape.js/D3 for pan/zoom
   (handled by `project-publish`).

## Usage

```text
# .unl -> topology.json
scripts/unl_to_topology.py lab.unl > topology.json
# topology.json -> diagrams
scripts/unl_to_topology.py lab.unl --emit mermaid > topology.mmd
scripts/unl_to_topology.py lab.unl --emit dot | dot -Tsvg > topology.svg
```

## Enrichments

Validated against a real EVE-NG **Pro** export, the parser captures:

- **Link labels** — interface `label` values (e.g. `WireGuard Tunnel UDP :51820`)
  ride the edge in Mermaid/DOT.
- **Roles** — node `icon`/`type`/`template` map to `router`/`server`/`docker`/
  `kali`/`linux`/`cloud` for styling.
- **Isolated nodes** — a node present in the `.unl` but with **no `<interface>`**
  is rendered dashed and annotated "unwired in .unl". Never fabricate an edge for
  a conceptual path; inferred wiring belongs in prose, not the generated diagram.
- **Zones** — `<textobject>` base64 HTML is decoded into a `zones` list (e.g.
  "Research Zone — VLAN 70").

Device `<config>` blocks are **never** auto-included — they carry certs and real
IPs. The publication layer redacts (cert → placeholder, real IPs → RFC 5737/3849
ranges) and may include only a sanitized excerpt.

## Validate before trusting

The `.unl` schema differs between EVE-NG **Community** and **Pro** (and across
versions). Run the parser against a **real export** first and diff the node/link
count against what you see in the EVE-NG UI. The parser is defensive: it reports
what it could not map rather than guessing.

## Generate (forward): scaffold, don't configure

The reverse of the pipeline. `scripts/generate_unl.py` builds an importable
EVE-NG **Pro** `.unl` from a topology spec so a lab is easier to stand up without
manual node-dragging.

**Principle — scaffold, don't configure.** The generator owns the tedious
*structure*: nodes, images, interface wiring, networks, canvas layout. It does
**not** own device configuration. A node's `config_file` is embedded **verbatim**;
the tool never edits, "fixes", or invents config. Technical config changes are the
user's hands-on lab work — leave the baseline faithful to observed state and
surface improvements as `! TODO`/advisories, never silently apply them.

**Node catalog (image strings are server-specific).** `template` is
platform-fixed; the `image` must exist on the target server or import fails. Keep
a per-project catalog in three tiers:

- Tier 1 — confirmed installed (from a real export of that server).
- Tier 2 — EVE-NG default QEMU templates (vios / viosl2 / iol / nxosv / veos / vmx…).
- Tier 3 — EVE-NG Pro default Docker containers (eve-gui-server, …).

Pass `--catalog catalog.json`; the generator warns (fail-soft) on any image not
in the catalog. Never guess an image string.

```text
scripts/generate_unl.py --example > spec.json      # sample spec to adapt
scripts/generate_unl.py spec.json > lab.unl         # spec -> importable .unl
scripts/generate_unl.py spec.json --catalog catalog.json > lab.unl
```

**Not proven until imported.** The `.unl` schema differs across Pro/Community and
versions. A generated `.unl` is unverified until it import-validates on the target
EVE-NG server; only then round-trip it back through `unl_to_topology.py` for docs.

### Presentable, context-driven layout (`design_unl.py`)

`generate_unl.py` wires nodes; `scripts/design_unl.py` makes them **presentable**
from project context instead of a fixed template. You describe the lab by **trust
tiers** (what lives in each zone, with a title, color, subnet, and the nodes); the
tool **computes** the layout — never hand-placed coordinates:

- Tiers become evenly spaced **columns**; nodes stack inside them.
- Each tier gets one **non-overlapping** zone rectangle of **equal height**
  (tops/bottoms align), with a title + subnet header.
- Every node gets an **IP/label** under its icon; interface `label`s ride links.
- Change the tiers/nodes → layout, zones, and labels recompute. IP strings are
  display labels only (generic placeholders are fine); `config` is still embedded
  verbatim (scaffold, don't configure).

```text
design_unl.py --example > design.json      # sample tiered design to adapt
design_unl.py design.json > lab.unl         # context -> elegant, aligned .unl
design_unl.py design.json --catalog catalog.json > lab.unl
```

Aim for **concise, legible** designs: a handful of clearly named tiers, one
subnet per zone, short node labels. The geometry is guaranteed clean (aligned,
non-overlapping); aesthetics like color and wording are yours to tune in the
design spec, then re-run.

**Two outputs, one spec.** For a polished, shareable picture, emit an
Excalidraw diagram from the same design — don't fight EVE-NG's fragile textobject
renderer for a hand-drawn look:

```text
design_unl.py design.json --format excalidraw > lab.excalidraw
```

It opens at excalidraw.com and embeds in docs/READMEs; output is deterministic
per lab name. Keep the `.unl` as the lab source of truth (IPs, wiring) and the
`.excalidraw` as the presentation artifact — they're generated from the same
context, so they never drift.

**Visual polish (automatic).** Both outputs are styled for legibility:

- **Distance-based links** — short hops render `Straight`; longer ones flow as
  `Bezier` with curvature scaled by endpoint distance (computed from the layout).
  In Excalidraw the same rule bows the connectors.
- **Zones** get a subtle vertical gradient; **subnet/IP labels** use a monospace
  font so addresses are scannable; the Excalidraw diagram adds a **title** and a
  **color legend**.
- **Labels are placeholders by design** — `node.ip`, `tier.subnet`, and
  `iface.label` are free strings. Use real lab values *or* generic placeholders
  (`<KALI_IP>`, `<VPN_ENDPOINT>`); the layout doesn't care and nothing is
  invented. Keep them short so they sit cleanly under the node / in the header.

## Redaction

When the topology feeds a public write-up, replace real management IPs/hostnames
with documentation ranges and strip lab-identifying names. Sanitization is the
caller's (conductor's) responsibility before publish.
