#!/usr/bin/env node
/**
 * import-approved-manifest.ts — build the PUBLIC portfolio index from an explicit
 * list of approved publish manifests handed over by the conductor. It is the
 * only path by which a project name reaches the public index.
 *
 * Hard rules (fail closed): a project is included ONLY if its manifest has
 * audience === "public", status === "approved", revoked === false, and the
 * publish policy allows it. Nothing else — no tiers, no local paths, no
 * unpublished/embargoed/rejected slugs — is emitted.
 *
 * Usage: node tools/import-approved-manifest.ts <manifest.json> [<manifest.json> ...]
 * Writes: src/data/approved-projects.json
 */
import { readFileSync, writeFileSync } from "node:fs";

interface Manifest {
  slug: string;
  title: string;
  summary: string;
  date: string;
  tags?: string[];
  archetype?: string;
  ogImage?: { src: string; alt: string };
  audience?: string;
  status?: string;
  revoked?: boolean;
  publish_policy?: string;
}

const PUBLISHABLE = new Set(["defensive-only", "full"]);

const out: Array<Record<string, unknown>> = [];
for (const path of process.argv.slice(2)) {
  let m: Manifest;
  try {
    m = JSON.parse(readFileSync(path, "utf8"));
  } catch {
    console.error(`skip (unparseable): ${path}`);
    continue;
  }
  const ok =
    m.audience === "public" &&
    m.status === "approved" &&
    m.revoked === false &&
    PUBLISHABLE.has(m.publish_policy ?? "");
  if (!ok) {
    console.error(`skip (not approved/public): ${m.slug ?? path}`);
    continue;
  }
  // Emit only the safe, public-facing subset.
  out.push({
    slug: m.slug,
    title: m.title,
    summary: m.summary,
    date: m.date,
    tags: m.tags ?? [],
    ogImage: m.ogImage ?? null,
  });
}

writeFileSync("src/data/approved-projects.json", JSON.stringify(out, null, 2) + "\n");
console.error(`wrote ${out.length} approved project(s) to src/data/approved-projects.json`);
