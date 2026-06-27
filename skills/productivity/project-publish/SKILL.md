---
name: project-publish
description: "Turn a project-build-loop project's sanitized publish manifest into an elegant Astro + Tailwind + MDX page bundle for a Cloudflare Pages static site. Use at project completion to compile the public write-up: consume only the allowlisted publish/ artifacts (never raw build logs), build an attack->detect->harden narrative for dual-use work, embed topology SVGs (optionally pan/zoom), and prepare a deployable Astro content bundle. Enforces the publication gate (secret scan, redaction review, tier publish-policy) before anything is written. Do not trigger to publish unsanitized artifacts or for non-static-site output."
# --- provenance ---
category: productivity
source: self-authored; part of the project orchestra (docs/plans/project-orchestra-plan.md)
author: Sharquille Andrew
license: MIT
retrieved: 2026-06-27
---

# Project Publish

Compiles a completed project's **sanitized** artifacts into an Astro + Tailwind +
MDX page bundle for Cloudflare Pages. It is the public boundary of the orchestra:
it reads only `publish/` (allowlisted, sanitized) artifacts — **never** raw
`build-log/` content.

## Pre-publish gate (mandatory, fail-closed)

Before writing any page, confirm with the conductor's policy:

1. `project-build-loop/scripts/policy_check.sh --action publish` allows it for
   the project's tier and `publish_policy`. T3 default no-publish; T4 never.
2. `project-build-loop/scripts/secret_scan.sh --publish publish/` is clean (real
   IPs → RFC 5737/3849 doc ranges; no creds/keys/PII/EXIF).
3. An allowlist **publish manifest** lists exactly which artifacts ship.

A dual-use disclaimer is boilerplate added **after** these pass — not a control.

## Content model (MDX components)

For a "gravitational," professional (not childish) technical write-up:

- `TopoViewer` — embed the `eve-ng-topology` SVG; optional Cytoscape.js/D3
  pan/zoom.
- `CommandBlock` — copy-safe command snippets (sanitized).
- `IOCCallout` / `EvidenceFigure` — detection artifacts and sanitized figures.
- Per-project Open Graph image; optimized SVG; alt text + captions +
  keyboard-navigable diagrams (accessibility).

## Dual-use narrative (required for T2+)

Structure as **attack → detect → harden**:

1. Context: authorization + isolation statement.
2. Approach: methodology, not weaponized tooling.
3. **Detection**: IOCs, Sigma/Suricata rules, log sources, alert logic.
4. **Mitigation**: segmentation, TLS/MACsec, 802.1X, cert pinning, hardening.

## Shipped scaffold

`assets/astro-cloudflare-template/` is a ready Astro + Tailwind 4 + MDX project:

- `astro.config.mjs` (static output), `wrangler.toml`, `package.json`.
- `src/content.config.ts` — the project write-up schema (`tier` is a build gate,
  never rendered or routed from).
- `src/components/mdx/` — `TopoViewer`, `CommandBlock`, `IOCCallout`,
  `EvidenceFigure`, `AttackDetectHarden`.
- `src/pages/index.astro` renders from `src/data/approved-projects.json` only —
  **never** filesystem discovery.
- `tools/import-approved-manifest.ts` — the only path a project reaches the public
  index; fail-closed (requires `audience: public`, `status: approved`,
  `revoked: false`, publishable policy).
- `src/content/projects/_example-osint-chain.mdx` — worked example.

Copy the template once, then per project: drop the sanitized topology SVG into
`public/projects/<slug>/`, write the MDX from the publish manifest, run the
importer, and `npm run build` (deploys `dist/` to Cloudflare Pages).

## Build & deploy

Reuse `site-architecture`, `modern-web-ui`, `design-tokens`, `ui-styling` for the
theme; `portable-markdown` + `humanizer` for the prose pass. Astro static output
deploys to Cloudflare Pages. The public **portfolio index** reads only approved
publish manifests and never lists unpublished T3/T4 project names.

## Safety

- Never read or ship `build-log/`, `evidence/`, or `.vault/` content.
- Support **revocation/embargo**: a published post can be pulled if risk changes.
- Respect the audience class (`internal-only` / `client-confidential` /
  `community-shared` / `public`).
