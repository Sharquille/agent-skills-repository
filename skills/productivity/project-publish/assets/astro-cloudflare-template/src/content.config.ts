import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";

const assetRef = z.object({
  src: z.string(), // e.g. /projects/<neutral-slug>/topology.svg
  alt: z.string(),
  caption: z.string().optional(),
});

// A project write-up. `tier` exists only as a build-time gate; it is NEVER
// rendered, listed, or used for routing. Only approved + non-revoked, public
// projects are ever published.
const projects = defineCollection({
  loader: glob({ pattern: "**/*.mdx", base: "./src/content/projects" }),
  schema: z.object({
    title: z.string(),
    summary: z.string(),
    date: z.coerce.date(),
    tags: z.array(z.string()).default([]),
    archetype: z.enum([
      "network-lab",
      "security-lab",
      "osint",
      "hardening",
      "infra-build",
    ]),
    tier: z.enum(["T0", "T1", "T2", "T3", "T4"]), // build gate only — never rendered
    topology: z.array(assetRef).default([]),
    detection: z.object({
      summary: z.string(),
      logSources: z.array(z.string()).default([]),
      ruleRefs: z.array(assetRef).default([]),
    }),
    mitigation: z.object({
      summary: z.string(),
      controls: z.array(z.string()).default([]),
    }),
    ogImage: assetRef,
    approved: z.literal(true),
    revoked: z.literal(false).default(false),
  }),
});

export const collections = { projects };
