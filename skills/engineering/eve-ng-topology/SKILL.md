---
name: eve-ng-topology
description: "Turn an EVE-NG lab into clean, version-controlled, presentation-grade topology diagrams. Use when the user has an EVE-NG .unl lab file (or HTML/PNG export) and wants a diffable topology: parse the .unl XML as the source of truth into structured topology.json, then generate Mermaid (logical/versionable) and Graphviz DOT->SVG (precise, vendor icons) for docs or a static site. Do not trigger for live device polling (use network-config-validation) or for non-EVE-NG diagrams. The .unl schema differs between Community and Pro, so validate the parser against a real export before relying on it."
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

## Validate before trusting

The `.unl` schema differs between EVE-NG **Community** and **Pro** (and across
versions). Run the parser against a **real export** first and diff the node/link
count against what you see in the EVE-NG UI. The parser is defensive: it reports
what it could not map rather than guessing.

## Redaction

When the topology feeds a public write-up, replace real management IPs/hostnames
with documentation ranges and strip lab-identifying names. Sanitization is the
caller's (conductor's) responsibility before publish.
